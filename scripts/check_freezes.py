#!/usr/bin/env python3
"""
Detect frozen picture in a RENDERED video (the picture stops while audio/captions go on).
Run it in the self-review step (editar-anuncios step 10) on every full render.

A talking-head video should have no stretch where consecutive frames are identical for
>= --min-s seconds, except where the plan itself holds a still (a title card, a held image).
Pass --source to also analyze the original: freezes that exist only in the render are bugs
(most often an HEVC / long-GOP source -- run scripts/prepare_source.py and re-render).

Usage:
  python3 check_freezes.py --video final.mp4 [--source raw.mp4] [--min-s 0.4]
Exit code 1 if the render has freezes the source does not.
"""
import argparse, re, subprocess, sys


def freezes(path, min_s, limit_s=None):
    cmd = ["ffmpeg", "-i", path]
    if limit_s:
        cmd += ["-t", str(limit_s)]
    cmd += ["-vf", f"freezedetect=n=-60dB:d={min_s}", "-an", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    starts = [float(x) for x in re.findall(r"freeze_start: ([0-9.]+)", r.stderr)]
    durs = [float(x) for x in re.findall(r"freeze_duration: ([0-9.]+)", r.stderr)]
    return list(zip(starts, durs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--source")
    ap.add_argument("--min-s", type=float, default=0.4)
    a = ap.parse_args()
    out = freezes(a.video, a.min_s)
    src = freezes(a.source, a.min_s) if a.source else []
    print(f"render: {len(out)} frozen stretch(es) >= {a.min_s}s")
    for s, d in out:
        print(f"  {int(s)//60:02d}:{s%60:05.2f}  ({d:.1f}s)")
    if a.source:
        print(f"source: {len(src)} frozen stretch(es)")
    if len(out) > len(src):
        print("FREEZES NOT PRESENT IN THE SOURCE -> likely a decoding problem. Normalize the source with "
              "scripts/prepare_source.py (H.264, short GOP) and re-render; re-check.")
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
