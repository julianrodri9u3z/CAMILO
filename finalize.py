#!/usr/bin/env python3
"""
Final mastering + delivery encode (replaces the ad-hoc `ffmpeg -crf 24` step).

  1. Measures loudness (EBU R128) of the render's audio.
  2. Two-pass `loudnorm` to a social-media target (default -14 LUFS integrated, -1.5 dBTP) --
     voice-led edits straight out of Remotion are usually 6-10 dB too quiet next to what
     TikTok/Reels viewers hear in the feed, one of the quiet tells of an "amateur" export.
  3. Encodes H.264 (CRF 21 capped at 8 Mbps, yuv420p, faststart) + AAC 192k @ 48 kHz.
  4. Re-measures and prints before/after.

Usage:
  python3 finalize.py --video render.mp4 --out final.mp4 [--lufs -14] [--tp -1.5] [--crf 18]
"""
import argparse, json, re, subprocess, sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)


def measure(path, I=-14.0, TP=-1.5, LRA=11.0):
    r = run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-vn", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise SystemExit("could not measure loudness (no audio stream?):\n" + r.stderr[-400:])
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.5)
    ap.add_argument("--lra", type=float, default=11.0)
    ap.add_argument("--crf", type=int, default=21)
    ap.add_argument("--maxrate", default="8M", help="bitrate cap for social delivery (film grain is expensive to encode)")
    ap.add_argument("--preset", default="medium")
    a = ap.parse_args()
    m = measure(a.video, a.lufs, a.tp, a.lra)
    print(f"before: {float(m['input_i']):.1f} LUFS, true peak {float(m['input_tp']):.1f} dBTP, LRA {float(m['input_lra']):.1f}")
    af = (f"loudnorm=I={a.lufs}:TP={a.tp}:LRA={a.lra}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    r = run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-af", af, "-c:v", "libx264", "-crf", str(a.crf), "-preset", a.preset,
             "-maxrate", a.maxrate, "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out])
    if r.returncode != 0:
        sys.exit("encode failed: " + r.stderr[-500:])
    m2 = measure(a.out, a.lufs, a.tp, a.lra)
    print(f"after:  {float(m2['input_i']):.1f} LUFS, true peak {float(m2['input_tp']):.1f} dBTP, LRA {float(m2['input_lra']):.1f}  -> {a.out}")


if __name__ == "__main__":
    main()
