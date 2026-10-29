#!/usr/bin/env python3
"""
Self-QA helper for the auto-revisión step (Part B, paso 10 in SKILL.md).
Renders one PNG combining a filmstrip (N evenly-spaced thumbnails) and an
audio waveform for a time window -- so a single Read of one image lets Claude
check for a visual jump-cut AND an audio pop at a cut boundary, instead of
extracting and looking at several separate frames per check.

Technique adapted from the video-use project's `timeline_view.py`
(https://github.com/browser-use/video-use) -- same idea (on-demand
filmstrip+waveform composite at decision points, not a full frame scan),
reimplemented here with plain ffmpeg (no extra Python deps).

Usage:
    python3 timeline_check.py --video final.mp4 --at-s 62.4 --output /tmp/check.png
    python3 timeline_check.py --video final.mp4 --start-s 60 --end-s 66 --output /tmp/check.png
"""
import argparse
import subprocess
import sys


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg fallo:\n" + result.stderr[-3000:], file=sys.stderr)
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--at-s", type=float, help="Center point -- combine with --window-s")
    ap.add_argument("--window-s", type=float, default=3.0, help="Total window width when using --at-s (default 3s, so 1.5s each side)")
    ap.add_argument("--start-s", type=float, help="Explicit window start (alternative to --at-s)")
    ap.add_argument("--end-s", type=float, help="Explicit window end")
    ap.add_argument("--n-thumbs", type=int, default=8)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    if args.at_s is not None:
        start = max(0.0, args.at_s - args.window_s / 2)
        end = args.at_s + args.window_s / 2
    elif args.start_s is not None and args.end_s is not None:
        start, end = args.start_s, args.end_s
    else:
        print("Pasa --at-s (+ opcional --window-s) o --start-s/--end-s.", file=sys.stderr)
        sys.exit(1)

    duration = end - start
    if duration <= 0:
        print("La ventana tiene que tener duracion positiva.", file=sys.stderr)
        sys.exit(1)

    filmstrip_png = args.output + ".filmstrip.png"
    waveform_png = args.output + ".waveform.png"

    fps = args.n_thumbs / duration
    run([
        "ffmpeg", "-y", "-ss", str(start), "-i", args.video, "-t", str(duration),
        "-vf", f"fps={fps:.4f},scale=180:-1,tile={args.n_thumbs}x1",
        "-frames:v", "1", filmstrip_png,
    ])

    run([
        "ffmpeg", "-y", "-ss", str(start), "-i", args.video, "-t", str(duration),
        "-filter_complex", "showwavespic=s=1440x200:colors=white",
        "-frames:v", "1", waveform_png,
    ])

    run([
        "ffmpeg", "-y", "-i", filmstrip_png, "-i", waveform_png,
        "-filter_complex", "[0:v]scale=1440:-1[top];[top][1:v]vstack=inputs=2",
        "-frames:v", "1", args.output,
    ])

    print(f"Ventana [{start:.2f}s - {end:.2f}s] ({duration:.2f}s, {args.n_thumbs} thumbnails + waveform): {args.output}")
    print("Mira este PNG con la herramienta de lectura de imagenes -- fila de arriba son frames en orden, fila de abajo es la forma de onda del audio en la misma ventana. Un salto visual raro en la fila de arriba o un pico/silencio abrupto en la onda marcan un problema en ese punto.")


if __name__ == "__main__":
    main()
