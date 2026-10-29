#!/usr/bin/env python3
"""
Search TikTok by keyword for REAL b-roll candidates (the user prefers TikTok footage over stock)
and build a contact sheet so you can pick by eye. Does NOT download videos: pick an index, then
`fetch_clip_url.py --url <webVideoUrl>` (yt-dlp, free) downloads/trims/normalizes it.

Uses the Apify actor clockworks/tiktok-scraper with the APIFY_TOKEN in editar-anuncios/.env
(searchQueries, no video download -> cheap: cost is per result returned). Always async + polling
(never run-sync, it cuts at ~5 min).

Usage:
  python3 find_tiktok_broll.py --query "man crying alone" --query "dark empty room" \
      --out DIR [--per-query 8] [--min-views 20000] [--min-s 3 --max-s 45]
Writes DIR/candidates.json (ranked) and DIR/sheet.jpg (numbered thumbnails with views/duration/author).
Selection rule: vertical, 3-45 s, enough views; then YOU look at the sheet -- search results are
loose matches, never pick by caption alone.
Third-party footage: say in the report it came from TikTok creators (rights unverified); the
ledger in fetch_clip_url.py records source URLs.
"""
import argparse, io, json, os, sys, time
import requests
from PIL import Image, ImageDraw

import bcc_env  # keys live in ~/.bcc-toolkit/.env (they survive plugin updates); the skill's own .env is still honoured
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = bcc_env.ENV_PATH


def token():
    t = os.environ.get("APIFY_TOKEN")
    if not t and os.path.isfile(ENV):
        for line in open(ENV):
            if line.startswith("APIFY_TOKEN="):
                t = line.split("=", 1)[1].strip()
    if not t or t.startswith("pega-aqui"):
        sys.exit("APIFY_TOKEN missing in editar-anuncios/.env (ask the user to set it; never paste it in chat)")
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-query", type=int, default=8)
    ap.add_argument("--min-views", type=int, default=20000)
    ap.add_argument("--min-s", type=float, default=3)
    ap.add_argument("--max-s", type=float, default=45)
    ap.add_argument("--timeout-s", type=int, default=600)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tk = token()
    run = requests.post(f"https://api.apify.com/v2/acts/clockworks~tiktok-scraper/runs?token={tk}",
                        json={"searchQueries": a.query, "resultsPerPage": a.per_query, "shouldDownloadVideos": False,
                              "searchSection": "/video"}, timeout=60)
    if run.status_code >= 300:
        sys.exit(f"Apify run failed to start: {run.status_code} {run.text[:300]}")
    run = run.json()["data"]
    t0 = time.time()
    while True:
        time.sleep(8)
        st = requests.get(f"https://api.apify.com/v2/actor-runs/{run['id']}?token={tk}", timeout=60).json()["data"]["status"]
        if st == "SUCCEEDED":
            break
        if st in ("FAILED", "ABORTED", "TIMED-OUT") or time.time() - t0 > a.timeout_s:
            sys.exit(f"Apify run {st}")
    items = requests.get(f"https://api.apify.com/v2/datasets/{run['defaultDatasetId']}/items?token={tk}&format=json&clean=true",
                         timeout=180).json()
    print(f"{len(items)} raw results")
    if items:
        print("fields of the first item:", sorted(items[0].keys()))
    json.dump(items, open(os.path.join(a.out, "raw.json"), "w"), ensure_ascii=False)
    cands = []
    why = {"slideshow/photo": 0, "duration": 0, "views": 0, "landscape": 0}
    for it in items:
        vm = it.get("videoMeta") or {}
        dur = vm.get("duration") or 0
        views = it.get("playCount") or 0
        if it.get("isSlideshow") or not dur:
            why["slideshow/photo"] += 1
            continue
        if not (a.min_s <= dur <= a.max_s):
            why["duration"] += 1
            continue
        if views < a.min_views:
            why["views"] += 1
            continue
        if (vm.get("width") or 0) and (vm.get("height") or 0) and vm["height"] < vm["width"]:
            why["landscape"] += 1
            continue
        cands.append({
            "url": it.get("webVideoUrl"), "views": views, "likes": it.get("diggCount"), "duration": dur,
            "author": (it.get("authorMeta") or {}).get("name"), "text": (it.get("text") or "")[:90],
            "cover": vm.get("coverUrl") or vm.get("originalCoverUrl"), "query": (it.get("searchQuery") or ""),
        })
    cands.sort(key=lambda c: -c["views"])
    dropped = len(items) - len(cands)
    print(f"{len(cands)} candidates kept; {dropped} dropped -> {why}")
    # contact sheet
    tiles = []
    for i, c in enumerate(cands[:24]):
        try:
            im = Image.open(io.BytesIO(requests.get(c["cover"], timeout=30).content)).convert("RGB")
        except Exception:
            im = Image.new("RGB", (270, 480), "gray")
        im = im.resize((270, 480))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 270, 34], fill=(0, 0, 0))
        d.text((6, 4), f"#{i}  {c['views']//1000}k views  {c['duration']:.0f}s", fill=(255, 255, 0))
        d.text((6, 18), f"@{c['author']}"[:40], fill=(255, 255, 255))
        tiles.append(im)
    if tiles:
        cols = 6
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (270 * cols, 480 * rows), "black")
        for k, im in enumerate(tiles):
            sheet.paste(im, ((k % cols) * 270, (k // cols) * 480))
        sheet.save(os.path.join(a.out, "sheet.jpg"), quality=85)
    json.dump(cands, open(os.path.join(a.out, "candidates.json"), "w"), indent=1, ensure_ascii=False)
    print("wrote", os.path.join(a.out, "candidates.json"), "and sheet.jpg")


if __name__ == "__main__":
    main()
