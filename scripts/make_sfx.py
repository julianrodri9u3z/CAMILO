#!/usr/bin/env python3
"""
Synthesize the sound-design library (whooshes, pops, hits, riser, ding, ticks) into
remotion/public/sfx/*.wav. 100% generated locally with numpy -> no licenses, no downloads.

These are deliberately SIMPLE, clean, short sounds meant to sit UNDER the voice at low
volume (0.2-0.4) and make graphics/cuts "feel" physical -- the single biggest tell of an
edit made by a human (silent text pops and silent b-roll cuts read as automated).
They cannot replace a hand-picked pack for a hero ad; if the user later provides a real SFX
pack (Freesound/Envato...), drop the files into remotion/public/sfx/ with the same names.

Usage: python3 make_sfx.py [--out DIR]     (idempotent; overwrites)
"""
import argparse, os, wave
import numpy as np

SR = 44100
RNG = np.random.default_rng(11)


def t(d):
    return np.arange(int(SR * d)) / SR


def lowpass_sweep(x, f0, f1, curve="exp", passes=2):
    """Time-varying one-pole lowpass: cutoff goes f0 -> f1 across the signal."""
    n = len(x)
    if curve == "exp":
        fc = f0 * (f1 / f0) ** (np.arange(n) / max(1, n - 1))
    else:
        fc = np.linspace(f0, f1, n)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = x.copy()
    for _ in range(passes):
        out = np.empty_like(y)
        acc = 0.0
        for i in range(n):
            acc += a[i] * (y[i] - acc)
            out[i] = acc
        y = out
    return y


def fade(x, ms_in=4, ms_out=12):
    a, b = int(SR * ms_in / 1000), int(SR * ms_out / 1000)
    x = x.copy()
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def norm(x, peak=0.7):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def whoosh(d, f0, f1, f2, peak_at=0.45):
    n = len(t(d))
    noise = RNG.normal(0, 1, n)
    up = lowpass_sweep(noise[: int(n * peak_at)], f0, f1)
    down = lowpass_sweep(noise[int(n * peak_at):], f1, f2)
    x = np.concatenate([up, down])
    env = np.sin(np.pi * np.linspace(0, 1, n) ** 0.8) ** 2
    return fade(norm(x * env), 6, 30)


def pop():
    x = t(0.14)
    f = 260 + 300 * np.exp(-x / 0.025)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-x / 0.035)
    click = RNG.normal(0, 1, len(x)) * np.exp(-x / 0.002) * 0.25
    return fade(norm(s + click), 1, 20)


def tick():
    x = t(0.06)
    s = np.sin(2 * np.pi * 1900 * x) * np.exp(-x / 0.009)
    n = lowpass_sweep(RNG.normal(0, 1, len(x)), 6000, 2500, passes=1) * np.exp(-x / 0.006) * 0.6
    return fade(norm(s + n, 0.55), 1, 8)


def click_soft():
    x = t(0.05)
    n = lowpass_sweep(RNG.normal(0, 1, len(x)), 4000, 1500, passes=1) * np.exp(-x / 0.008)
    s = np.sin(2 * np.pi * 1100 * x) * np.exp(-x / 0.012) * 0.6
    return fade(norm(n + s, 0.5), 1, 8)


def hit_low():
    """Impact with a sub layer AND audible mid/high content: a pure sub thump disappears on phone speakers
    (and in any 16 kHz-downsampled analysis), so we add a 100-250 Hz body and a 1.5-5 kHz transient click."""
    x = t(0.8)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-x / 0.07)) / SR) * np.exp(-x / 0.22)
    body = np.sin(2 * np.pi * np.cumsum(95 + 130 * np.exp(-x / 0.05)) / SR) * np.exp(-x / 0.12) * 0.9
    thump = lowpass_sweep(RNG.normal(0, 1, len(x)), 900, 120, passes=2) * np.exp(-x / 0.05) * 0.8
    click = lowpass_sweep(RNG.normal(0, 1, len(x)), 5000, 1800, passes=1) * np.exp(-x / 0.006) * 0.5
    y = np.tanh(1.6 * (0.5 * sub + 1.2 * body + 0.5 * thump + 0.8 * click))
    return fade(norm(y, 0.8), 1, 60)


def riser(d=1.6):
    x = t(d)
    n = RNG.normal(0, 1, len(x))
    s = lowpass_sweep(n, 250, 7000, curve="exp", passes=2)
    glide = np.sin(2 * np.pi * np.cumsum(200 + 700 * (x / d) ** 2) / SR) * 0.25
    env = (x / d) ** 2.2
    return fade(norm((s + glide) * env, 0.65), 20, 6)


def ding():
    x = t(1.0)
    y = sum(a * np.sin(2 * np.pi * f * x) * np.exp(-x / tau)
            for f, a, tau in [(1319, 1.0, 0.24), (2637, 0.3, 0.14), (3957, 0.12, 0.08)])
    return fade(norm(y, 0.6), 1, 80)


LIB = {
    "whoosh_soft": lambda: whoosh(0.6, 300, 3200, 700),
    "whoosh_fast": lambda: whoosh(0.3, 700, 6500, 1500, 0.5),
    "pop": pop,
    "tick": tick,
    "click_soft": click_soft,
    "hit_low": hit_low,
    "riser": riser,
    "ding": ding,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "remotion", "public", "sfx"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, fn in LIB.items():
        x = fn()
        write(os.path.join(a.out, f"{name}.wav"), x)
        print(f"{name}.wav  {len(x)/SR:.2f}s  peak {np.max(np.abs(x)):.2f}")


if __name__ == "__main__":
    main()
