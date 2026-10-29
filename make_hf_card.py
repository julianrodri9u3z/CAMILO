#!/usr/bin/env python3
"""Render a HyperFrames catalog block (HTML + GSAP) as a cutaway for editar-anuncios.

HyperFrames (heygen-com/hyperframes, Apache-2.0) ships ~170 ready-made, parameterized blocks:
chat / WhatsApp-style threads, notifications, follow cards, AI-chat reveals, charts, maps, lower thirds,
shader transitions, 3D phones, code windows... Each block declares its editable slots
(`data-composition-variables`), so one block = infinite variations without touching HTML.

  python3 make_hf_card.py list [--tag chat] [--vertical] [--search word]
  python3 make_hf_card.py vars  --block message-thread-reveal
  python3 make_hf_card.py render --block message-thread-reveal --job casa --name chat-clientes \
        --vars '{"contactName":"Cliente nuevo","questionMessage":"como lo hiciste?"}' [--trim 8] [--fit cover|contain]

The result is an H.264 MP4 dropped into editar-anuncios/remotion/public/jobs/<job>/ and a ready `broll` entry is
printed. Cards are SILENT in the edit (sound design comes from add_sfx.py).
Needs Node (npx) + ffmpeg. First run downloads HyperFrames and creates a cached project in ~/.cache/bcc-hyperframes
(check the machine with `npx hyperframes doctor`). Block/skill licence: HyperFrames is Apache-2.0.
"""
import argparse, json, os, re, shutil, subprocess, sys

CACHE = os.path.expanduser("~/.cache/bcc-hyperframes")
EDITAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # this skill's folder (works from the plugin cache too)
ENV = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
if os.name != "nt":   # GUI-launched shells on macOS often miss Homebrew's bin
    ENV["PATH"] = os.pathsep.join(["/opt/homebrew/bin", "/usr/local/bin", os.environ.get("PATH", "")])
NPX = [shutil.which("npx") or "npx", "--yes", "hyperframes"]   # shutil.which finds npx.cmd on Windows


def run(args, cwd=None, check=True, timeout=900):
    r = subprocess.run(args, cwd=cwd, env=ENV, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout)
    if check and r.returncode != 0:
        sys.exit(f"command failed: {' '.join(args)}\n" + (r.stdout + r.stderr)[-1500:])
    return r


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "card"


def catalog():
    path = os.path.join(CACHE, "catalog.json")
    os.makedirs(CACHE, exist_ok=True)
    if not os.path.isfile(path) or (os.path.getmtime(path) < __import__("time").time() - 7 * 86400):
        r = run(NPX + ["catalog", "--json"])
        i = r.stdout.find("[")
        open(path, "w").write(r.stdout[i:])
    return json.load(open(path))


def project():
    """One cached project; blocks are added on demand (they bring their own width/height)."""
    proj = os.path.join(CACHE, "proj")
    if not os.path.isfile(os.path.join(proj, "hyperframes.json")):
        os.makedirs(CACHE, exist_ok=True)
        run(NPX + ["init", "proj", "--non-interactive", "--resolution", "portrait", "--example", "blank"], cwd=CACHE)
    return proj


def ensure_block(name):
    proj = project()
    comp = os.path.join(proj, "compositions", f"{name}.html")
    if not os.path.isfile(comp):
        run(NPX + ["add", name], cwd=proj)
    if not os.path.isfile(comp):
        sys.exit(f"block '{name}' not found. See: make_hf_card.py list --search <word>")
    return proj, comp


def declared_vars(comp):
    html = open(comp, encoding="utf-8").read()
    m = re.search(r"data-composition-variables='(.*?)'\s*>", html, re.S)
    if not m:
        return []
    import html as H
    return json.loads(H.unescape(m.group(1)))


def cmd_list(a):
    items = [i for i in catalog() if i["type"] == "block"]
    if a.tag:
        items = [i for i in items if a.tag in i["tags"]]
    if a.vertical:
        items = [i for i in items if (i.get("dimensions") or {}).get("height", 0) > (i.get("dimensions") or {}).get("width", 0)]
    if a.search:
        w = a.search.lower()
        items = [i for i in items if w in (i["name"] + " " + i["description"] + " " + " ".join(i["tags"])).lower()]
    for i in items:
        d = i.get("dimensions") or {}
        print(f"{i['name']:32} {d.get('width')}x{d.get('height')} {i.get('duration')}s  [{', '.join(i['tags'][:4])}]  {i['description'][:90]}")
    print(f"\n{len(items)} blocks")


def cmd_vars(a):
    proj, comp = ensure_block(a.block)
    for v in declared_vars(comp):
        print(f"{v['id']:22} {v.get('type','?'):7} default={json.dumps(v.get('default'), ensure_ascii=False)[:70]}   # {v.get('label','')}")
    t = os.path.join(proj, "TEMPLATE.md")
    if os.path.isfile(t):
        print("\n(see the block contract in", t, ")")


