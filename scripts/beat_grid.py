#!/usr/bin/env python3
"""
"Hear" a music track numerically: tempo, beat grid, downbeats, bass DROPS and energy sections.
numpy + ffmpeg only (no librosa/scipy -> works on any Python the students have).

Method: log-magnitude STFT -> spectral-flux onset envelope -> tempo by autocorrelation (60-180 BPM, with a
moderate-tempo prior to avoid half/double errors) -> beat tracking by dynamic programming (Ellis 2007, the
same idea librosa uses) -> downbeat = the beat phase (mod 4) with the most onset energy.
Drops = places where bass energy (<120 Hz, via FFT bins) jumps >1.8x versus the previous ~4 s (same idea as the
motion-video kit's music.py, which needs scipy).

Usage:
  python3 beat_grid.py --audio music.mp3 --out beats.json [--start S --dur D]
Prints a short text summary (cheap on tokens). beats.json: {bpm, beats[], downbeats[], onsets[], drops[], energy[]}
Times are seconds from the START of the analyzed audio window (add --start back if you cut it).
"""
import argparse, json, subprocess
import numpy as np

SR = 22050
HOP = 512
NFFT = 1024


def load(path, start, dur):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(start)] if start else []) + (["-t", str(dur)] if dur else []) + \
          ["-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True, stdin=subprocess.DEVNULL).stdout, dtype=np.float32)


def stft_mag(x):
    n = 1 + (len(x) - NFFT) // HOP
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(x[idx] * np.hanning(NFFT), axis=1))


def onset_env(X):
    """Band-weighted spectral flux: kicks/snares (low-mid) count more than hats/noise (high), because a plain
    full-band flux locks onto hi-hats (tested on synthetic click tracks: beats landed on the off-beats)."""
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    out = np.zeros(X.shape[0])
    for lo, hi, w in ((30, 150, 1.0), (150, 1500, 0.8), (1500, 9000, 0.3)):
        B = np.log1p(10 * X[:, (f >= lo) & (f < hi)])
        fl = np.r_[0, np.maximum(0, np.diff(B, axis=0)).sum(1)]
        fl = np.convolve(fl, np.ones(3) / 3, mode="same")
        out += w * (fl - fl.mean()) / (fl.std() + 1e-9)
    return (out - out.mean()) / (out.std() + 1e-9)


def tempo(env, fps):
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    lags = np.arange(1, len(ac))
    bpm = 60 * fps / lags
    ok = (bpm >= 60) & (bpm <= 180)
    prior = np.exp(-0.5 * (np.log2(bpm / 120.0) / 0.9) ** 2)   # mild preference for ~120 BPM
    score = ac[1:] * prior
    score[~ok] = -np.inf
    k = int(np.argmax(score)) + 1                               # lag (frames) of the peak
    # parabolic interpolation around the peak for sub-frame lag precision (~0.5 % tempo error instead of ~2 %)
    if 1 < k < len(ac) - 1:
        y0, y1, y2 = ac[k - 1], ac[k], ac[k + 1]
        den = y0 - 2 * y1 + y2
        k = k + (0.5 * (y0 - y2) / den if den != 0 else 0)
    return float(60 * fps / k)


def track_beats(env, fps, bpm, tight=100.0):
    period = 60.0 * fps / bpm
    n = len(env)
    score = np.zeros(n)
    back = np.zeros(n, int) - 1
    for i in range(n):
        lo, hi = int(i - 2 * period), int(i - period / 2)
        if hi <= 0:
            score[i] = env[i]
            continue
        lo = max(lo, 0)
        prev = np.arange(lo, hi)
        pen = -tight * np.log((i - prev) / period) ** 2
        cand = score[prev] + pen
        j = int(np.argmax(cand))
        score[i] = env[i] + cand[j]
        back[i] = prev[j]
    i = int(np.argmax(score[-int(period):]) + n - int(period)) if n > period else int(np.argmax(score))
    beats = []
    while i >= 0:
        beats.append(i)
        i = back[i]
    return np.array(beats[::-1]) / fps


def drops(x):
    X = np.abs(np.fft.rfft(x[: (len(x) // 660) * 660].reshape(-1, 660), axis=1))   # 30 ms frames
    f = np.fft.rfftfreq(660, 1 / SR)
    L = np.sqrt((X[:, f < 120] ** 2).mean(1))
    out = []
    cands = []
    for i in range(134, len(L) - 67, 3):
        r = L[i:i + 67].mean() / (L[i - 134:i].mean() + 1e-4)
        if r > 1.8:
            cands.append((r, i))
    for r, i in sorted(cands, reverse=True):
        if all(abs(i - j) > 200 for _, j in out):
            base = L[i - 134:i].mean()
            k = next((k for k in range(i - 30, i + 60) if L[k] > 2 * base), i)
            out.append((r, k))
    return sorted([(round(k * 0.03, 2), round(float(r), 1)) for r, k in out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--dur", type=float, default=0)
    a = ap.parse_args()
    x = load(a.audio, a.start, a.dur)
    fps = SR / HOP
    X = stft_mag(x)
    env = onset_env(X)
    bpm = tempo(env, fps)
    beats = track_beats(env, fps, bpm)
    # downbeats: strongest of the 4 phases
    if len(beats) >= 8:
        e = np.array([env[int(round(b * fps))] for b in beats if int(round(b * fps)) < len(env)])
        phase = int(np.argmax([e[p::4].sum() for p in range(4)]))
        downbeats = beats[phase::4]
    else:
        downbeats = beats[:0]
    peaks = [i for i in range(1, len(env) - 1) if env[i] > 1.2 and env[i] >= env[i - 1] and env[i] > env[i + 1]]
    rms = [float(np.sqrt(np.mean(x[s * SR:(s + 5) * SR] ** 2))) for s in range(0, len(x) // SR, 5)]
    d = drops(x)
    if len(beats) >= 8:
        bpm = 60.0 / float(np.median(np.diff(beats)))   # report the tempo the tracker actually followed
    res = {"bpm": round(bpm, 1), "duration_s": round(len(x) / SR, 2), "beats": [round(float(b), 3) for b in beats],
           "downbeats": [round(float(b), 3) for b in downbeats], "onsets": [round(i / fps, 3) for i in peaks],
           "drops": [{"t": t, "ratio": r} for t, r in d], "energy_5s": [round(v, 3) for v in rms]}
    if a.out:
        json.dump(res, open(a.out, "w"))
    med = float(np.median(np.diff(beats))) if len(beats) > 1 else 0
    print(f"{res['duration_s']}s | BPM ~ {res['bpm']} (median beat gap {med:.3f}s -> {60/med if med else 0:.1f}) | {len(beats)} beats, "
          f"{len(downbeats)} downbeats, {len(peaks)} onsets | drops: " + (", ".join(f"{t:.2f}s (x{r})" for t, r in d) or "none"))


if __name__ == "__main__":
    main()
