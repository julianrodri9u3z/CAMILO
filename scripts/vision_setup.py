#!/usr/bin/env python3
"""
One-time setup for the CROSS-PLATFORM vision backend (MediaPipe) used by vision_analyze.py on Windows/Linux, and on
macOS when Apple Vision/Swift is unavailable.

What it installs (ASK THE USER FIRST, it is ~400 MB and takes a few minutes):
  * a private virtual environment at <skill>/.venv-vision with: mediapipe, numpy, pillow  (needs Python 3.9-3.12 --
    mediapipe has no wheels for 3.13+ yet; if the system Python is newer, install 3.12: Windows `winget install
    Python.Python.3.12`, macOS `brew install python@3.12`)
  * three small public Google model files into <skill>/models/ (selfie segmenter 0.25 MB, face detector 0.2 MB,
    hand landmarker 7.8 MB; Apache-2.0)
Nothing is installed globally.

Usage:  python3 vision_setup.py --yes          (run `python3 env_check.py` first to see whether you need it)
"""
import argparse, os, platform, shutil, subprocess, sys, urllib.request

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV = os.path.join(SKILL_DIR, ".venv-vision")
MODELS = os.path.join(SKILL_DIR, "models")
B = "https://storage.googleapis.com/mediapipe-models"
FILES = {
    "selfie_segmenter.tflite": f"{B}/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite",
    "face_detector.tflite": f"{B}/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
    "hand_landmarker.task": f"{B}/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
}


def venv_python():
    return os.path.join(VENV, "Scripts", "python.exe") if platform.system() == "Windows" else os.path.join(VENV, "bin", "python")


def find_python():
    """A Python 3.9-3.12 interpreter command (list), or None."""
    cands = []
    if platform.system() == "Windows":
        cands += [["py", f"-3.{v}"] for v in (12, 11, 10, 9)]
    cands += [[f"python3.{v}"] for v in (12, 11, 10, 9)] + [["python3"], ["python"]]
    for c in cands:
        try:
            r = subprocess.run(c + ["-c", "import sys;print('%d.%d'%sys.version_info[:2])"], capture_output=True, text=True)
            if r.returncode == 0:
                major, minor = map(int, r.stdout.strip().split("."))
                if major == 3 and 9 <= minor <= 12:
                    return c
        except Exception:
            continue
    return None


def ready():
    return os.path.isfile(venv_python()) and all(os.path.isfile(os.path.join(MODELS, f)) for f in FILES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="confirm you have the user's OK for the ~400 MB install")
    a = ap.parse_args()
    if ready():
        print("vision backend (mediapipe) already set up:", VENV)
        return
    if not a.yes:
        sys.exit("This installs ~400 MB (mediapipe in a private venv + 3 model files). Ask the user, then re-run with --yes.")
    py = find_python()
    if not py:
        sys.exit("No Python 3.9-3.12 found (mediapipe has no wheels for 3.13+). Install 3.12: Windows `winget install Python.Python.3.12`, macOS `brew install python@3.12`, then re-run.")
    if not os.path.isfile(venv_python()):
        print("creating venv with", " ".join(py))
        subprocess.run(py + ["-m", "venv", VENV], check=True)
    print("installing mediapipe (a few minutes)...")
    subprocess.run([venv_python(), "-m", "pip", "install", "-q", "mediapipe", "numpy", "pillow"], check=True)
    os.makedirs(MODELS, exist_ok=True)
    for name, url in FILES.items():
        dst = os.path.join(MODELS, name)
        if not os.path.isfile(dst):
            print("downloading", name)
            urllib.request.urlretrieve(url, dst)
    print("ready.")


if __name__ == "__main__":
    main()
