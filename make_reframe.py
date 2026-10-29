#!/usr/bin/env python3
"""
Smart reframing: turn the subject track from vision_analyze.py (zones.json) into a smooth VIRTUAL CAMERA for a wide
source shown in a vertical frame (EditPlan.reframe).

Behaviour of a good camera operator, not a jittery tracker:
  * follows the FACE (largest), falls back to the person's upper body;
  * a dead zone: it only moves when the subject leaves a small central zone, then eases toward them
    (exponential smoothing, ~0.7 s) -- no constant micro-motion;
  * SOURCE CUTS reset it instantly (pass --cuts), so a change of camera angle is a hard cut, not a pan.

Usage:
  python3 make_reframe.py --zones zones.json --out reframe.json [--cuts 1.47,3.37,4.97]
                          [--tau 0.7] [--deadzone 0.03] [--target-y 0.4]
reframe.json is {srcW, srcH, targetX, targetY, points:[{t,x,y,z}]}: merge it into the plan as plan["reframe"].
"""
import argparse, json, math


def focus(f):
    faces = f.get("faces") or []
    if faces:
        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
        return x + w / 2, y + h / 2, True
    p = f.get("person")
    if p:
        return p[0] + p[2] / 2, p[1] + 0.2 * p[3], False
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cuts", default="", help="comma separated SOURCE seconds where the camera angle changes")
    ap.add_argument("--tau", type=float, default=0.7)
    ap.add_argument("--deadzone", type=float, default=0.03)
    ap.add_argument("--target-y", type=float, default=0.4)
    a = ap.parse_args()
    z = json.load(open(a.zones))
    cuts = sorted(float(c) for c in a.cuts.split(",") if c.strip())
    frames = sorted(z["frames"], key=lambda f: f["t"])
    pts, cam, prev_t, last_focus = [], None, None, None
    for f in frames:
        fo = focus(f)
        if fo is None:
            fo = last_focus
        if fo is None:
            continue
        last_focus = fo
        fx, fy, _ = fo
        t = f["t"]
        cut = prev_t is not None and any(prev_t < c <= t for c in cuts)
        if cam is None or cut:
            cam = [fx, fy]
        else:
            dt = max(1e-3, t - prev_t)
            al = 1 - math.exp(-dt / a.tau)
            for i, v in enumerate((fx, fy)):
                err = v - cam[i]
                if abs(err) < a.deadzone:
                    err = 0
                else:
                    err -= math.copysign(a.deadzone * 0.5, err)   # ease to the edge of the dead zone, not the exact center
                cam[i] += al * err
        pts.append({"t": round(t, 3), "x": round(cam[0], 4), "y": round(cam[1], 4), "z": 1})
        prev_t = t
    out = {"srcW": z["w"], "srcH": z["h"], "targetX": 0.5, "targetY": a.target_y, "points": pts}
    json.dump(out, open(a.out, "w"))
    xs = [p["x"] for p in pts]
    print(f"{len(pts)} camera points, x range {min(xs):.2f}-{max(xs):.2f}; cuts at {cuts}")


if __name__ == "__main__":
    main()
