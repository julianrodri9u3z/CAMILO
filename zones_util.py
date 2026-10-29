"""Shared helpers for scripts that read zones.json (from vision_analyze.py) and map TIMELINE time -> SOURCE time."""
import json


def load_zones(path):
    z = json.load(open(path))
    z["frames"].sort(key=lambda f: f["t"])
    return z


def clip_map(plan):
    """List of (timeline_start_s, timeline_end_s, clip) for hard-cut timelines (cumulative clip durations)."""
    out, t = [], 0.0
    for c in plan["clips"]:
        d = c["endAtSeconds"] - c["startFromSeconds"]
        out.append((t, t + d, c))
        t += d
    return out


def to_source(clips, t):
    """timeline seconds -> (source seconds, clip) or (None, None)."""
    for a, b, c in clips:
        if a <= t < b:
            return c["startFromSeconds"] + (t - a), c
    return None, None


def zoom_rect(r, clip):
    """Apply the clip's static zoom (about the zoom origin) to a normalized [x,y,w,h] rect."""
    z = clip.get("zoom", 1) or 1
    if z == 1:
        return r
    ox, oy = 0.5, (0.2 if clip.get("zoomOrigin") == "top" else 0.5)
    x, y, w, h = r
    return [ox + (x - ox) * z, oy + (y - oy) * z, w * z, h * z]


def frames_between(z, t0, t1):
    return [f for f in z["frames"] if t0 <= f["t"] <= t1]


def overlap_area(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    w = min(ax + aw, bx + bw) - max(ax, bx)
    h = min(ay + ah, by + bh) - max(ay, by)
    return max(0, w) * max(0, h)
