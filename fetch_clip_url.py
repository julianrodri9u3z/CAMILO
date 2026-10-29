#!/usr/bin/env python3
"""
Download a clip from a URL (TikTok, YouTube, Instagram, X... anything yt-dlp supports),
optionally trim it, and leave it ready to use as b-roll inside
remotion/public/jobs/<job>/<name>.mp4 -- normalized to H.264 with short keyframes
(see prepare_source.py for why) and muted-friendly (audio kept; BrollLayer mutes it).

Why this exists: the user prefers b-roll taken from TikTok/real footage (the person
himself, movie scenes, news segments) over stock. Finding the right URL is a search task
(browser / web search / the user sends links); this script does the mechanical part.

Usage:
  python3 fetch_clip_url.py --url https://www.tiktok.com/@x/video/123 --job <slug> --name sad_scene \
      [--start 3.5 --end 9] [--vertical]      # --vertical: crop/pad to 1080x1920 cover
Prints the `broll` entry source path: jobs/<job>/<name>.mp4
Also appends the clip to jobs/<job>/sources_ledger.json (url, date, interval, checksum, rights note).
Uses personal/local use only unless the user decides otherwise: third-party footage can trigger
copyright claims on Meta/TikTok -- say so in the report.
"""
import argparse, datetime, hashlib, json, os, subprocess, sys, tempfile, time

import bcc_env  # keys live in ~/.bcc-toolkit/.env (they survive plugin updates); the skill's own .env is still honoured
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTION_PUBLIC = os.path.join(SKILL_DIR, "remotion", "public")


def apify_download(url, dst_dir):
    """Fallback when yt-dlp cannot get a TikTok (some posts return 'Video not available'): let the Apify actor fetch
    the file (postURLs + shouldDownloadVideos) and download its mediaUrls[0]. Needs APIFY_TOKEN in .env (costs cents)."""
    import requests
    token = os.environ.get("APIFY_TOKEN")
    envp = os.path.join(SKILL_DIR, ".env")
    if not token and os.path.isfile(envp):
        for line in open(envp):
            if line.startswith("APIFY_TOKEN="):
                token = line.split("=", 1)[1].strip()
    if not token or token.startswith("pega-aqui") or "tiktok.com" not in url:
        return None
    run = requests.post(f"https://api.apify.com/v2/acts/clockworks~tiktok-scraper/runs?token={token}",
                        json={"postURLs": [url], "resultsPerPage": 1, "shouldDownloadVideos": True}, timeout=60)
    if run.status_code >= 300:
        return None
    run = run.json()["data"]
    t0 = time.time()
    while time.time() - t0 < 600:
        time.sleep(6)
        st = requests.get(f"https://api.apify.com/v2/actor-runs/{run['id']}?token={token}", timeout=60).json()["data"]["status"]
        if st == "SUCCEEDED":
            break
        if st in ("FAILED", "ABORTED", "TIMED-OUT"):
            return None
    items = requests.get(f"https://api.apify.com/v2/datasets/{run['defaultDatasetId']}/items?token={token}&format=json&clean=true", timeout=120).json()
    media = (items[0].get("mediaUrls") or []) if items else []
    if not media:
        return None
    dst = os.path.join(dst_dir, "dl.mp4")
    murl = media[0]
    if "api.apify.com" in murl and "token=" not in murl:
        murl += ("&" if "?" in murl else "?") + f"token={token}"   # key-value-store records are private
    with requests.get(murl, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(dst, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--job", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--start", type=float)
    ap.add_argument("--end", type=float)
    ap.add_argument("--vertical", action="store_true", help="cover-crop to 1080x1920")
    a = ap.parse_args()
    out_dir = os.path.join(REMOTION_PUBLIC, "jobs", a.job)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{a.name}.mp4")
    with tempfile.TemporaryDirectory() as tmp:
        dl = os.path.join(tmp, "dl.%(ext)s")
        r = subprocess.run(["yt-dlp", "-o", dl, "-f", "bv*+ba/b", "--merge-output-format", "mp4", "--no-playlist", a.url],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        files = [f for f in os.listdir(tmp) if f.startswith("dl.")]
        if r.returncode != 0 or not files:
            print("yt-dlp failed, trying the Apify fallback...", file=sys.stderr)
            got = apify_download(a.url, tmp)
            if not got:
                print("download failed:", (r.stderr or r.stdout)[-400:], file=sys.stderr)
                sys.exit(1)
            files = [os.path.basename(got)]
        src = os.path.join(tmp, files[0])
        cmd = ["ffmpeg", "-y", "-v", "error"]
        if a.start is not None:
            cmd += ["-ss", str(a.start)]
        cmd += ["-i", src]
        if a.end is not None:
            cmd += ["-t", str((a.end - (a.start or 0)))]
        if a.vertical:
            cmd += ["-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"]
        cmd += ["-c:v", "libx264", "-crf", "16", "-preset", "fast", "-g", "12", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
        subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()
    # Source ledger: where every third-party clip came from, so rights questions can be answered later.
    ledger_path = os.path.join(out_dir, "sources_ledger.json")
    ledger = json.load(open(ledger_path)) if os.path.isfile(ledger_path) else []
    ledger = [e for e in ledger if e.get("file") != f"{a.name}.mp4"]
    ledger.append({
        "file": f"{a.name}.mp4", "url": a.url, "accessedAt": datetime.date.today().isoformat(),
        "interval_s": [a.start, a.end], "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest(),
        "rights": "unverified third-party footage (platform creator); decide with the user before publishing",
    })
    json.dump(ledger, open(ledger_path, "w"), indent=1)
    print(f"ok: {out} ({float(d):.1f}s)\nsrc for the plan: jobs/{a.job}/{a.name}.mp4")


if __name__ == "__main__":
    main()
