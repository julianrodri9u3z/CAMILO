#!/usr/bin/env python3
"""
Build a MUSIC-DRIVEN, high-energy ("dopamine") EditPlan from one continuous shot + the music's beat grid.

Everything is derived from numbers (beat_grid.py), nothing "felt":
  * Multi-camera from one camera: the shot is cut at beats into segments with different punch-in levels
    (1.0 / 1.15 / 1.28 ...), so it reads as several cameras. The source time is NEVER skipped (the music is the
    source's own audio and stays continuous).
  * Rhythm adapts to energy: calm intro -> long segments (2 bars); the build -> slow push-in; the DROP ->
    flash + shake + hit + riser; after the drop -> a cut every bar, every 2 beats in the hottest stretches.
  * Beat pulses (zoom) on every beat, stronger on downbeats, only when the music is energetic.
  * Sound: riser into the drop, impact on it, soft whooshes on some bar cuts.
  * No invented text: this builder adds NO captions/titles (a music-only clip has nothing to quote).

Usage:
  python3 make_beat_edit.py --src jobs/<slug>/raw.mp4 --beats beats.json --reframe reframe.json \
      --start 0 --end 70.7 [--cuts 1.47,3.37,4.97] [--max-zoom 1.3] [--out job.json]
(times in SOURCE seconds; the timeline starts at --start.)
"""
import argparse, json

ZOOMS = [1.0, 1.15, 1.0, 1.28, 1.08, 1.22]


def nearest(arr, t):
    return min(arr, key=lambda x: abs(x - t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--beats", required=True)
    ap.add_argument("--reframe", required=True)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--cuts", default="", help="source camera-angle cuts (seconds): kept as boundaries, zoom 1.0")
    ap.add_argument("--max-zoom", type=float, default=1.3)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--drop", type=float, help="drop time in source seconds (default: strongest drop)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bt = json.load(open(a.beats))
    beats = [b for b in bt["beats"] if a.start <= b <= a.end]
    downs = set(round(b, 2) for b in bt["downbeats"])
    drops = [d["t"] for d in bt["drops"] if a.start < d["t"] < a.end and d["ratio"] >= 1.8]
    drop = a.drop or (max((d for d in bt["drops"] if a.start < d["t"] < a.end), key=lambda d: d["ratio"])["t"] if drops else None)
    src_cuts = sorted(float(c) for c in a.cuts.split(",") if c.strip())
    energy = bt["energy_5s"]

    def en(t):
        i = min(len(energy) - 1, int(t // 5))
        return energy[i]

    # --- segment boundaries on beats -------------------------------------------------
    bounds = [a.start]
    t = a.start
    bar = 4
    idx = 0
    while True:
        later = [b for b in beats if b > t + 0.2]
        if not later:
            break
        e = en(t)
        post_drop = drop is not None and t >= drop - 0.05
        if drop is not None and t < drop - 0.3 and any(b >= drop - 0.1 for b in later):
            # make sure a boundary lands exactly on the drop
            nb_before = [b for b in later if b < drop - 0.1]
            step = 8 if e < 0.05 else 4
            nxt = later[min(step, len(later)) - 1]
            if nxt > drop - 0.1:
                nxt = drop   # the cut lands exactly on the measured bass onset
        elif post_drop and e > 0.15:
            step = 2
            nxt = later[min(step, len(later)) - 1]
        elif post_drop:
            step = 4
            nxt = later[min(step, len(later)) - 1]
        else:
            step = 8 if e < 0.05 else 4
            nxt = later[min(step, len(later)) - 1]
        # snap onto the source's own camera cuts inside the span
        for c in src_cuts:
            if t + 0.1 < c < nxt - 0.1:
                nxt = c
                break
        bounds.append(round(nxt, 3))
        t = nxt
        if t >= a.end - 0.05:
            break
    if bounds[-1] < a.end:
        bounds.append(a.end)
    else:
        bounds[-1] = a.end

    # --- clips with a rotating zoom, push-in during the build ------------------------
    clips = []
    zi = 0
    for s, e in zip(bounds[:-1], bounds[1:]):
        if e - s < 0.15:
            continue
        if any(abs(s - c) < 0.05 or s < min(src_cuts + [1e9]) for c in src_cuts) and s < (src_cuts[-1] if src_cuts else 0) + 0.01:
            z = 1.0   # intro: the source's own cuts carry the rhythm
        elif drop is not None and s < drop - 0.1:
            prog = (s - a.start) / max(1e-6, drop - a.start)
            z = 1.0 + 0.16 * prog          # slow push-in through the build
        elif drop is not None and abs(s - drop) < 0.2:
            z = 1.3                         # the drop lands on a tight shot
        else:
            z = ZOOMS[zi % len(ZOOMS)]
            zi += 1
        z = min(round(z, 3), a.max_zoom)
        clips.append({"src": a.src, "startFromSeconds": round(s, 3), "endAtSeconds": round(e, 3), "zoom": z})

    total_frames = int(round((a.end - a.start) * a.fps))
    reframe = json.load(open(a.reframe))

    # --- pulses ----------------------------------------------------------------------
    pulses = []
    for b in beats:
        ms = int(round((b - a.start) * 1000))
        e = en(b)
        if e < 0.05:
            continue
        down = round(b, 2) in downs or any(abs(b - d) < 0.04 for d in bt["downbeats"])
        pulses.append({"atMs": ms, "kind": "zoom", "strength": 0.7 if down else 0.35, "decayMs": 240})
    drop_times = [d["t"] for d in bt["drops"] if a.start < d["t"] < a.end and d["ratio"] >= 1.8]
    sfx = []
    for d in drop_times:
        ms = int(round((d - a.start) * 1000))
        big = d == drop
        pulses.append({"atMs": ms, "kind": "flash", "strength": 1.0 if big else 0.6, "decayMs": 160})
        pulses.append({"atMs": ms, "kind": "shake", "strength": 1.0 if big else 0.6, "decayMs": 300})
        pulses.append({"atMs": ms, "kind": "zoom", "strength": 1.5 if big else 1.0, "decayMs": 300})
        sfx.append({"src": "sfx/hit_low.wav", "atMs": ms, "volume": 0.9 if big else 0.6})
        if big:
            sfx.append({"src": "sfx/riser.wav", "atMs": max(0, ms - 1600), "volume": 0.55})
    # soft whooshes on every other bar cut after the first drop
    k = 0
    for s in bounds[1:-1]:
        if drop is not None and s > drop + 0.5:
            k += 1
            if k % 2 == 0:
                sfx.append({"src": "sfx/whoosh_fast.wav", "atMs": int(round((s - a.start) * 1000)) - 60, "volume": 0.3})
    pulses.sort(key=lambda p: p["atMs"])
    sfx.sort(key=lambda p: p["atMs"])

    plan = {
        "fps": a.fps, "width": a.width, "height": a.height, "clips": clips, "captions": [], "broll": [],
        "totalDurationInFrames": total_frames, "reframe": reframe, "pulses": pulses, "sfx": sfx,
        "grade": {"contrast": 1.1, "saturation": 1.12, "temperature": 0.1, "fade": 0.02, "grain": 0.16},
        "vignette": {"intensity": 0.35},
    }
    json.dump(plan, open(a.out, "w"), indent=1)
    zs = [c["zoom"] for c in clips]
    print(f"{len(clips)} clips ({bounds[0]:.1f}-{bounds[-1]:.1f}s), zoom {min(zs)}-{max(zs)}, {len(pulses)} pulses, {len(sfx)} sounds, drop at {drop}")


if __name__ == "__main__":
    main()
