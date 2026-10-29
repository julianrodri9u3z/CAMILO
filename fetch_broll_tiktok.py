#!/usr/bin/env python3
"""
Alternative b-roll source to fetch_broll.py: searches TikTok itself (via the
same Apify `clockworks/tiktok-scraper` actor already used for content mining)
instead of Pexels/Pixabay -- for when the generic stock look isn't native
enough for a niche (real user feedback: "los bancos de vídeos que usamos son
muy genéricos").

Two-step, cost-guarded by design -- NEVER search-and-download in one shot:

  search    Cheap. Fetches N candidates for one query (text + cover thumbnail
            only, no video download) and saves them to candidates.json plus
            local cover_NN.jpg files. Nothing here costs more than a few
            cents even for several queries.
  download  Only after a human (or Claude, reading the covers) has PICKED
            one candidate index from that json -- downloads just that one
            video, trims it to the needed span, mutes it, and copies it into
            remotion/public/jobs/<job>/ ready for the EditPlan's `broll[]`.

Why split like this: `shouldDownloadVideos` is a paid add-on per item, and
`resultsPerPage` defaults to 100 in the actor's own UI -- calling it once
with a big page size and video download on is how a routine unintentionally
burns real money (this happened once already, in the daily-mining routine
this same actor powers). Searching first and downloading only the one clip
actually used keeps a whole ad's worth of b-roll (several slots) under
$0.15 total. `search` still prints its own estimated cost before running,
same discipline as `video-ads-avatar`'s pipeline.py.

COPYRIGHT / ACCOUNT-RISK NOTE (read before picking a candidate): unlike
Pexels/Pixabay, TikTok clips are NOT licensed for reuse inside someone
else's paid ad -- this carries real copyright and ad-account-ban risk,
worse than the equivalent question for background music because it's full
video and more recognizable. The agreed mitigation (confirmed with the
user): only use candidates that are generic, faceless b-roll -- hands,
objects, candles, textures, no identifiable person, no visible watermark or
branding of the original creator. That judgment call is NOT automatable
from metadata alone -- always look at each candidate's downloaded cover
image (`cover_NN.jpg`) before calling `download`, and skip any candidate
whose thumbnail shows a recognizable face or on-screen branding, even if
its text/thumbnail otherwise matches the query well.

Usage:
    python3 fetch_broll_tiktok.py search \
        --query "velas encendidas mesa" --count 6 --output-dir /tmp/broll-tt/velas

    # look at /tmp/broll-tt/velas/cover_*.jpg, pick an index, then:
    python3 fetch_broll_tiktok.py download \
        --candidates /tmp/broll-tt/velas/candidates.json --index 2 \
        --job my-campaign --name velas_01 \
        --at-ms 4500 --duration-ms 2000 [--trim-start-s 3.0]
"""
import argparse
import json
import os
import subprocess
import sys

import requests

import bcc_env  # keys live in ~/.bcc-toolkit/.env (they survive plugin updates); the skill's own .env is still honoured
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = bcc_env.ENV_PATH   # messages point at the persistent file
PUBLIC_DIR = os.path.join(SKILL_DIR, "remotion", "public")

ACTOR_RUN_URL = "https://api.apify.com/v2/acts/clockworks~tiktok-scraper/run-sync-get-dataset-items"

# FREE-tier per-event pricing (api.apify.com pricing for clockworks/tiktok-scraper,
# checked directly -- PAY_PER_EVENT model). Real cost may be lower once the
# account's usage tier climbs (BRONZE/SILVER/...), this is the conservative
# ceiling to show upfront.
PRICE_ACTOR_START = 0.001
PRICE_RESULT = 0.0037
PRICE_VIDEO_DOWNLOAD_ADDON = 0.0013


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


