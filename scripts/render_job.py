#!/usr/bin/env python3
"""
Render an EditPlan with Remotion, robustly.

Remotion's compositor intermittently fails with "No frame found at position ..." (seen 2026-10-29 on files that had
rendered fine minutes before, both A-roll and stock b-roll) when many frames are pulled in parallel. A retry almost
always passes. This wrapper:
  * deletes the previous output first -- a failed render must never leave an old file that later gets mastered
    and delivered as if it were new;
  * renders with moderate concurrency and retries up to --tries times, lowering concurrency each time;
  * exits non-zero if every try failed (callers must stop there).

Usage:
  python3 render_job.py --plan job.json --out render.mp4 [--composition UgcIA] [--tries 3] [--concurrency 4]
"""
import argparse, os, shutil, subprocess, sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTION = os.path.join(SKILL_DIR, "remotion")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--composition", default="UgcIA")
    ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=4)
    a = ap.parse_args()
    out, plan = os.path.abspath(a.out), os.path.abspath(a.plan)
    if os.path.exists(out):
        os.remove(out)
    npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
    log = os.path.splitext(out)[0] + ".log"
    conc = a.concurrency
    for t in range(1, a.tries + 1):
        with open(log, "w", encoding="utf-8", errors="replace") as lf:
            r = subprocess.run([npx, "remotion", "render", "src/index.ts", a.composition, out, f"--props={plan}",
                                "--gl=angle", f"--concurrency={conc}"], cwd=REMOTION, stdout=lf, stderr=subprocess.STDOUT)
        if r.returncode == 0 and os.path.exists(out):
            print(f"render ok (try {t}, concurrency {conc}): {out}")
            return
        txt = open(log, encoding="utf-8", errors="replace").read()
        why = "no frame found (compositor, intermittent)" if "No frame found" in txt else f"exit {r.returncode}"
        print(f"render try {t} failed: {why}; log: {log}")
        if os.path.exists(out):
            os.remove(out)
        conc = max(2, conc - 1)
    sys.exit(f"render FAILED after {a.tries} tries -- nothing to deliver")


if __name__ == "__main__":
    main()
