#!/usr/bin/env python3
"""
Per-frame PERSON MATTES + FACE/HAND ZONES for a video. Powers behindText (text behind the presenter) and
dodge_captions.py (subtitles that avoid faces/hands). ONE command for every OS: it detects where it runs and picks the
backend itself.

  python3 vision_analyze.py --video raw.mp4 --out DIR [--start S --dur D] [--matte-width 540]
                            [--backend auto|apple|mediapipe] [--no-matte] [--no-zones] [--quality accurate|balanced|fast]

Backends (identical output: DIR/matte/m_000001.png RGBA alpha=person, and DIR/zones.json):
  apple      macOS only. Apple Vision via a small Swift program compiled on first use (needs Xcode Command Line Tools,
             `xcode-select --install`). Nothing else to install. Sharpest edges. ~17 frames/s.
  mediapipe  Windows / Linux / macOS fallback. Google MediaPipe in a private venv made by vision_setup.py (~400 MB, ask the
             user first). Measured vs Apple Vision on the same frames: mask IoU 0.985, same face/hand counts, ~12 frames/s.
auto: macOS with a working Swift toolchain -> apple; otherwise mediapipe if set up; otherwise tells you what to run.
"""
import argparse, os, platform, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mac", "vision_analyze.swift")
BIN = os.path.join(HERE, "mac", ".bin", "vision_analyze")
sys.path.insert(0, HERE)


def apple_ok():
    return platform.system() == "Darwin" and shutil.which("swiftc") is not None


def ensure_apple_binary():
    if os.path.isfile(BIN) and os.path.getmtime(BIN) >= os.path.getmtime(SRC):
        return True
    os.makedirs(os.path.dirname(BIN), exist_ok=True)
    print("compiling vision_analyze.swift (first run, ~40 s)...")
    r = subprocess.run(["swiftc", "-O", "-swift-version", "5", "-o", BIN, SRC], capture_output=True, text=True)
    if r.returncode != 0:
        print("swift compile failed (install Xcode Command Line Tools with `xcode-select --install`):\n" + r.stderr[-600:], file=sys.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--dur", type=float, default=0)
    ap.add_argument("--matte-width", type=int, default=540)
    ap.add_argument("--quality", default="accurate", choices=["accurate", "balanced", "fast"])
    ap.add_argument("--zone-step", type=int, default=3)
    ap.add_argument("--no-matte", action="store_true")
    ap.add_argument("--no-zones", action="store_true")
    ap.add_argument("--no-png", action="store_true", help="only person/face/hand boxes (zones.json), no matte images: fast + tiny; enough for smart reframing")
    ap.add_argument("--backend", default="auto", choices=["auto", "apple", "mediapipe"])
    a = ap.parse_args()

    import vision_setup
    backend = a.backend
    if backend == "auto":
        if apple_ok() and ensure_apple_binary():
            backend = "apple"
        elif vision_setup.ready():
            backend = "mediapipe"
        else:
            sys.exit("No vision backend ready on this machine (" + platform.system() + "). Run `python3 scripts/env_check.py`; then, "
                     "with the user's OK (~400 MB): `python3 scripts/vision_setup.py --yes` and re-run this command.")
    print(f"backend: {backend} ({platform.system()})")
    if backend == "apple":
        if not (apple_ok() and ensure_apple_binary()):
            sys.exit("Apple backend not available here")
        cmd = [BIN, os.path.abspath(a.video), os.path.abspath(a.out), "--matte-width", str(a.matte_width), "--quality", a.quality,
               "--start", str(a.start), "--dur", str(a.dur), "--zone-step", str(a.zone_step)]
    else:
        if not vision_setup.ready():
            sys.exit("mediapipe backend not set up: with the user's OK run `python3 scripts/vision_setup.py --yes`")
        cmd = [vision_setup.venv_python(), os.path.join(HERE, "vision_mediapipe.py"), os.path.abspath(a.video), os.path.abspath(a.out),
               "--matte-width", str(a.matte_width), "--start", str(a.start), "--dur", str(a.dur), "--zone-step", str(a.zone_step)]
    if a.no_png:
        cmd.append("--no-png")
    if a.no_matte:
        cmd.append("--no-matte")
    if a.no_zones:
        cmd.append("--no-zones")
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