def cmd_render(a):
    proj, comp = ensure_block(a.block)
    declared = {v["id"]: v for v in declared_vars(comp)}
    vars_ = json.loads(a.vars) if a.vars else {}
    if a.vars_file:
        vars_.update(json.load(open(a.vars_file)))
    unknown = [k for k in vars_ if declared and k not in declared]
    if unknown:
        sys.exit(f"unknown variables for {a.block}: {unknown}. Declared: {list(declared)}")
    # local image paths -> copied into the project so the renderer can load them
    for k, v in list(vars_.items()):
        if isinstance(v, str) and os.path.isfile(os.path.expanduser(v)):
            dst = os.path.join(proj, "assets", "user")
            os.makedirs(dst, exist_ok=True)
            fn = f"{slug(a.name)}-{k}{os.path.splitext(v)[1]}"
            shutil.copy(os.path.expanduser(v), os.path.join(dst, fn))
            vars_[k] = f"assets/user/{fn}"
    name = slug(a.name)
    raw = os.path.join(CACHE, "renders", f"{name}.mp4")
    os.makedirs(os.path.dirname(raw), exist_ok=True)
    cmd = NPX + ["render", "-c", f"compositions/{a.block}.html", "-o", raw, "--workers", str(a.workers), "--quiet"]
    if vars_:
        vf_path = os.path.join(CACHE, "renders", f"{name}.vars.json")
        json.dump(vars_, open(vf_path, "w", encoding="utf-8"), ensure_ascii=False)
        cmd += ["--variables-file", vf_path]
    r = run(cmd, cwd=proj, check=False)
    if r.returncode != 0 or not os.path.isfile(raw):
        sys.exit("render failed:\n" + (r.stdout + r.stderr)[-1500:])
    dst_dir = os.path.join(EDITAR, "remotion", "public", "jobs", a.job)
    os.makedirs(dst_dir, exist_ok=True)
    out = os.path.join(dst_dir, f"{name}.mp4")
    vf = {"cover": "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
          "contain": f"scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color={a.bg}",
          "none": "scale=trunc(iw/2)*2:trunc(ih/2)*2"}[a.fit]
    speed = a.speed
    if a.squeeze:
        # UI blocks wait for "a person reading" between events: cut those dead holds (keep 0.2 s of each)
        tmp = raw.replace(".mp4", ".sped.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-an", "-vf", f"setpts=PTS/{a.speed}", "-c:v", "libx264", "-crf", "14", "-g", "12", "-pix_fmt", "yuv420p", tmp],
                       check=True, stdin=subprocess.DEVNULL)
        log = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-vf", "freezedetect=n=-60dB:d=0.4", "-f", "null", "-"], capture_output=True, text=True).stderr
        starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", log)]
        durs = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", log)]
        drops = [(st + 0.2, st + du) for st, du in zip(starts, durs) if du > 0.45]
        raw, speed = tmp, 1.0
        if drops:
            expr = "+".join(f"between(t,{x:.3f},{y:.3f})" for x, y in drops)
            vf_pre = f"select='not({expr})',setpts=N/FRAME_RATE/TB,"
        else:
            vf_pre = ""
        print(f"squeeze: removed {sum(y - x for x, y in drops):.1f}s of dead holds")
    else:
        vf_pre = ""
    ff = ["ffmpeg", "-y", "-v", "error", "-i", raw]
    if a.trim:
        ff += ["-t", str(a.trim)]
    ff += ["-an", "-vf", vf_pre + f"setpts=PTS/{speed}," + vf + ",fps=30", "-c:v", "libx264", "-crf", "16", "-g", "12", "-pix_fmt", "yuv420p", out]
    subprocess.run(ff, check=True, stdin=subprocess.DEVNULL)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                               capture_output=True, text=True).stdout.strip() or 0)
    print(f"ok: {dur:.1f}s card -> {out}")
    print(json.dumps({"src": f"jobs/{a.job}/{name}.mp4", "atMs": 0, "durationMs": int(dur * 1000), "scrim": 0}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("--tag"); l.add_argument("--vertical", action="store_true"); l.add_argument("--search")
    v = sub.add_parser("vars"); v.add_argument("--block", required=True)
    r = sub.add_parser("render")
    r.add_argument("--block", required=True); r.add_argument("--job", required=True); r.add_argument("--name", required=True)
    r.add_argument("--vars", help="JSON object of variable overrides"); r.add_argument("--vars-file")
    r.add_argument("--trim", type=float, help="cut the card to N seconds")
    r.add_argument("--fit", default="contain", choices=["contain", "cover", "none"], help="how a 16:9 block is placed in 9:16")
    r.add_argument("--speed", type=float, default=1.0, help="play the block faster (the output is trimmed AFTER speeding up)")
    r.add_argument("--squeeze", action="store_true", help="cut the dead holds (static stretches) of UI blocks")
    r.add_argument("--bg", default="black"); r.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    {"list": cmd_list, "vars": cmd_vars, "render": cmd_render}[a.cmd](a)


if __name__ == "__main__":
    main()
