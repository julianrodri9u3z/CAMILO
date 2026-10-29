#!/usr/bin/env python3
"""
Detects WHERE the toolkit is running and which editing features that machine supports, and what to do for the rest.
Run it at the start of an editing session (Claude: run this first and plan only with the features that say OK).

  python3 env_check.py [--json]
"""
import json, os, platform, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
import bcc_env  # keys live in ~/.bcc-toolkit/.env (they survive plugin updates); the skill's own .env is still honoured
SKILL_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (r.stdout + r.stderr).strip()
    except Exception:
        return ""


def keys():
    out = {}
    env = os.path.join(SKILL_DIR, ".env")
    vals = {}
    if os.path.isfile(env):
        for line in open(env):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                vals[k] = v
    for k in ("APIMART_API_KEY", "ELEVENLABS_API_KEY", "ASSEMBLYAI_KEY", "TWELVELABS_KEY", "PEXELS_API_KEY", "PIXABAY_API_KEY", "JAMENDO_CLIENT_ID", "APIFY_TOKEN"):
        v = os.environ.get(k) or vals.get(k, "")
        out[k] = bool(v) and not v.startswith("pega-aqui")
    return out


def main():
    import vision_setup
    osname = platform.system()
    r = {"os": osname, "machine": platform.machine(), "python": sys.version.split()[0]}
    r["ffmpeg"] = bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe"))
    r["node"] = run(["node", "-v"]) if shutil.which("node") else None
    r["remotion_deps"] = os.path.isdir(os.path.join(SKILL_DIR, "remotion", "node_modules"))
    if "--fix" in sys.argv and not r["remotion_deps"] and shutil.which("npm"):
        # the plugin folder is replaced on every update, so the edit engine's dependencies must be reinstalled after one (~2 min)
        print("Installing the edit engine's dependencies (npm install, ~2 min)...", flush=True)
        subprocess.run([shutil.which("npm"), "install", "--silent"], cwd=os.path.join(SKILL_DIR, "remotion"))
        r["remotion_deps"] = os.path.isdir(os.path.join(SKILL_DIR, "remotion", "node_modules"))
    motion = os.path.join(os.path.dirname(SKILL_DIR), "motion-video", "motion-studio")
    r["motion_video"] = ("not installed" if not os.path.isdir(motion) else
                         "ready" if os.path.isdir(os.path.join(motion, "node_modules")) and os.path.isdir(os.path.join(motion, ".venv"))
                         else "needs setup: bash motion-video/motion-studio/tools/setup.sh")
    r["yt_dlp"] = bool(shutil.which("yt-dlp"))
    chrome = [p for p in (
        "/Applications/Google Chrome.app", r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "/usr/bin/google-chrome") if os.path.exists(p)]
    r["chrome"] = bool(chrome)
    r["swift"] = osname == "Darwin" and bool(shutil.which("swiftc"))
    r["vision_py_candidate"] = vision_setup.find_python()
    r["mediapipe_ready"] = vision_setup.ready()
    r["keys"] = keys()
    vision_backend = "apple" if r["swift"] else ("mediapipe" if r["mediapipe_ready"] else None)
    f = {}
    f["core_editing (captions, b-roll, music, render)"] = "OK" if r["ffmpeg"] and r["node"] and r["remotion_deps"] else \
        "MISSING: " + ", ".join(x for x, ok in (("ffmpeg", r["ffmpeg"]), ("node", bool(r["node"])), ("remotion npm install", r["remotion_deps"])) if not ok)
    f["behind_text + caption_dodging (needs a vision backend)"] = f"OK via {vision_backend}" if vision_backend else (
        "AVAILABLE AFTER SETUP: `python3 scripts/vision_setup.py --yes` (~400 MB, ask the user)" if r["vision_py_candidate"] else
        "BLOCKED: needs Python 3.9-3.12 (mediapipe has no wheels for newer). Install 3.12 (winget install Python.Python.3.12 / brew install python@3.12), then vision_setup.py --yes")
    f["motion-video templates (make_card.py)"] = r["motion_video"]
    f["beat_sync (beat_grid, beat_snap)"] = "OK" if r["ffmpeg"] else "needs ffmpeg"
    f["sound design (make_sfx, add_sfx)"] = "OK" if r["ffmpeg"] else "needs ffmpeg"
    f["mastering + QA (finalize, qa_render)"] = "OK" if r["ffmpeg"] else "needs ffmpeg"
    f["tiktok b-roll search"] = "OK" if r["keys"].get("APIFY_TOKEN") else "needs APIFY_TOKEN in .env"
    f["tiktok clip download (yt-dlp)"] = "OK" if r["yt_dlp"] else "install yt-dlp (brew install yt-dlp / winget install yt-dlp)"
    r["features"] = f
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1))
        return
    print(f"{osname} {r['machine']} | python {r['python']} | ffmpeg {'yes' if r['ffmpeg'] else 'NO'} | node {r['node'] or 'NO'} | chrome {'yes' if r['chrome'] else 'NO'}")
    for k, v in f.items():
        print(f"  {k}: {v}")
    print("  keys set:", ", ".join(k for k, ok in r["keys"].items() if ok) or "none", "| missing:", ", ".join(k for k, ok in r["keys"].items() if not ok) or "none")


if __name__ == "__main__":
    main()
