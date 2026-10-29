#!/usr/bin/env python3
"""
Subtitles that get out of the way: for every caption phrase, measure how much the default placement overlaps
the presenter's FACE and HANDS (Apple Vision boxes from vision_analyze.py) and, if it does, move that phrase to
the best of: left / center / right x a few lift heights. Writes `anchor` / `liftPx` on the FIRST word of each
phrase (the "kinetic" caption variant reads them). Phrases that are already clear are left untouched, so the
look stays consistent and only the problem phrases move.

Phrase grouping mirrors components/Captions.tsx (kinetic): new phrase after a >450 ms gap or 4 words.

Usage:
  python3 dodge_captions.py --plan job.json --zones zones.json [--out job.json] [--bottom-px 300]
Reports how many phrases moved and the overlap before/after (the verification).
"""
import argparse, json
import numpy as np
from zones_util import load_zones, clip_map, to_source, zoom_rect, frames_between, overlap_area

W, H = 1080, 1920
SIZE, SIZE_EMPH = 54, 104
LEFT_MARGIN = 70


def phrases(words, gap=450, max_words=4):
    out, cur = [], []
    for w in words:
        if cur and (w["startMs"] - cur[-1]["endMs"] > gap or len(cur) >= max_words):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def caption_box(ph, anchor, lift, bottom_px):
    longest = max(len(w["text"]) * (SIZE_EMPH if w.get("emphasis") else SIZE) * 0.52 for w in ph)
    height = sum((SIZE_EMPH if w.get("emphasis") else SIZE) * 0.92 for w in ph)
    wn, hn = longest / W, height / H
    bottom = 1 - (bottom_px + lift) / H
    y = bottom - hn
    x = LEFT_MARGIN / W if anchor == "left" else (1 - LEFT_MARGIN / W - wn if anchor == "right" else (1 - wn) / 2)
    return [x, y, wn, hn]


def score(box, faces, hands):
    area = box[2] * box[3]
    s = 0.0
    for f in faces:
        s += 3.0 * overlap_area(box, f) / area
    for h in hands:
        s += 2.0 * overlap_area(box, h) / area
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--zones", required=True)
    ap.add_argument("--out")
    ap.add_argument("--bottom-px", type=float, default=300)
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    z = load_zones(a.zones)
    if (z["w"], z["h"]) != (plan["width"], plan["height"]):
        raise SystemExit(f"zones are for {z['w']}x{z['h']} but the plan is {plan['width']}x{plan['height']}: only identical framing is supported")
    clips = clip_map(plan)
    brolls = [(b["atMs"] / 1000, (b["atMs"] + b["durationMs"]) / 1000) for b in plan.get("broll", [])]
    options = [(an, lift) for lift in (0, 230, 460) for an in ("left", "right", "center")]
    moved, before_tot, after_tot, n_checked = 0, 0.0, 0.0, 0
    for ph in phrases(plan["captions"]):
        t0, t1 = ph[0]["startMs"] / 1000, ph[-1]["endMs"] / 1000 + 0.25
        if any(a_ < t1 and b_ > t0 for a_, b_ in brolls):
            continue  # b-roll on screen: the zones describe the presenter, not what is visible
        samples = []
        for t in np.linspace(t0, t1, 5):
            src, clip = to_source(clips, min(t, clips[-1][1] - 1e-3))
            if src is None:
                continue
            fr = frames_between(z, src - 0.17, src + 0.17)
            if not fr:
                continue
            f = fr[len(fr) // 2]
            samples.append(([zoom_rect(r, clip) for r in f["faces"]], [zoom_rect(r, clip) for r in f["hands"]]))
        if not samples:
            continue
        n_checked += 1

        def total(an, lift):
            box = caption_box(ph, an, lift, a.bottom_px)
            return float(np.mean([score(box, fa, ha) for fa, ha in samples]))

        base = total("left", 0)
        before_tot += base
        if base < 0.04:
            after_tot += base
            continue
        best = min(options, key=lambda o: total(*o) + (0.02 if o[0] != "left" else 0) + 0.03 * (o[1] // 230))
        best_s = total(*best)
        if best_s < base - 0.03:
            ph[0]["anchor"] = best[0]
            if best[1]:
                ph[0]["liftPx"] = best[1]
            moved += 1
            after_tot += best_s
        else:
            after_tot += base
    print(f"{n_checked} phrases checked, {moved} moved. mean face/hand overlap score {before_tot/max(1,n_checked):.3f} -> {after_tot/max(1,n_checked):.3f}")
    json.dump(plan, open(a.out or a.plan, "w"), indent=1)


if __name__ == "__main__":
    main()
