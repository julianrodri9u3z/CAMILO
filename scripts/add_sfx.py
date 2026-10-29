#!/usr/bin/env python3
"""
Auto-place sound design on an EditPlan: every visual event that has an overlay/insert gets a
matching quiet sound (whoosh into a b-roll, pop on a keyword, hit on a stat, ding on a
guarantee/CTA...), the way a human editor "scores" the graphics. Writes plan["sfx"].

Follows the editing rules in references/reglas-de-edicion-antonio.md (clase "Volumen de la musica y
sound effect"):
  * 70/30: the voice sits around 0 and the SFX between -20 and -30 dB under it (never closer than -12).
    Each hit is leveled from MEASURED peaks (voice clip + sfx file), not from a fixed volume.
  * Never the same sound twice in a short span: a repeat is swapped for another sound of the same
    family. Deliberate sequences (price/proof stacks counting up) may repeat.
  * Money words (dinero, vender, compra, ganar, euros...) get the "cachin" (sfx/cash.wav).
  * Highlighted caption words (emphasis: true) get a pop/ding, alternating.

Usage:
  python3 add_sfx.py --plan job.json [--out job.json] [--intensity low|medium|high] [--db-under 25]
Requires the library from make_sfx.py in remotion/public/sfx/ (run it once).

intensity: low    -> b-roll whooshes + stats/price/CTA/money only (calm, emotional, documentary)
           medium -> + titles, callouts, lower thirds, proof stacks, highlighted words (default)
           high   -> + hard-cut swishes on punch-in cuts and out-whooshes (energetic UGC/VSL)
"""
import argparse, json, os, re, shutil, subprocess, unicodedata

PRIORITY = {"hit_low": 5, "cash": 4, "ding": 4, "whoosh_soft": 3, "whoosh_fast": 3, "riser": 3, "pop": 2, "tick": 1, "click_soft": 1}
MIN_GAP_MS = {"low": 900, "medium": 600, "high": 380}
MAX_PER_10S = {"low": 3, "medium": 5, "high": 8}
# Same sound again within this window sounds monotonous -> swap for another of its family.
REPEAT_WINDOW_MS = 3000
FAMILY = {
    "whoosh_soft": ["whoosh_fast"], "whoosh_fast": ["whoosh_soft"],
    "pop": ["click_soft", "tick"], "click_soft": ["pop", "tick"], "tick": ["click_soft", "pop"],
    "ding": ["pop", "click_soft"], "cash": ["ding"],  # cash only ever lands on money words
    "hit_low": ["whoosh_soft"], "riser": ["whoosh_soft"],
}
MONEY = re.compile(r"^(dinero|plata|pesos?|dolares?|euros?|usd|cash|vend\w*|compr\w*|gan\w*|pag\w*|factur\w*|ingresos?|"
                   r"millon\w*|ventas?|precio|cobr\w*|rentab\w*|profit|ahorr\w*)$|^\$|\d+\s*(k|mil|€|\$)$")
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(SKILL_DIR, "remotion", "public")
# synthetic sound -> role in the user's own library (scripts/sfx_library.py)
ROLE = {"whoosh_soft": "whoosh", "whoosh_fast": "whoosh", "pop": "pop", "click_soft": "click", "tick": "tick",
        "hit_low": "hit", "riser": "riser", "ding": "ding", "cash": "money"}


def peak_db(path):
    """max_volume (dBFS) of a media file via ffmpeg volumedetect, or None."""
    if not (path and os.path.isfile(path) and shutil.which("ffmpeg")):
        return None
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", r.stderr)
    return float(m.group(1)) if m else None