def get_token():
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        token = load_env_file(ENV_FILE).get("APIFY_TOKEN")
    if not token or token.startswith("pega-aqui"):
        print(
            f"Falta APIFY_TOKEN en {ENV_FILE} (o como variable de entorno).\n"
            "Es el mismo token que ya usas para minar TikTok -- copialo desde "
            "el .env del proyecto o desde console.apify.com/settings/integrations.",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def cmd_search(args):
    token = get_token()
    count = min(args.count, 10)  # hard cap -- this is b-roll picking, not mining
    est_cost = PRICE_ACTOR_START + count * PRICE_RESULT
    print(f"Costo estimado de esta busqueda (tier FREE, techo conservador): ~${est_cost:.3f} ({count} candidatos, solo texto+portada, sin descargar video todavia)")

    resp = requests.post(
        ACTOR_RUN_URL,
        params={"token": token},
        json={
            "searchQueries": [args.query],
            "resultsPerPage": count,
            "searchSection": "/video",
            "shouldDownloadCovers": True,
            "shouldDownloadVideos": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    items = resp.json()
    if not items:
        print(f"Sin resultados para '{args.query}'. Proba con otra query.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    candidates = []
    for i, it in enumerate(items):
        vm = it.get("videoMeta", {})
        cover_url = vm.get("coverUrl") or vm.get("originalCoverUrl")
        cover_path = None
        if cover_url:
            cover_path = os.path.join(args.output_dir, f"cover_{i:02d}.jpg")
            try:
                # Apify key-value-store record URLs need the token too, not
                # just the actor-run call itself -- confirmed via a 403
                # without it.
                cr = requests.get(cover_url, params={"token": token}, timeout=30)
                cr.raise_for_status()
                with open(cover_path, "wb") as f:
                    f.write(cr.content)
            except requests.RequestException as e:
                print(f"  [{i}] no se pudo bajar la portada: {e}", file=sys.stderr)
                cover_path = None

        candidates.append({
            "index": i,
            "id": it.get("id"),
            "text": (it.get("text") or "")[:200],
            "author": it.get("authorMeta", {}).get("name"),
            "play_count": it.get("playCount"),
            "duration_s": vm.get("duration"),
            "web_video_url": it.get("webVideoUrl"),
            "cover_local_path": cover_path,
        })
        print(f"  [{i}] @{candidates[-1]['author']} ({candidates[-1]['duration_s']}s, {candidates[-1]['play_count']} plays) -- \"{candidates[-1]['text'][:80]}\"")
        if cover_path:
            print(f"        portada: {cover_path}")

    candidates_path = os.path.join(args.output_dir, "candidates.json")
    with open(candidates_path, "w") as f:
        json.dump({"query": args.query, "candidates": candidates}, f, indent=2, ensure_ascii=False)

    print(f"\n{len(candidates)} candidatos guardados en {candidates_path}")
    print(
        "\nANTES de descargar ninguno: mira cada cover_NN.jpg con la herramienta de "
        "lectura de imagenes y descarta cualquiera con rostro identificable o marca/"
        "watermark del creador original a la vista -- preferi tomas genericas (manos, "
        "objetos, texturas, velas, sin persona reconocible). Reciennnn ahi corre "
        "'download' con el indice elegido."
    )


def cmd_download(args):
    token = get_token()
    with open(args.candidates) as f:
        data = json.load(f)
    matches = [c for c in data["candidates"] if c["index"] == args.index]
    if not matches:
        print(f"No hay candidato con index={args.index} en {args.candidates}", file=sys.stderr)
        sys.exit(1)
    cand = matches[0]

    # 'search' deliberately does NOT request shouldDownloadVideos (that's a
    # paid add-on, and paying it for every candidate just to look at covers
    # would defeat the whole point of the two-step split) -- so download_addr
    # is only fetched now, scoped to just the ONE candidate actually picked.
    est_cost = PRICE_ACTOR_START + PRICE_RESULT + PRICE_VIDEO_DOWNLOAD_ADDON
    print(f"Costo estimado de esta descarga: ~${est_cost:.4f}")
    print(f"Re-consultando @{cand['author']} para obtener el video ({cand['web_video_url']})...")
    resp = requests.post(
        ACTOR_RUN_URL,
        params={"token": token},
        json={"postURLs": [cand["web_video_url"]], "shouldDownloadVideos": True},
        timeout=120,
    )
    resp.raise_for_status()
    items = resp.json()
    if not items or not items[0].get("videoMeta", {}).get("downloadAddr"):
        print(f"No se pudo obtener el video para {cand['web_video_url']} -- puede haberse borrado.", file=sys.stderr)
        sys.exit(1)
    download_addr = items[0]["videoMeta"]["downloadAddr"]
    print(f"Descargando @{cand['author']}...")

    job_dir = os.path.join(PUBLIC_DIR, "jobs", args.job)
    os.makedirs(job_dir, exist_ok=True)
    raw_path = os.path.join(job_dir, f"_raw_{args.name}.mp4")
    dest_path = os.path.join(job_dir, f"{args.name}.mp4")

    r = requests.get(download_addr, params={"token": token}, stream=True, timeout=180)
    r.raise_for_status()
    with open(raw_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 16):
            f.write(chunk)

    # Trim to just the needed span, re-encode for Remotion compatibility, and
    # strip audio at the source (BrollLayer.tsx already forces muted on
    # render -- this just removes the possibility entirely, on top of
    # shrinking the file).
    trim_start = args.trim_start_s if args.trim_start_s is not None else 0.0
    trim_duration = args.duration_ms / 1000
    cmd = [
        "ffmpeg", "-nostdin", "-y",
        "-ss", str(trim_start), "-i", raw_path, "-t", str(trim_duration),
        "-an", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        dest_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(raw_path)
    if result.returncode != 0:
        print("ffmpeg fallo al recortar:\n" + result.stderr[-3000:], file=sys.stderr)
        sys.exit(1)

    rel_src = f"jobs/{args.job}/{args.name}.mp4"
    manifest_path = os.path.join(job_dir, f"{args.name}.manifest.json")
    manifest = {
        "source": "tiktok",
        "tiktok_id": cand["id"],
        "author": cand["author"],
        "web_video_url": cand["web_video_url"],
        "text": cand["text"],
        "trimmed_from_s": trim_start,
        "trimmed_duration_s": trim_duration,
        "src": rel_src,
        "copyright_note": "Clip ajeno de TikTok, no licenciado -- reusado en el anuncio con riesgo de copyright/cuenta asumido explicitamente por el usuario. Ver nota en fetch_broll_tiktok.py.",
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n-> {rel_src}")
    print(f"Manifiesto (trazabilidad del origen, por si hace falta ante un reclamo): {manifest_path}")
    print("\nEntrada 'broll' lista para pegar en el EditPlan:")
    print(json.dumps({"src": rel_src, "atMs": args.at_ms, "durationMs": args.duration_ms}, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("--query", required=True, help="Texto de busqueda en TikTok, en el idioma/estilo que usarian los creadores del nicho")
    p_search.add_argument("--count", type=int, default=6, help="Candidatos a traer (tope 10 -- esto es para elegir 1, no para minar)")
    p_search.add_argument("--output-dir", required=True)
    p_search.set_defaults(func=cmd_search)

    p_download = sub.add_parser("download")
    p_download.add_argument("--candidates", required=True, help="Path a candidates.json de un 'search' previo")
    p_download.add_argument("--index", type=int, required=True, help="Indice del candidato elegido (visto en la salida de 'search')")
    p_download.add_argument("--job", required=True, help="Job slug -- destino remotion/public/jobs/<job>/")
    p_download.add_argument("--name", required=True, help="Nombre de archivo sin extension, ej. 'velas_01'")
    p_download.add_argument("--at-ms", type=int, required=True, help="atMs para la entrada broll del EditPlan")
    p_download.add_argument("--duration-ms", type=int, required=True, help="Cuanto del clip usar, en ms -- casi nunca el TikTok completo")
    p_download.add_argument("--trim-start-s", type=float, default=None, help="Segundo del video original de TikTok donde empezar a recortar (default: desde el inicio)")
    p_download.set_defaults(func=cmd_download)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
