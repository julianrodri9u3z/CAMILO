#!/usr/bin/env python3
"""
The user's own sound-effects library (real, hand-picked packs) -> a catalog that add_sfx.py uses instead of
the synthetic sounds from make_sfx.py.

  python3 sfx_library.py index [--root ~/Documents/SONIDOS-FX]   # measure + classify every file (once, ~2 min)
  python3 sfx_library.py stats                                   # how many sounds per role
  python3 sfx_library.py list --role money                       # what's in a role

The catalog lives in ~/.bcc-toolkit/sfx-catalog.json (next to the keys, survives plugin updates). The library
itself stays outside the repo: the repo is public and these packs are not ours to redistribute.

Roles (what add_sfx.py asks for): whoosh, riser, hit, money, ding, pop, click, tick, typing, camera, glitch,
notification, cheer, sad. Anything else is "foley" (literal b-roll sounds: car, kitchen, water, fire...) or
"meme" (comical / meme packs -- never used automatically: the agency style is elegant, see
references/reglas-de-edicion-antonio.md).
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HOME = os.path.expanduser("~")
CATALOG = os.path.join(HOME, ".bcc-toolkit", "sfx-catalog.json")
DEFAULT_ROOT = os.path.join(HOME, "Documents", "SONIDOS-FX")
AUDIO = (".wav", ".mp3", ".aif", ".aiff", ".ogg", ".m4a", ".aac", ".flac", ".caf")
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(SKILL_DIR, "remotion", "public")

def W(*words):
    """regex matching any of the words as a whole word (filenames use spaces, _ and - as separators)."""
    return r"(?<![a-z])(" + "|".join(words) + r")(?![a-z])"


# Order matters: first match wins. (regex on "folder/filename", lowercase)
RULES = [
    ("meme", r"^(comical|mai sound pack)/|" + W("bruh", "meme", "wtf", "oof", "sheesh", "fart", "among us", "minecraft",
             "roblox", "mario", "spongebob", "illuminati", "lyrics", "club penguin", "wii sports", "kevin macleod",
             "lukrembo", "censor", "wolf whistle", "buzzer wrong", "cat meow", "boing", "kids saying yay",
             "falling whistle", "evil laughter", "zombie", "hannah montana", "nicki", "careless whisper",
             "empire state", "circus", "elevator music", "aww", "hmm")),
    ("money", W("cha_?ching", "ching", "cash", "coins?", "money", "casino", "change drop", "register")),
    ("riser", W("risers?", "fierceriser\\d*", "suspense", "rewind", "dun dun")),
    ("whoosh", W("swoosh(ing)?", "whoosh(ing)?", "swish", "transition")),
    ("hit", W("hits?\\d*", "fiercehit\\d*", "thud\\d*", "slam\\d*", "lockslam\\d*", "impact", "bass drop", "bwong",
              "boom", "punch", "metaldeepthud\\d*", "dullpadhit\\d*")),
    ("ding", W("ding", "pling", "chime", "shop bell", "bell ring", "render complete", "angels")),
    ("typing", W("keyboard\\w*", "typing", "keyboardtyp\\w*")),
    ("camera", W("shutter", "camera", "flashing")),
    ("glitch", W("glitch", "blue screen", "error")),
    ("notification", W("e-?mail", "message", "sentmessage", "notification", "alerts?", "vibrate", "facetime",
                       "phone call", "breaking news")),
    ("tick", W("tick(ing)?", "clock_ticking", "count ?down", "dial clicks", "ratchet")),
    ("click", W("clicks?\\d*", "mouseclicks?\\d*", "button", "switch", "mouse", "unlock", "confirm", "activation")),
    ("pop", W("pop", "bottlepop", "blop", "snap", "bubble", "soda can")),
    ("cheer", W("applause", "cheer(ing)?", "audiencecheer\\w*", "yay", "wow", "gasp")),
    ("sad", W("sad", "ear ringing", "whimper", "whining", "cry")),
]
# Longest usable hit per role (s): staged copies are cut to this. Files whose sound itself is much longer, or that
# contain several separate sounds (a compilation), stay as foley.
MAX_DUR = {"whoosh": 3.0, "riser": 8.0, "hit": 4.0, "money": 3.0, "ding": 4.0, "pop": 1.5, "click": 1.5,
           "tick": 6.0, "typing": 6.0, "camera": 3.0, "glitch": 3.0, "notification": 4.0, "cheer": 8.0, "sad": 8.0}


def classify(rel):
    key = rel.replace("\\", "/").lower()
    for role, rx in RULES:
        if re.search(rx, key):
            return role
    return "foley"


def probe(path):
    """duration, peak dBFS, onset (leading silence), active (s from onset to the final fade under -45 dB),
    gaps (internal silences >= 0.3 s: many = a compilation of separate sounds)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
                        "silencedetect=n=-45dB:d=0.3,volumedetect", "-f", "null", "-"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    e = r.stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e)
    dur = int(dur[1]) * 3600 + int(dur[2]) * 60 + float(dur[3]) if dur else None
    peak = re.search(r"max_volume:\s*(-?[\d.]+) dB", e)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", e)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", e)]
    onset = ends[0] if starts and abs(starts[0]) < 0.01 and ends else 0.0
    tail = starts[-1] if dur and starts and len(starts) > len(ends) else dur  # trailing silence never "ends"
    inner = [s for s in starts if onset + 0.01 < s < (tail or 0) - 0.01] if tail else []
    active = max(0.0, (tail or 0) - onset)
    return dur, float(peak[1]) if peak else None, round(onset, 3), round(active, 3), len(inner)