def plain(word):
    w = unicodedata.normalize("NFKD", word.lower())
    return "".join(c for c in w if not unicodedata.combining(c)).strip(".,;:!?¡¿\"'()")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out")
    ap.add_argument("--intensity", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--keep-existing", action="store_true", help="append to plan['sfx'] instead of replacing it")
    ap.add_argument("--db-under", type=float, default=25.0,
                    help="how many dB the SFX peaks sit under the voice peak (regla 70/30: 20-30, never under 12)")
    ap.add_argument("--synthetic", action="store_true",
                    help="use only the generated sounds of make_sfx.py, not the user's library (sfx_library.py)")
    a = ap.parse_args()
    if not 20 <= a.db_under <= 30:
        print(f"WARNING --db-under {a.db_under}: la regla es que los efectos queden entre -20 y -30 dB bajo la voz")
    plan = json.load(open(a.plan, encoding="utf-8"))
    lvl = {"low": 0, "medium": 1, "high": 2}[a.intensity]
    ev = []  # (atMs, sound, weight, may_repeat)

    def add(ms, sound, w=1.0, seq=False):
        ev.append((max(0, int(ms)), sound, w, seq))

    for b in plan.get("broll", []) or []:
        add(b["atMs"] - 120, "whoosh_soft")
        if lvl >= 2:
            add(b["atMs"] + b["durationMs"] - 150, "whoosh_fast", 0.6)
    for s in plan.get("statCallouts", []) or []:
        add(s["atMs"], "hit_low")
        if lvl >= 1:
            add(s["atMs"] + 40, "pop", 0.7)
    for p in plan.get("priceStacks", []) or []:
        step = p.get("staggerMs") or 350
        n = len(p.get("lines", []))
        for i in range(n):
            add(p["atMs"] + i * step, "tick", 0.9, seq=True)
        add(p["atMs"] + n * step + 200, "cash")
    for g in plan.get("guaranteeSeals", []) or []:
        add(g["atMs"], "ding")
    for c in plan.get("ctaButtons", []) or []:
        add(c["atMs"], "pop")
        if lvl >= 2:
            add(c["atMs"] + 120, "ding", 0.7)
    # money words -> cachin (any intensity: it's what the words say, not decoration)
    for w in plan.get("captions", []) or []:
        if MONEY.search(plain(w["text"])):
            add(w["startMs"], "cash", 0.9)
    if lvl >= 1:
        for c in plan.get("titleCards", []) or []:
            add(c["atMs"] - 80, "whoosh_soft")
            add(c["atMs"], "pop", 0.8)
        t = plan.get("title")
        if t and t.get("startMs") is not None:
            add(t["startMs"], "pop", 0.8)
        for k in plan.get("keywordCallouts", []) or []:
            add(k["atMs"], "pop")
        for l in plan.get("lowerThirds", []) or []:
            add(l["atMs"], "click_soft")
        for pr in plan.get("proofStacks", []) or []:
            step = pr.get("staggerMs") or 250
            add(pr["atMs"] - 60, "whoosh_fast")
            for i in range(len(pr.get("images", []))):
                add(pr["atMs"] + i * step, "tick", 0.9, seq=True)
        for b in plan.get("badges", []) or []:
            add(b["atMs"], "pop", 0.8)
        for st in plan.get("stickers", []) or []:
            add(st["atMs"], "pop", 0.8)
        for bt in plan.get("behindText", []) or []:
            add(bt["atMs"] - 120, "whoosh_soft")
            add(bt["atMs"] + 60, "pop", 0.8)
        # highlighted words ("palabras de peso") get a sound too, alternating pop / ding
        for i, w in enumerate([w for w in plan.get("captions", []) or [] if w.get("emphasis")]):
            add(w["startMs"], "pop" if i % 2 == 0 else "ding", 0.8)
    if lvl >= 2:
        fps = plan.get("fps", 30)
        t = 0.0
        for i, c in enumerate(plan.get("clips", [])):
            if i > 0 and c.get("zoom", 1) != plan["clips"][i - 1].get("zoom", 1):
                add(t * 1000 - 40, "whoosh_fast", 0.6)
            t += c["endAtSeconds"] - c["startFromSeconds"]

    # thin out: highest priority first, respect min gap and a per-10s density cap
    ev.sort(key=lambda e: (-PRIORITY[e[1]], e[0]))
    kept = []
    for e in ev:
        if any(abs(e[0] - k[0]) < MIN_GAP_MS[a.intensity] for k in kept if not (e[3] and k[3])):
            continue
        window = [k for k in kept if abs(k[0] - e[0]) < 5000]
        if len(window) >= MAX_PER_10S[a.intensity]:
            continue
        kept.append(e)
    kept.sort()

    # no monotony: swap a sound that already played within REPEAT_WINDOW_MS (sequences excepted)
    varied, swaps = [], 0
    for ms, s, w, seq in kept:
        recent = {k[1] for k in varied if ms - k[0] < REPEAT_WINDOW_MS and not (seq and k[3])}
        if s in recent:
            alt = next((f for f in FAMILY.get(s, []) if f not in recent), None)
            if alt:
                s, swaps = alt, swaps + 1
        varied.append((ms, s, w, seq))

    # level every hit from measured peaks: sfx peak = voice peak - db_under
    clips = plan.get("clips") or []
    voice = peak_db(os.path.join(PUBLIC, clips[0]["src"])) if clips else None
    if voice is None:
        voice = -3.0
        print("WARNING no pude medir la voz (clips[0].src); asumo pico de voz -3 dBFS")
    picker = None
    if not a.synthetic:
        import sfx_library
        picker = sfx_library.Picker(seed=len(plan.get("captions") or []))
        if not picker.by_role:
            picker = None
            print("(sin catalogo de tu libreria: uso los sonidos sinteticos; corre `sfx_library.py index`)")
    cache = {}
    hits = []
    from_lib = 0
    for ms, s, w, _ in varied:
        item = picker.pick(ROLE[s]) if picker and picker.has(ROLE[s]) else None
        if item:
            src, sp = sfx_library.Picker.stage(item, ROLE[s])
            from_lib += 1
        else:
            src = f"sfx/{s}.wav"
            if s not in cache:
                cache[s] = peak_db(os.path.join(PUBLIC, src))
            sp = cache[s]
        sp = sp if sp is not None else -4.0
        vol = 10 ** ((voice - a.db_under - sp) / 20) * w
        hits.append({"src": src, "atMs": ms, "volume": round(min(1.0, vol), 4)})
    if a.keep_existing:
        hits = (plan.get("sfx") or []) + hits
    plan["sfx"] = hits
    out = a.out or a.plan
    json.dump(plan, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    from collections import Counter
    print(f"{len(hits)} sound hits ({a.intensity}, -{a.db_under:g} dB bajo la voz de {voice:.1f} dBFS, "
          f"{swaps} cambiados por repeticion, {from_lib} de tu libreria):",
          dict(Counter(ROLE.get(os.path.basename(h['src'])[:-4], os.path.basename(h['src']).split('_')[0]) for h in hits)))
    missing = sorted({h["src"] for h in hits if not os.path.isfile(os.path.join(PUBLIC, h["src"]))})
    if missing:
        print("WARNING missing sound files (run make_sfx.py):", missing)


if __name__ == "__main__":
    main()
