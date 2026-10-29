#!/usr/bin/env python3
"""
Normalize a raw source video before it goes into remotion/public/jobs/<slug>/.

WHY (learned 2026-10, The Rock podcast test): Remotion's OffthreadVideo decodes by
seeking to a timestamp. HEVC/H.265 sources (what TikTok/yt-dlp serves as "bytevc1",
and iPhone/CapCut exports) use B-frames and long GOPs; in a full render the picture
intermittently FROZE for 0.5-2 s while audio and captions kept going (9 freezes in
75 s, source had none). Re-encoding to H.264 with short GOPs rendered clean.

What it does: probes the file; if the video codec is not h264, or the GOP is long, or
the frame rate is variable, re-encodes to H.264 (CRF 16, keyframe every 12 frames,
yuv420p, AAC audio). Frame rate is kept (no resampling). A file that is already
safe is just copied. Never touches audio content.

Usage:
  python3 prepare_source.py --video in.mp4 --out <skill>/remotion/public/jobs/<slug>/raw.mp4
  python3 prepare_source.py --video in.mp4 --check     # only report, write nothing
"""
import argparse, json, shutil, subprocess, sys


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_name,r_frame_rate,avg_frame_rate,has_b_frames,pix_fmt",
                        "-of", "json", path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return json.loads(r.stdout)["streams"][0]


def keyframe_gap_s(path, seconds=20):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey",
                        "-show_entries", "frame=pts_time", "-read_intervals", f"%+{seconds}", "-of", "csv=p=0", path],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    ts = [float(x.strip(",")) for x in r.stdout.split() if x.strip(",").replace(".", "", 1).isdigit()]
    return max((b - a for a, b in zip(ts, ts[1:])), default=0.0)


def fps_of(frac):
    n, d = (frac.split("/") + ["1"])[:2]
    return float(n) / float(d) if float(d) else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    s = probe(a.video)
    gap = keyframe_gap_s(a.video)
    vfr = abs(fps_of(s["r_frame_rate"]) - fps_of(s["avg_frame_rate"])) > 0.05
    reasons = []
    if s["codec_name"] != "h264":
        reasons.append(f"codec {s['codec_name']} (not h264)")
    if gap > 1.0:
        reasons.append(f"keyframes every {gap:.1f}s (long GOP)")
    if vfr:
        reasons.append("variable frame rate")
    print(f"{a.video}: codec={s['codec_name']} fps={s['r_frame_rate']} max keyframe gap={gap:.2f}s ->",
          "RE-ENCODE: " + "; ".join(reasons) if reasons else "ok as is")
    if a.check or not a.out:
        sys.exit(0)
    if not reasons:
        shutil.copyfile(a.video, a.out)
        print("copied:", a.out)
        return
    # -bf 0: no B-frames. With them, Remotion's compositor intermittently failed to seek ("No frame found at
    # position ...", seen 2026-10-29 on a re-encoded HEVC A-roll) when several frames are read in parallel.
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.video, "-c:v", "libx264", "-crf", "16", "-preset", "fast",
           "-g", "12", "-bf", "0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart"]
    if vfr:
        cmd += ["-vsync", "cfr", "-r", str(round(fps_of(s["avg_frame_rate"]), 3))]
    subprocess.run(cmd + [a.out], check=True, stdin=subprocess.DEVNULL)
    print("re-encoded:", a.out)


if __name__ == "__main__":
    main()
