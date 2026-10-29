#!/usr/bin/env python3
"""
Voice enhancement for phone/selfie recordings: removes room hiss, tames mud, adds presence, controls loudness jumps,
de-esses and raises the level. ffmpeg only (works on any OS).

Chain: high-pass 80 Hz -> light FFT denoise (afftdn) -> EQ (-2.5 dB @200 Hz mud,
+3.5 dB @3 kHz presence, +1.5 dB air shelf @9 kHz) -> de-esser -> gentle compressor (3:1) -> +6 dB into a hard limiter (result about -16 LUFS, peak -1 dBFS).
Final loudness is set later by finalize.py (-14 LUFS) after music/SFX are mixed.

It also MEASURES the result (ears-free verification): speech level and noise floor before/after. What ffmpeg CANNOT do:
remove reverb/echo of a hard-walled room or music bleeding into the mic; for that an AI voice isolator (ElevenLabs
"Voice Isolator", Adobe Podcast) is needed -- offer it, and say that the audio leaves the machine if used.

Usage:
  python3 enhance_voice.py --video in.mp4 --out-audio voice.wav [--strength 1.0] [--verify-asr]
  python3 enhance_voice.py --video in.mp4 --out-video enhanced.mp4      # also muxes the clean voice back (video copied)
strength: 0.6 gentle ... 1.0 default ... 1.4 strong (only changes the denoise depth; measured effect is small)
"""
import argparse, json, subprocess, sys
import numpy as np

SR = 44100


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, **kw)


def pcm(path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss else []) + (["-t", str(t)] if t else []) + \
          ["-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True, stdin=subprocess.DEVNULL).stdout, dtype=np.float32)


def levels(x):
    """speech level (dBFS RMS of the loudest 30% of 50 ms windows), noise floor (10th percentile), SNR estimate."""
    w = int(0.05 * SR)
    n = len(x) // w
    r = np.sqrt(np.mean(x[: n * w].reshape(n, w) ** 2, axis=1)) + 1e-9
    db = 20 * np.log10(r)
    speech = float(np.mean(np.sort(db)[int(0.7 * n):]))
    floor = float(np.percentile(db, 10))
    return speech, floor, speech - floor


def chain(strength):
    """EQ + de-ess + compression (+ very light denoise). A gate and a one-pass loudnorm were TRIED and REJECTED:
    they lowered AssemblyAI's word confidence (0.980 -> 0.968, weak words 5 -> 12) by chopping reverb tails. This chain scored
    0.984 (weak words 5 -> 2) on a test recording: better intelligibility, ~+14 dB level."""
    nr = round(6 + 4 * strength, 1)
    return ",".join([
        "highpass=f=80",
        f"afftdn=nr={nr}:nf=-40",
        "equalizer=f=200:t=q:w=1.2:g=-2.5",
        "equalizer=f=3000:t=q:w=1.0:g=3.5",
        "highshelf=f=9000:g=1.5",
        "deesser=i=0.25",
        # two-stage compression: phone recordings often peak at -7 dB with an average of -34 dB; a single compressor cannot
        # raise the average without hitting the peak limit (measured: 1 stage -> -31 LUFS, 2 stages -> -19.7 LUFS)
        "acompressor=threshold=-34dB:ratio=3:attack=8:release=150:makeup=6",
        "acompressor=threshold=-22dB:ratio=4:attack=4:release=80:makeup=4",
        # push into a hard limiter: measured -24.9 LUFS without it, -16.5 LUFS with +6 dB (peak -1.1 dBFS)
        "volume=6dB",
        "alimiter=limit=0.89:attack=3:release=60:level=disabled",
    ])


def render_two_pass(video, af, out, target=-18.0):
    """Two-pass linear loudnorm: single-pass loudnorm cannot lift a -34 dB phone recording to the target."""
    import re
    r = run(["ffmpeg", "-hide_banner", "-i", video, "-vn", "-af", f"{af},loudnorm=I={target}:TP=-2:LRA=9:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return r
    j = json.loads(m.group(0))
    f = (f"{af},loudnorm=I={target}:TP=-2:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
         f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    return run(["ffmpeg", "-y", "-v", "error", "-i", video, "-vn", "-af", f, "-ar", "48000", "-ac", "1", out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out-audio")
    ap.add_argument("--out-video")
    ap.add_argument("--strength", type=float, default=1.0)
    a = ap.parse_args()
    out_audio = a.out_audio or (a.out_video.rsplit(".", 1)[0] + "_voice.wav" if a.out_video else None)
    if not out_audio:
        sys.exit("give --out-audio or --out-video")
    r = run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-vn", "-af", chain(a.strength), "-ar", "48000", "-ac", "1", out_audio])
    if r.returncode != 0:
        sys.exit("enhance failed: " + r.stderr[-500:])
    before, after = pcm(a.video), pcm(out_audio)
    sb, fb, nb = levels(before)
    sa, fa, na = levels(after)
    print(f"speech level: {sb:6.1f} -> {sa:6.1f} dBFS | noise floor: {fb:6.1f} -> {fa:6.1f} dBFS | speech-to-noise: {nb:5.1f} -> {na:5.1f} dB")
    if a.out_video:
        m = run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", out_audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "192k", "-shortest", a.out_video])
        if m.returncode != 0:
            sys.exit("mux failed: " + m.stderr[-400:])
        print("wrote", a.out_video)
    print("wrote", out_audio)


if __name__ == "__main__":
    main()
