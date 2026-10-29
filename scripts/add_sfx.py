#!/usr/bin/env python3
"""
Auto-place sound design on an EditPlan: every visual event that has an overlay/insert gets a
matching quiet sound (whoosh into a b-roll, pop on a keyword, hit on a stat, ding on a
guarantee/CTA...), the way a human editor "scores" the graphics. Writes plan["sfx"].

Rules are conservative on purpose: SFX should be FELT, not heard. Low volumes, a minimum gap
between hits, and a density cap so a calm/emotional piece doesn't turn into a game show.

Usage:
  python3 add_sfx.py --plan job.json [--out job.json] [--intensity low|medium|high]
Requires the library from make_sfx.py in remotion/public/sfx/ (run it once).

intensity: low    -> b-roll whooshes + stats/price/CTA only (calm, emotional, documentary)
           medium -> + titles, callouts, lower thirds, proof stacks (default)
           high   -> + hard-cut swishes on punch-in cuts and out-whooshes (energetic UGC/VSL)
"""
import argparse, json, os

PRIORITY = {"hit_low": 5, "ding": 4, "whoosh_soft": 3, "whoosh_fast": 3, "riser": 3, "pop": 2, "tick": 1, "click_soft": 1}
MIN_GAP_MS = {"low": 900, "medium": 600, "high": 380}
MAX_PER_10S = {"low": 3, "medium": 5, "high": 8}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out")
    ap.add_argument("--intensity", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--keep-existing", action="store_true", help="append to plan['sfx'] instead of replacing it")
    ap.add_argument("--gain", type=float, default=1.5, help="global multiplier on every hit volume (measured: 1.0 left whooshes 9-14 dB under the voice = inaudible; 1.5 sits ~4-8 dB under)")
    a = ap.parse_args()
    plan = json.load(open(a.plan))
    lvl = {"low": 0, "medium": 1, "high": 2}[a.intensity]
    ev = []  # (atMs, sound, volume)

    def add(ms, sound, vol):
        ev.append((max(0, int(ms)), sound, vol))

    for b in plan.get("broll", []) or []:
        add(b["atMs"] - 120, "whoosh_soft", 0.30)
        if lvl >= 2:
            add(b["atMs"] + b["durationMs"] - 150, "whoosh_fast", 0.18)
    for s in plan.get("statCallouts", []) or []:
        add(s["atMs"], "hit_low", 0.40)
        if lvl >= 1:
            add(s["atMs"] + 40, "pop", 0.25)
    for p in plan.get("priceStacks", []) or []:
        step = p.get("staggerMs") or 350
        n = len(p.get("lines", []))
        for i in range(n):
            add(p["atMs"] + i * step, "tick", 0.28)
        add(p["atMs"] + n * step + 200, "ding", 0.30)
    for g in plan.get("guaranteeSeals", []) or []:
        add(g["atMs"], "ding", 0.30)
    for c in plan.get("ctaButtons", []) or []:
        add(c["atMs"], "pop", 0.35)
        if lvl >= 2:
            add(c["atMs"] + 120, "ding", 0.20)
    if lvl >= 1:
        for c in plan.get("titleCards", []) or []:
            add(c["atMs"] - 80, "whoosh_soft", 0.30)
            add(c["atMs"], "pop", 0.25)
        t = plan.get("title")
        if t and t.get("startMs") is not None:
            add(t["startMs"], "pop", 0.22)
        for k in plan.get("keywordCallouts", []) or []:
            add(k["atMs"], "pop", 0.28)
        for l in plan.get("lowerThirds", []) or []:
            add(l["atMs"], "click_soft", 0.25)
        for pr in plan.get("proofStacks", []) or []:
            step = pr.get("staggerMs") or 250
            add(pr["atMs"] - 60, "whoosh_fast", 0.25)
            for i in range(len(pr.get("images", []))):
                add(pr["atMs"] + i * step, "tick", 0.25)
        for b in plan.get("badges", []) or []:
            add(b["atMs"], "pop", 0.22)
        for st in plan.get("stickers", []) or []:
            add(st["atMs"], "pop", 0.2)
        for bt in plan.get("behindText", []) or []:
            add(bt["atMs"] - 120, "whoosh_soft", 0.30)
            add(bt["atMs"] + 60, "pop", 0.25)
    if lvl >= 2:
        fps = plan.get("fps", 30)
        t = 0.0
        for i, c in enumerate(plan.get("clips", [])):
            if i > 0 and c.get("zoom", 1) != plan["clips"][i - 1].get("zoom", 1):
                add(t * 1000 - 40, "whoosh_fast", 0.14)
            t += c["endAtSeconds"] - c["startFromSeconds"]

    # thin out: highest priority first, respect min gap and a per-10s density cap
    ev.sort(key=lambda e: (-PRIORITY[e[1]], e[0]))
    kept = []
    for e in ev:
        if any(abs(e[0] - k[0]) < MIN_GAP_MS[a.intensity] for k in kept):
            continue
        window = [k for k in kept if abs(k[0] - e[0]) < 5000]
        if len(window) >= MAX_PER_10S[a.intensity]:
            continue
        kept.append(e)
    kept.sort()
    hits = [{"src": f"sfx/{s}.wav", "atMs": ms, "volume": round(min(1.0, v * a.gain), 3)} for ms, s, v in kept]
    if a.keep_existing:
        hits = (plan.get("sfx") or []) + hits
    plan["sfx"] = hits
    out = a.out or a.plan
    json.dump(plan, open(out, "w"), indent=1)
    from collections import Counter
    print(f"{len(hits)} sound hits ({a.intensity}):", dict(Counter(h['src'][4:-4] for h in hits)))
    missing = [h["src"] for h in hits if not os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "remotion", "public", h["src"]))]
    if missing:
        print("WARNING missing sound files (run make_sfx.py):", sorted(set(missing)))


if __name__ == "__main__":
    main()
