#!/usr/bin/env python3
"""
Fills in supporting b-roll for an edit: given a list of search slots (a
keyword + how long the insert should be), queries Pexels Video (primary) and
falls back to Pixabay Video (secondary, or if Pexels has no key/no result)
for a matching vertical clip, downloads the best match, and saves it into
the Remotion project's public/ folder so it can be referenced directly from
an EditPlan's `broll[].src`.

Both Pexels and Pixabay's free API tiers allow commercial use without
attribution (check current terms before large-scale reuse). Neither requires
payment info to sign up.

Usage:
    python3 fetch_broll.py --job my-campaign --slots slots.json

slots.json:
[
  {"query": "hands typing on laptop", "atMs": 4500, "durationMs": 1500},
  {"query": "city street at night", "atMs": 9000, "durationMs": 2000}
]

Writes downloaded clips to remotion/public/jobs/<job>/broll_NN.mp4 and prints
a `broll` array (EditPlan-ready, src paths already relative to public/) that
can be pasted straight into the job's EditPlan JSON.
"""

import argparse
import json
import os
import sys

import requests

import bcc_env  # keys live in ~/.bcc-toolkit/.env (they survive plugin updates); the skill's own .env is still honoured
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = bcc_env.ENV_PATH   # messages point at the persistent file
PUBLIC_DIR = os.path.join(SKILL_DIR, "remotion", "public")

PEXELS_SEARCH = "https://api.pexels.com/videos/search"
PIXABAY_SEARCH = "https://pixabay.com/api/videos/"


def load_env_file(path):
    values = {}
    if not os.path.isfile(path):
        return values
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_key(name):
    key = os.environ.get(name)
    if not key:
        key = load_env_file(ENV_FILE).get(name)
    if not key or key.startswith("pega-aqui"):
        return None
    return key


def _closest_to_1080(video_files, want_portrait=True):
    """Pexels returns several renditions per video. For a 1080x1920 vertical edit we need the long side to be
    >= 1900 px (a 960-px-tall file looks soft once scaled up): take the smallest rendition that reaches it,
    else the largest available. Prefers portrait files if the source has any."""
    candidates = video_files
    if want_portrait:
        portrait = [v for v in video_files if v.get("height", 0) > v.get("width", 0)]
        if portrait:
            candidates = portrait
    def side(v):
        return (v.get("height") or v.get("width") or 0)
    big = [v for v in candidates if side(v) >= 1900]
    return min(big, key=side) if big else max(candidates, key=side)


def search_pexels(query, key, orientation="portrait"):
    resp = requests.get(
        PEXELS_SEARCH,
        headers={"Authorization": key},
        params={"query": query, "orientation": orientation, "per_page": 5},
        timeout=30,
    )
    resp.raise_for_status()
    videos = resp.json().get("videos", [])
    if not videos:
        return None
    video = videos[0]
    file = _closest_to_1080(video["video_files"])
    return {"url": file["link"], "source": "pexels", "page_url": video.get("url")}


def search_pixabay(query, key, orientation="vertical"):
    resp = requests.get(
        PIXABAY_SEARCH,
        params={"key": key, "q": query, "video_type": "film", "orientation": orientation, "per_page": 5},
        timeout=30,
    )
    resp.raise_for_status()
    hits = resp.json().get("hits", [])
    if not hits:
        return None
    hit = hits[0]
    videos = hit["videos"]
    file = videos.get("large") or videos.get("medium") or videos.get("small")
    return {"url": file["url"], "source": "pixabay", "page_url": hit.get("pageURL")}


def download(url, dest_path):
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 16):
            f.write(chunk)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, help="Job slug, e.g. 'campana-lanzamiento' -- destination is remotion/public/jobs/<job>/")
    parser.add_argument("--slots", required=True, help="Path to slots JSON: [{query, atMs, durationMs}, ...]")
    parser.add_argument("--orientation", default="portrait", choices=["portrait", "landscape", "square"])
    parser.add_argument("--prefix", default="broll", help="Filename/manifest prefix -- use a distinct one (e.g. 'cta') for a second fetch_broll.py call on the same --job so it doesn't overwrite the first")
    args = parser.parse_args()

    pexels_key = get_key("PEXELS_API_KEY")
    pixabay_key = get_key("PIXABAY_API_KEY")
    if not pexels_key and not pixabay_key:
        print(
            "Falta PEXELS_API_KEY y/o PIXABAY_API_KEY.\n"
            f"Abre {ENV_FILE} y agrega al menos una (ambas son gratis, sin tarjeta):\n"
            "  PEXELS_API_KEY=... -> conseguila en https://www.pexels.com/api/\n"
            "  PIXABAY_API_KEY=... -> conseguila en https://pixabay.com/api/docs/\n",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(args.slots) as f:
        slots = json.load(f)

    job_dir = os.path.join(PUBLIC_DIR, "jobs", args.job)
    os.makedirs(job_dir, exist_ok=True)

    broll_entries = []
    manifest = []
    pixabay_orientation = {"portrait": "vertical", "landscape": "horizontal", "square": "vertical"}[args.orientation]

    for i, slot in enumerate(slots):
        query = slot["query"]
        result = None
        if pexels_key:
            try:
                result = search_pexels(query, pexels_key, orientation=args.orientation)
            except requests.HTTPError as e:
                print(f"  [{i}] Pexels fallo para '{query}': {e}", file=sys.stderr)
        if not result and pixabay_key:
            try:
                result = search_pixabay(query, pixabay_key, orientation=pixabay_orientation)
            except requests.HTTPError as e:
                print(f"  [{i}] Pixabay fallo para '{query}': {e}", file=sys.stderr)

        if not result:
            print(f"  [{i}] SIN RESULTADOS para '{query}' -- este slot queda vacio, revisa a mano.", file=sys.stderr)
            manifest.append({"query": query, "status": "not_found"})
            continue

        filename = f"{args.prefix}_{i:02d}.mp4"
        dest = os.path.join(job_dir, filename)
        download(result["url"], dest)
        rel_src = f"jobs/{args.job}/{filename}"
        print(f"  [{i}] '{query}' -> {rel_src} (fuente: {result['source']}, {result.get('page_url', '')})")

        broll_entries.append({"src": rel_src, "atMs": slot["atMs"], "durationMs": slot["durationMs"]})
        manifest.append({"query": query, "status": "ok", "src": rel_src, "source": result["source"], "page_url": result.get("page_url")})

    manifest_path = os.path.join(job_dir, f"{args.prefix}_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nManifiesto (con fuente y URL de cada clip, para atribucion si hace falta): {manifest_path}")
    print("\nArray 'broll' listo para pegar en el EditPlan:")
    print(json.dumps(broll_entries, indent=2, ensure_ascii=False))

    missing = [m for m in manifest if m["status"] == "not_found"]
    if missing:
        print(f"\n{len(missing)}/{len(slots)} busquedas sin resultado -- no inventes un src para esos, o busca manualmente.", file=sys.stderr)


if __name__ == "__main__":
    main()
