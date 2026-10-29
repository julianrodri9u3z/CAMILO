#!/usr/bin/env python3
"""
Make graphics/inserts land ON the music's beat (and put a drop on a key moment) using beat_grid.py output.
This is the numeric replacement for "feeling the rhythm": every number is checked, nothing is guessed by ear.

Two operations on an EditPlan:
  1. SNAP   move the start of overlays/b-roll to the nearest beat if it is within --tol-ms (default 140 ms, i.e.
            imperceptible against speech but tight against the groove). Keeps durations, never moves an event
            earlier than 0 or past its own end; speech-synced cuts (clips) are NEVER touched.
  2. DROP   --align-drop VIDEO_MS: choose musicOffsetSeconds so the music's bass drop (--drop-index, default
            the first) hits exactly at that video time (e.g. the price reveal or the first CTA).

Usage:
  python3 beat_snap.py --plan job.json --beats beats.json [--out job.json] [--grid beats|downbeats]
                       [--tol-ms 140] [--align-drop 12500 --drop-index 0]
Reports mean |event - nearest beat| before and after (the verification).
Only worth doing when the music is audible/prominent (UGC, montage, promo). On a voice-led piece with the music
at -25 dB, snapping adds nothing a viewer can feel -- use --tol-ms 0 / skip it.
"""
import argparse, json
import numpy as np

EVENT_KEYS = ["keywordCallouts", "statCallouts", "badges", "titleCards", "lowerThirds", "proofStacks", "priceStacks",
              "guaranteeSeals", "ctaButtons", "imageCards", "arrows", "highlightCircles", "stickers", "bubbles", "broll"]


def nearest(grid, t):
    i = int(np.argmin(np.abs(grid - t)))
    return grid[i]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--beats", required=True)
    ap.add_argument("--out")
    ap.add_argument("--grid", default="beats", choices=["beats", "downbeats"])
    ap.add_argument("--tol-ms", type=float, default=140)
    ap.add_argument("--align-drop", type=float, help="video time (ms) where a bass drop should land")
    ap.add_argument("--drop-index", type=int, default=0)
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    bt = json.load(open(a.beats))
    offset = float(plan.get("musicOffsetSeconds") or 0)
    if a.align_drop is not None:
        if not bt["drops"]:
            raise SystemExit("no drops found in the music; cannot align")
        d = bt["drops"][min(a.drop_index, len(bt["drops"]) - 1)]["t"]
        offset = d - a.align_drop / 1000.0
        plan["musicOffsetSeconds"] = round(offset, 3)
        print(f"drop at music {d:.2f}s -> video {a.align_drop/1000:.2f}s: musicOffsetSeconds = {offset:.3f}"
              + ("  (music is delayed)" if offset < 0 else ""))
        if bt["duration_s"] - max(offset, 0) < plan["totalDurationInFrames"] / plan.get("fps", 30):
            print("WARNING: the music will end before the video does; pick another track/offset or loop it")
    grid = np.array(bt[a.grid]) - offset          # beat times in VIDEO seconds
    grid = grid[grid >= 0]
    before, after, moved = [], [], 0
    tol = a.tol_ms / 1000.0
    for key in EVENT_KEYS:
        for o in plan.get(key, []) or []:
            if "atMs" not in o:
                continue
            t = o["atMs"] / 1000.0
            b = nearest(grid, t)
            before.append(abs(b - t) * 1000)
            if tol > 0 and abs(b - t) <= tol:
                o["atMs"] = int(round(b * 1000))
                after.append(0.0)
                moved += 1
            else:
                after.append(abs(b - t) * 1000)
    if before:
        print(f"{len(before)} events: mean distance to nearest {a.grid[:-1]} {np.mean(before):.0f} ms -> {np.mean(after):.0f} ms "
              f"({moved} snapped within +-{a.tol_ms:.0f} ms, {len(before)-moved} left as is)")
    json.dump(plan, open(a.out or a.plan, "w"), indent=1)


if __name__ == "__main__":
    main()
