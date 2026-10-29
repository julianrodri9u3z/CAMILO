#!/usr/bin/env python3
"""
Measure the main footage and each b-roll insert (brightness, contrast, saturation) with ffmpeg
and write a gentle per-insert `grade` so inserts sit in the same look as the main clip --
the fix for stock/TikTok inserts that look "pasted in".

Corrections are CLAMPED (brightness 0.9-1.12, saturation 0.88-1.12; contrast is not touched):
this nudges, it never re-colors. Skips images (nothing to measure fast) unless --images.

Usage:
  python3 match_broll_grade.py --plan job.json [--out job.json] [--public DIR]
"""
import argparse, json, os, re, subprocess

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(SKILL_DIR, "remotion", "public")


def stats(path, ss=0.0, dur=3.0):
    """Return (mean luma 0-255, luma std-ish via YHIGH-YLOW span, mean saturation) for a window."""
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(dur), "-i", path, "-vf", "fps=4,scale=270:-2,signalstats,metadata=print:file=-",
           "-an", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    txt = r.stdout + r.stderr
    def avg(key):
        v = [float(x) for x in re.findall(rf"lavfi\.signalstats\.{key}=([0-9.]+)", txt)]
        return sum(v) / len(v) if v else None
    return avg("YAVG"), (avg("YHIGH") or 0) - (avg("YLOW") or 0), avg("SATAVG")


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out")
    ap.add_argument("--public", default=PUBLIC)
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    # reference look = main footage, sampled across its clips
    refs = []
    for c in plan["clips"][:: max(1, len(plan["clips"]) // 6)]:
        y, span, sat = stats(os.path.join(a.public, c["src"]), c["startFromSeconds"], min(3.0, c["endAtSeconds"] - c["startFromSeconds"]))
        if y is not None:
            refs.append((y, span, sat))
    if not refs:
        print("could not measure main footage"); return
    ry = sum(r[0] for r in refs) / len(refs)
    rs = sum(r[1] for r in refs) / len(refs)
    rsat = sum(r[2] for r in refs) / len(refs)
    print(f"main footage: luma {ry:.0f}, span {rs:.0f}, sat {rsat:.0f}")
    for b in plan.get("broll", []):
        if re.search(r"\.(png|jpe?g|webp)$", b["src"], re.I):
            continue
        y, span, sat = stats(os.path.join(a.public, b["src"]), 0, min(3.0, b["durationMs"] / 1000))
        if y is None:
            continue
        # Brightness + saturation only. Matching contrast crushed dark/moody inserts (tested: a dim
        # gym shot came out darker and muddier), so the contrast span is measured but not applied.
        g = {
            "brightness": round(clamp(ry / max(y, 1), 0.9, 1.12), 3),
            "saturation": round(clamp(rsat / max(sat, 1), 0.88, 1.12), 3),
        }
        b["grade"] = g
        print(f"  {b['src']}: luma {y:.0f}, span {span:.0f}, sat {sat:.0f} -> {g}")
    json.dump(plan, open(a.out or a.plan, "w"), indent=1)


if __name__ == "__main__":
    main()
