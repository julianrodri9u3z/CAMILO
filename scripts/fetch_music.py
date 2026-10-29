#!/usr/bin/env python3
"""
Searches Jamendo (jamendo.com) for a royalty-free, commercially-usable
track and downloads it into the Remotion project's public/ folder, ready to
be referenced from an EditPlan's `musicPath` or `cta.musicSrc`.

Why Jamendo and not Pexels/Pixabay: those two only expose images/video in
their public APIs -- neither has a documented music search endpoint. Jamendo
does (https://developer.jamendo.com), with real commercial-use filtering and
direct download URLs.

Needs JAMENDO_CLIENT_ID in .env -- free, no payment info, register at
https://devportal.jamendo.com. Claude cannot create this account for you
(account creation is off-limits for it to do on your behalf) -- sign up
yourself and drop the client_id in the .env file.

Usage:
    python3 fetch_music.py --job my-campaign --tags "cinematic,ambient" \
        --output-name music.mp3 [--min-duration-s 60] [--max-duration-s 180]

Only downloads tracks Jamendo flags as free for commercial use
(ccnc=false -- excludes NonCommercial-licensed tracks). Writes a manifest
with artist name and license URL next to the file -- some CC licenses
(CC-BY) require attribution even when commercial use is allowed, so check
that file before publishing at scale.
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

JAMENDO_SEARCH = "https://api.jamendo.com/v3.0/tracks/"


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


def get_key():
    key = os.environ.get("JAMENDO_CLIENT_ID")
    if not key:
        key = load_env_file(ENV_FILE).get("JAMENDO_CLIENT_ID")
    if not key or key.startswith("pega-aqui"):
        print(
            "Falta JAMENDO_CLIENT_ID.\n"
            f"Registrate gratis (sin tarjeta) en https://devportal.jamendo.com, "
            f"creá una app, y pegá el client_id en {ENV_FILE}.\n"
            "Esto tenés que hacerlo vos -- no puedo crear la cuenta por vos.",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def search_track(client_id, tags, min_duration_s, max_duration_s, search_text, instrumental_only):
    params = {
        "client_id": client_id,
        "format": "json",
        "limit": 5,
        "ccnc": "false",  # exclude NonCommercial-only licenses
        "ccsa": "false",  # exclude ShareAlike -- murky for a commercial ad (derivative-licensing implications)
        "audioformat": "mp32",
        "order": "popularity_total",
    }
    if instrumental_only:
        # Default ON: lyrics compete with/distract from the ad's own voiceover.
        params["vocalinstrumental"] = "instrumental"
    if tags:
        # NOTE: Jamendo's `fuzzytags` param is undocumented-strict about casing
        # (e.g. "ambient" -> 0 results, "Ambient" -> 5) -- confirmed in
        # production by testing the raw API directly. `tags` (exact tag match,
        # case-insensitive) is the reliable param; it does an AND across
        # multiple comma-separated tags, so prefer one well-known tag plus
        # `--search` free text over stacking several rare tags together.
        params["tags"] = tags
    if search_text:
        params["search"] = search_text
    if min_duration_s:
        params["durationbetween"] = f"{min_duration_s}_{max_duration_s or min_duration_s + 120}"

    resp = requests.get(JAMENDO_SEARCH, params=params, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--tags", default="", help="Comma-separated tags/genres/mood, e.g. 'cinematic,ambient,spiritual'")
    ap.add_argument("--search", default="", help="Free-text search, combined with --tags")
    ap.add_argument("--min-duration-s", type=int, default=None)
    ap.add_argument("--max-duration-s", type=int, default=None)
    ap.add_argument("--output-name", default="music.mp3")
    ap.add_argument("--allow-vocals", action="store_true", help="Skip the instrumental-only filter (default excludes tracks with lyrics -- they distract from the ad's own voiceover)")
    args = ap.parse_args()

    client_id = get_key()

    results = search_track(client_id, args.tags, args.min_duration_s, args.max_duration_s, args.search, not args.allow_vocals)
    if not results:
        print(f"Sin resultados para tags='{args.tags}' search='{args.search}'. Probá con otros tags.", file=sys.stderr)
        sys.exit(1)

    track = results[0]
    job_dir = os.path.join(PUBLIC_DIR, "jobs", args.job)
    os.makedirs(job_dir, exist_ok=True)
    raw_path = os.path.join(job_dir, "_raw_" + args.output_name)
    dest = os.path.join(job_dir, args.output_name)

    audio_resp = requests.get(track["audiodownload"], stream=True, timeout=60)
    audio_resp.raise_for_status()
    with open(raw_path, "wb") as f:
        for chunk in audio_resp.iter_content(chunk_size=1 << 16):
            f.write(chunk)

    # Jamendo tracks vary wildly in mastering loudness -- ambient/meditation
    # tracks in particular are often mixed very quiet and end up inaudible
    # under a video. Normalize to a fixed loudness target (-16 LUFS, a safe
    # level for background music under dialogue) so every fetched track is
    # consistently audible regardless of source mastering.
    normalize_result = subprocess.run(
        ["ffmpeg", "-y", "-i", raw_path, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", dest],
        capture_output=True, text=True,
    )
    if normalize_result.returncode != 0:
        print("loudnorm fallo, uso el audio sin normalizar:\n" + normalize_result.stderr[-1500:], file=sys.stderr)
        os.replace(raw_path, dest)
    else:
        os.remove(raw_path)

    rel_src = f"jobs/{args.job}/{args.output_name}"
    manifest_path = os.path.join(job_dir, f"{args.output_name}.manifest.json")
    manifest = {
        "track_name": track.get("name"),
        "artist_name": track.get("artist_name"),
        "license_ccurl": track.get("license_ccurl"),
        "duration_s": track.get("duration"),
        "jamendo_page": f"https://www.jamendo.com/track/{track.get('id')}",
        "src": rel_src,
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"'{track.get('name')}' de {track.get('artist_name')} ({track.get('duration')}s) -> {rel_src}")
    print(f"Licencia: {track.get('license_ccurl')} -- revisar si pide atribucion antes de publicar.")
    print(f"Manifiesto: {manifest_path}")
    print(f"\nmusicPath para el EditPlan: \"{rel_src}\"")


if __name__ == "__main__":
    main()