def cmd_index(a):
    root = os.path.abspath(a.root)
    files = []
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x != "__MACOSX"]
        files += [os.path.join(d, n) for n in names if n.lower().endswith(AUDIO) and not n.startswith("._")]
    print(f"midiendo {len(files)} sonidos en {root} ...", flush=True)

    def one(p):
        rel = os.path.relpath(p, root)
        dur, peak, onset, active, gaps = probe(p)
        role = classify(rel)
        # a one-shot may ring out longer than we use (it gets cut), but not 3x longer, and not be a compilation
        if role not in ("meme", "foley") and (dur is None or active > 3 * MAX_DUR.get(role, 99) or gaps > 2):
            role = "foley"
        return {"path": p, "rel": rel.replace("\\", "/"), "role": role, "dur": dur, "peak": peak, "onset": onset,
                "active": active, "gaps": gaps}

    with ThreadPoolExecutor(max_workers=8) as ex:
        items = [x for x in ex.map(one, files) if x["peak"] is not None and x["peak"] > -60]
    # the same file often sits in several packs: keep one copy, or the rotation would repeat it
    seen, unique = set(), []
    for x in sorted(items, key=lambda x: x["rel"]):
        k = (os.path.splitext(os.path.basename(x["rel"]))[0].lower().replace(" (1)", ""), round(x["dur"] or 0, 1))
        if k not in seen:
            seen.add(k)
            unique.append(x)
    items = unique
    os.makedirs(os.path.dirname(CATALOG), exist_ok=True)
    json.dump({"root": root, "items": items}, open(CATALOG, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"catalogo: {CATALOG}")
    cmd_stats(a)


def load():
    if not os.path.isfile(CATALOG):
        return None
    return json.load(open(CATALOG, encoding="utf-8"))


def cmd_stats(a):
    cat = load()
    if not cat:
        sys.exit("no hay catalogo: corre `sfx_library.py index`")
    c = Counter(i["role"] for i in cat["items"])
    for role, n in sorted(c.items(), key=lambda x: -x[1]):
        print(f"  {role:13} {n}")


def cmd_list(a):
    for i in (load() or {"items": []})["items"]:
        if i["role"] == a.role:
            print(f"  {i['dur']:5.2f}s  {i['peak']:6.1f} dB  {i['rel']}")


class Picker:
    """Rotates through each role's files so the same real sound doesn't come back soon (regla: no repetir)."""

    def __init__(self, seed=0):
        cat = load()
        self.by_role = {}
        for i in (cat or {"items": []})["items"]:
            self.by_role.setdefault(i["role"], []).append(i)
        for r in self.by_role.values():
            r.sort(key=lambda i: hashlib.md5((i["rel"] + str(seed)).encode()).hexdigest())
        self.next = Counter()

    def has(self, role):
        return bool(self.by_role.get(role))

    def pick(self, role):
        items = self.by_role.get(role)
        if not items:
            return None
        i = items[self.next[role] % len(items)]
        self.next[role] += 1
        return i

    @staticmethod
    def stage(item, role):
        """Copy into remotion/public/sfx-lib/ trimmed (leading silence off, capped length, fade out) -> (src, peak)."""
        h = hashlib.md5(item["path"].encode()).hexdigest()[:10]
        rel = f"sfx-lib/{role}_{h}.wav"
        out = os.path.join(PUBLIC, rel)
        if not os.path.isfile(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            dur = min(MAX_DUR.get(role, 4.0), item.get("active") or (item["dur"] or 4.0) - item["onset"])
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(item["onset"]), "-i", item["path"], "-t", f"{dur:.3f}",
                            "-af", f"afade=t=out:st={max(0, dur - 0.15):.3f}:d=0.15", "-ar", "48000", "-ac", "2", out],
                           check=True)
        return rel, item["peak"]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("index")
    p.add_argument("--root", default=DEFAULT_ROOT)
    sub.add_parser("stats")
    p = sub.add_parser("list")
    p.add_argument("--role", required=True)
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("falta ffmpeg")
    {"index": cmd_index, "stats": cmd_stats, "list": cmd_list}[a.cmd](a)


if __name__ == "__main__":
    main()
