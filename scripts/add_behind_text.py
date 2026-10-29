#!/usr/bin/env python3
"""
Add a "text behind the person" headline to an EditPlan, with the position computed from the presenter's measured
head position (zones.json from vision_analyze.py), and copy only the needed matte frames into remotion/public.

  python3 add_behind_text.py --plan job.json --zones zones.json --matte-dir MATTE_DIR --job SLUG \
      --text "DEPRESSION" --at-ms 600 --dur-ms 2600 [--size auto|N] [--color "#FFD84A"] [--out job.json]

What it checks / decides:
  * which source clip(s) the window covers and that no b-roll overlaps it
  * head top (median over the window): the text is centered so the head overlaps its LOWER ~45 %
  * refuses windows where the head touches the top edge (no room to go behind), the person is missing, or the
    framing changes a lot (a cut inside the window is fine, but each segment is checked)
  * auto size so the widest line fits 92 % of the frame width
Matte frames are copied to remotion/public/jobs/<SLUG>/matte_<n>/ (a window-specific folder) so the public dir stays small.
Hard-cut styles only (transition "none").
"""
import argparse, json, os, shutil
import numpy as np
from zones_util import load_zones, clip_map, to_source, frames_between

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(SKILL_DIR, "remotion", "public")
W, H = 1080, 1920


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--zones", required=True)
    ap.add_argument("--matte-dir", required=True, help="folder with m_000001.png... (from vision_analyze.py: OUT/matte)")
    ap.add_argument("--job", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--at-ms", type=int, required=True)
    ap.add_argument("--dur-ms", type=int, required=True)
    ap.add_argument("--size", default="auto")
    ap.add_argument("--color", default="#FFFFFF")
    ap.add_argument("--anim", default="rise", choices=["rise", "scale", "none"])
    ap.add_argument("--head-overlap", type=float, default=None, help="fraction of the text height hidden behind the head (auto: 0.45 for wide text, less for short words)")
    ap.add_argument("--out")
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    z = load_zones(a.zones)
    clips = clip_map(plan)
    t0, t1 = a.at_ms / 1000, (a.at_ms + a.dur_ms) / 1000
    for b in plan.get("broll", []):
        if b["atMs"] / 1000 < t1 and (b["atMs"] + b["durationMs"]) / 1000 > t0:
            raise SystemExit(f"b-roll at {b['atMs']/1000:.1f}s overlaps the window: the presenter is not on screen there")
    tops, need = [], set()
    for t in np.linspace(t0, t1 - 0.05, 8):
        src, clip = to_source(clips, t)
        if src is None:
            raise SystemExit("window runs past the end of the clips")
        fr = frames_between(z, src - 0.17, src + 0.17)
        fr = [f for f in fr if f.get("person")]
        if not fr:
            raise SystemExit(f"no person detected at {t:.2f}s")
        p = fr[len(fr) // 2]["person"]
        z_ = clip.get("zoom", 1) or 1
        oy = 0.2 if clip.get("zoomOrigin") == "top" else 0.5
        top = oy + (p[1] - oy) * z_
        tops.append(top * H)
    top_px = float(np.median(tops))
    if top_px < 0.045 * H:
        raise SystemExit(f"head touches the top edge here (head top at {top_px:.0f}px): no room to put text behind the head. Pick a window with a wider shot.")
    if max(tops) - min(tops) > 0.12 * H:
        print(f"WARNING: the head moves a lot in this window ({min(tops):.0f}-{max(tops):.0f}px); the text may feel loose")
    lines = a.text.upper().split("\n")
    longest = max(len(l) for l in lines)
    fit = int(0.92 * W / (0.47 * longest))
    natural_w = 0.47 * longest * min(fit, 420) / W if a.size == "auto" else 0
    if a.head_overlap is None:
        # a short word is mostly covered by a head; a phrase that spans the frame is only covered in the middle
        a.head_overlap = 0.45 if longest >= 9 else (0.3 if longest >= 6 else 0.2)
        if longest < 6:
            print(f"WARNING: '{a.text}' is short ({longest} chars): the head will hide much of it. Prefer a phrase of 9+ characters.")
    # the text must fit ABOVE the head apex plus the overlap, otherwise it would be pushed down and the head would hide most of it
    max_h = (top_px - 30) / (1 - a.head_overlap)
    room = int(max_h / (0.92 * len(lines)))
    size = min(fit, 420, room) if a.size == "auto" else int(a.size)
    if a.size == "auto" and size < 130:
        raise SystemExit(f"only {room}px of headroom above the head -> text would be {size}px (too small to matter). Use a wider shot or skip.")
    line_h = 0.92 * size
    h_text = line_h * len(lines)
    cy = top_px - h_text * (0.5 - a.head_overlap)   # the bottom `head_overlap` of the text sits below the head apex
    cy = max(cy, h_text / 2 + 30)
    # copy only the matte frames for this window (source frame index = (t - firstT) * fps + 1)
    first_src, _ = to_source(clips, t0)
    last_src, _ = to_source(clips, t1 - 0.02)
    f0 = max(1, int((first_src - z["firstT"]) * z["fps"]))
    f1 = int((last_src - z["firstT"]) * z["fps"]) + 3
    # window may span several clips with different source ranges -> copy the covering span per clip segment
    spans = []
    for ca, cb, c in clips:
        lo, hi = max(ca, t0), min(cb, t1)
        if hi > lo:
            s_lo = c["startFromSeconds"] + (lo - ca)
            s_hi = c["startFromSeconds"] + (hi - ca)
            spans.append((int((s_lo - z["firstT"]) * z["fps"]), int((s_hi - z["firstT"]) * z["fps"]) + 3))
    rel = f"jobs/{a.job}/matte"
    dst = os.path.join(PUBLIC, rel)
    os.makedirs(dst, exist_ok=True)
    n = 0
    for lo, hi in spans:
        for i in range(max(1, lo), min(z["frameCount"], hi) + 1):
            src = os.path.join(a.matte_dir, f"m_{i:06d}.png")
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(dst, f"m_{i:06d}.png"))
                n += 1
    item = {"text": a.text.upper(), "atMs": a.at_ms, "durationMs": a.dur_ms,
            "matte": {"dir": rel, "fps": z["fps"], "firstT": z["firstT"]},
            "y": round(cy), "size": size, "color": a.color, "anim": a.anim}
    plan.setdefault("behindText", []).append(item)
    json.dump(plan, open(a.out or a.plan, "w"), indent=1)
    print(f"behindText '{a.text}' {t0:.1f}-{t1:.1f}s: head top {top_px:.0f}px -> text center y={cy:.0f}px, size {size}px; copied {n} matte frames to {rel}")


if __name__ == "__main__":
    main()
