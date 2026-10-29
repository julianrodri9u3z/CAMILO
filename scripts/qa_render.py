#!/usr/bin/env python3
"""
Pre-delivery quality gate for a RENDERED ad (run after finalize.py, before sending it).
Codifies "reject low-quality completion" so the checks stop depending on my eyes alone.

Checks (FAIL = fix and re-render; WARN = look at it):
  FAIL  frozen picture the source doesn't have          (freezedetect; needs --source to compare)
  FAIL  black frames in the middle of the video          (blackdetect, ignores first/last 0.5 s)
  FAIL  audio clipping / true peak above -1 dBTP
  WARN  integrated loudness outside -16..-12 LUFS        (social feed target is about -14)
  WARN  dead air: silence >= 1.5 s in the middle         (unless the piece is music-led)
  WARN  (with --plan) captions faster than 32 chars/s over 8 words, overlay pile-ups (>3 events in 1 s),
        sound hits denser than 1 per 0.8 s, b-roll shorter than 1.2 s

Usage:
  python3 qa_render.py --video final.mp4 [--source raw.mp4] [--plan job.json]
Exit code 1 on any FAIL.
"""
import argparse, json, re, subprocess, sys


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner"] + args, capture_output=True, text=True, stdin=subprocess.DEVNULL).stderr


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                        "-of", "json", path], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return json.loads(r.stdout)


def freezes(path, limit=None):
    a = ["-i", path] + (["-t", str(limit)] if limit else []) + ["-vf", "freezedetect=n=-60dB:d=0.4", "-an", "-f", "null", "-"]
    err = ff(a)
    return list(zip([float(x) for x in re.findall(r"freeze_start: ([0-9.]+)", err)], [float(x) for x in re.findall(r"freeze_duration: ([0-9.]+)", err)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--source")
    ap.add_argument("--plan")
    a = ap.parse_args()
    fails, warns = [], []
    info = probe(a.video)
    dur = float(info["format"]["duration"])
    streams = {s["codec_type"]: s for s in info["streams"]}
    print(f"{a.video}: {dur:.1f}s {streams['video']['width']}x{streams['video']['height']} {streams['video']['r_frame_rate']} audio={'yes' if 'audio' in streams else 'NO'}")
    if "audio" not in streams:
        fails.append("no audio stream")

    fr = freezes(a.video)
    src_fr = freezes(a.source) if a.source else []
    if len(fr) > len(src_fr):
        fails.append(f"{len(fr)} frozen stretches (source has {len(src_fr)}): " + ", ".join(f"{s:.1f}s(+{d:.1f})" for s, d in fr[:6]) +
                     " -> run prepare_source.py on the raw footage and re-render")

    err = ff(["-i", a.video, "-vf", "blackdetect=d=0.2:pix_th=0.06", "-an", "-f", "null", "-"])
    blacks = [(float(s), float(e)) for s, e in re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", err)]
    mid = [(s, e) for s, e in blacks if s > 0.5 and e < dur - 0.5]
    if mid:
        fails.append("black frames mid-video: " + ", ".join(f"{s:.1f}-{e:.1f}s" for s, e in mid))

    if "audio" in streams:
        err = ff(["-i", a.video, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"])
        mI = re.findall(r"I:\s+(-?[0-9.]+) LUFS", err)
        mP = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", err)
        if mI:
            I = float(mI[-1])
            print(f"loudness: {I:.1f} LUFS" + (f", true peak {mP[-1]} dBTP" if mP else ""))
            if not (-16 <= I <= -12):
                warns.append(f"integrated loudness {I:.1f} LUFS (target about -14): run finalize.py")
        if mP and float(mP[-1]) > -1.0:
            fails.append(f"true peak {mP[-1]} dBTP (> -1): clipping risk, run finalize.py")
        err = ff(["-i", a.video, "-af", "silencedetect=n=-45dB:d=1.5", "-vn", "-f", "null", "-"])
        sil = [(float(s)) for s in re.findall(r"silence_start: ([0-9.]+)", err)]
        sil = [s for s in sil if 0.5 < s < dur - 2.0]
        if sil:
            warns.append("dead air (>=1.5 s silence) at " + ", ".join(f"{s:.1f}s" for s in sil[:6]))

    if a.plan:
        p = json.load(open(a.plan))
        caps = p.get("captions", [])
        if caps:
            bad = 0
            for i in range(0, len(caps) - 7, 8):
                grp = caps[i:i + 8]
                chars = sum(len(w["text"]) + 1 for w in grp)
                secs = max(0.2, (grp[-1]["endMs"] - grp[0]["startMs"]) / 1000)
                if chars / secs > 32:
                    bad += 1
            if bad:
                warns.append(f"{bad} caption phrase(s) faster than 32 chars/s over 8 words (hard to read; typical fast speech is ~19)")
        ev = []
        for k in ("keywordCallouts", "statCallouts", "badges", "titleCards", "lowerThirds", "proofStacks", "ctaButtons", "priceStacks", "guaranteeSeals", "imageCards", "arrows", "highlightCircles"):
            ev += [o["atMs"] for o in p.get(k, []) or [] if "atMs" in o]
        ev += [b["atMs"] for b in p.get("broll", [])]
        ev.sort()
        if any(ev[i + 3] - ev[i] < 1000 for i in range(len(ev) - 3)):
            warns.append("4+ visual events inside one second (decorative pile-up; keep one primary emphasis per beat)")
        sfx = sorted(h["atMs"] for h in p.get("sfx", []) or [])
        if any(sfx[i + 1] - sfx[i] < 800 for i in range(len(sfx) - 1)):
            warns.append("sound hits closer than 0.8 s apart")
        short = [b for b in p.get("broll", []) if b["durationMs"] < 1200]
        if short:
            warns.append(f"{len(short)} b-roll insert(s) shorter than 1.2 s (read as flicker)")

    for f in fails:
        print("FAIL:", f)
    for w in warns:
        print("WARN:", w)
    if not fails and not warns:
        print("PASS: no issues found")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
