#!/usr/bin/env python3
"""
Removes dead air from a raw talking-head video and, if it's still longer than
the target duration after that, speeds up the whole thing uniformly (video +
audio) to hit it. Outputs a new video file AND a remapped copy of the
word-level caption timestamps (from an AssemblyAI transcript JSON) so
captions/b-roll built from the ORIGINAL timeline still line up with the NEW
one.

Why word gaps instead of ffmpeg silencedetect: the transcript already tells
us exactly where speech is, which is more reliable than an audio-level
silence threshold (immune to background music/hiss). A gap between two
consecutive words IS a silence, by definition.

KNOWN FAILURE MODE -- ASR timestamp drift (read before debugging an
unexplained leftover silence): AssemblyAI's word timestamps can be off by
seconds even when the transcribed TEXT is perfect and overall `confidence`
is high (a real case: 98.77% confidence, correct words, but the word
"Cuando" was tagged ~2.57s earlier than it actually starts in the audio).
Since build_keep_segments() trusts those timestamps to decide where speech
starts/ends, a drifted timestamp makes it keep a chunk of silence that
should have been cut -- and this looks EXACTLY like a code bug (a gap that
"wasn't cut") when it's actually bad input data. `--verify` (see
verify_tightened_output) now catches this class of bug automatically by
checking actual re-transcribed gap sizes, not just word text -- see its
docstring. If it flags a gap anomaly, the diagnostic recipe that found this
originally: extract a plain (non-sped, non-cut) copy of just the suspect
original-timeline span with ffmpeg, re-transcribe THAT in isolation, and
compare its word start times against the original transcript -- the
isolated re-transcription is ground truth.

Usage:
    python3 tighten_pacing.py \
        --video raw.mp4 --transcript raw_transcript.json \
        --output-dir out/ --target-duration-s 105 --max-pause-ms 350

Writes to --output-dir:
    tightened.mp4        -- the trimmed (and possibly sped-up) video
    captions_remapped.json  -- same shape as the `words` field, timestamps
                                remapped onto the new timeline
    report.json           -- original/new duration, speed factor, how many
                              pauses were trimmed and by how much
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import time

import requests

# Raised from 350ms after real-world feedback: 350ms was cutting pauses tight
# enough that some cuts felt like they clipped into the next word / made
# speech hard to follow, even though no cut technically landed inside a word
# boundary. 450ms matches the 400-600ms range documented as safe by the
# video-use project for the same technique.
DEFAULT_MAX_PAUSE_MS = 450
LEADING_TRIM_MS = 150  # how much silence to keep before the first word
TRAILING_TRIM_MS = 250  # how much to keep after the last word


import bcc_env  # keys live in ~/.bcc-toolkit/.env (they survive plugin updates); the skill's own .env is still honoured
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = bcc_env.ENV_PATH   # messages point at the persistent file


def load_env_file(path):
    values = {}
    if not os.path.isfile(path):
        return values
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_assemblyai_key():
    key = os.environ.get("ASSEMBLYAI_KEY")
    if not key:
        key = load_env_file(ENV_FILE).get("ASSEMBLYAI_KEY")
    if not key or key.startswith("pega-aqui"):
        return None
    return key


def get_duration(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video],
        capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def get_fps(video):
    """Reads the source's frame rate so segment extraction/concat can be forced
    to that same constant rate (see the -r flag in run_ffmpeg_trim_concat_speed)
    -- hardcoding 24 or 30 would silently mismatch a source shot at the other
    rate and reintroduce the same VFR drift this is meant to prevent."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
         "-of", "default=noprint_wrappers=1:nokey=1", video],
        capture_output=True, text=True,
    )
    num, _, den = out.stdout.strip().partition("/")
    return float(num) / float(den or 1)


def build_keep_segments(words, video_duration_s, max_pause_ms):
    """Returns a sorted list of (start_s, end_s) segments to keep, in
    ORIGINAL video time, covering all speech with pauses capped at
    max_pause_ms."""
    if not words:
        return [(0.0, video_duration_s)]

    segments = []
    first_start = max(0.0, words[0]["start"] / 1000 - LEADING_TRIM_MS / 1000)
    cur_start = first_start

    for i in range(len(words) - 1):
        gap_ms = words[i + 1]["start"] - words[i]["end"]
        if gap_ms > max_pause_ms:
            cur_end = words[i]["end"] / 1000 + (max_pause_ms / 2) / 1000
            segments.append((cur_start, cur_end))
            cur_start = words[i + 1]["start"] / 1000 - (max_pause_ms / 2) / 1000

    last_end = min(video_duration_s, words[-1]["end"] / 1000 + TRAILING_TRIM_MS / 1000)
    segments.append((cur_start, last_end))

    return [(round(s, 3), round(e, 3)) for s, e in segments if e > s]


def apply_extra_cuts(keep_segments, extra_cuts):
    """Subtracts explicit (start_s, end_s) intervals -- e.g. a misspoken word
    to excise -- from the pause-based keep segments. Same mechanism as a
    pause cut, just forced rather than detected."""
    if not extra_cuts:
        return keep_segments
    result = list(keep_segments)
    for cut_start, cut_end in extra_cuts:
        next_result = []
        for seg_start, seg_end in result:
            if cut_end <= seg_start or cut_start >= seg_end:
                next_result.append((seg_start, seg_end))
                continue
            if cut_start > seg_start:
                next_result.append((seg_start, cut_start))
            if cut_end < seg_end:
                next_result.append((cut_end, seg_end))
        result = next_result
    return [(round(s, 3), round(e, 3)) for s, e in result if e > s]


def remap_time_fn(keep_segments, speed_factor):
    """Returns a function old_time_s -> new_time_s given the keep segments
    (post silence-removal, pre speed-up) and a uniform speed factor applied
    after that."""
    cum = 0.0
    boundaries = []  # (orig_start, orig_end, new_start_before_speed)
    for start, end in keep_segments:
        boundaries.append((start, end, cum))
        cum += end - start

    def remap(t):
        for start, end, new_start in boundaries:
            if t < start:
                return new_start / speed_factor
            if start <= t <= end:
                return (new_start + (t - start)) / speed_factor
        # after everything -- clamp to the end
        last_start, last_end, last_new_start = boundaries[-1]
        return (last_new_start + (last_end - last_start)) / speed_factor

    return remap


def run_ffmpeg_trim_concat_speed(video, keep_segments, speed_factor, out_path, source_fps):
    """Two-pass approach: extract+speed each segment to its own temp file,
    then concat those files with the plain concat DEMUXER (not a single
    giant filter_complex graph).

    History: an earlier version built one filter_complex chaining
    trim+setpts+atempo+afade+concat for all N segments in a single ffmpeg
    call. Verified correct per-segment in isolation (each extracted
    segment's duration matched the expected post-speed value to within
    ~50-90ms, normal frame-quantization), and correct in a 3-segment
    mini-repro -- but on the real 9-segment job it silently inserted ~3.3s
    of extra duration between two specific segments, confirmed two
    independent ways (re-transcribing the actual delivered output, and
    computing expected vs. actual cumulative segment boundaries). Never
    isolated the exact internal cause (suspect: fade/pts interaction across
    a large chained graph); the two-pass demuxer-concat approach below
    sidesteps it entirely and is the same reliable method already used
    elsewhere in this pipeline for clip concatenation.
    """
    n = len(keep_segments)
    FADE_S = 0.03
    tmp_dir = out_path + ".segs_tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    seg_paths = []

    for i, (start, end) in enumerate(keep_segments):
        final_dur = (end - start) / speed_factor
        fade_s = min(FADE_S, final_dur / 4) if final_dur < FADE_S * 4 else FADE_S
        fade_out_start = max(0.0, final_dur - fade_s)
        seg_path = os.path.join(tmp_dir, f"seg{i:03d}.mp4")
        if speed_factor != 1.0:
            vf = f"[0:v]trim=start={start}:end={end},setpts=(PTS-STARTPTS)/{speed_factor}[v]"
            af = (
                f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,atempo={speed_factor},"
                f"afade=t=in:st=0:d={fade_s:.4f},afade=t=out:st={fade_out_start:.4f}:d={fade_s:.4f}[a]"
            )
        else:
            vf = f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v]"
            af = (
                f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d={fade_s:.4f},afade=t=out:st={fade_out_start:.4f}:d={fade_s:.4f}[a]"
            )
        cmd = [
            "ffmpeg", "-nostdin", "-y", "-i", video,
            "-filter_complex", f"{vf};{af}",
            "-map", "[v]", "-map", "[a]",
            # setpts=PTS/speed_factor divides timestamps by a non-integer factor,
            # which does NOT land on a clean frame grid -- without forcing a
            # constant output frame rate here, each segment silently becomes VFR
            # (variable frame rate). Concatenating several VFR segments compounds
            # small timing errors invisibly until, several dozen seconds in, audio
            # and video visibly drift apart (real case: fine at the start, audibly
            # desynced by ~75% through a 27-clip video). -r forces resampling to a
            # true constant rate so every segment (and the final concat) shares
            # one exact, predictable frame grid.
            "-r", str(source_fps),
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            seg_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ffmpeg fallo en segmento {i}:\n" + result.stderr[-4000:], file=sys.stderr)
            sys.exit(1)
        seg_paths.append(seg_path)

    list_path = os.path.join(tmp_dir, "concat_list.txt")
    with open(list_path, "w") as f:
        for p in seg_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    cmd = [
        "ffmpeg", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
        # Each segment above is already true CFR at source_fps, but re-asserting
        # -r here costs nothing and guarantees the final file can't end up VFR
        # even if some future segment (e.g. one produced by a different code
        # path) slips through without it.
        "-r", str(source_fps),
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        out_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg fallo en concat final:\n" + result.stderr[-4000:], file=sys.stderr)
        sys.exit(1)


def _norm_word(s):
    s = s.lower()
    return re.sub(r"[^\wáéíóúñü]", "", s, flags=re.UNICODE)


def verify_tightened_output(tightened_video, expected_words, key, max_gap_ms=None):
    """Re-transcribes the tightened video and (a) diffs it against the words
    we expected to survive the cut, and (b) checks the RE-TRANSCRIBED word
    gaps for anomalies. (a) is the only reliable way to catch a cut that
    clipped into speech -- a visual/waveform check (timeline_check.py) can't
    tell you whether the result is still intelligible, only whether there's
    a visible jump or an audio pop. Real feedback that prompted (a): silence
    cuts were removing/garbling words even where no cut technically landed
    inside a word boundary.

    (b) catches a DIFFERENT failure mode: ASR timestamp drift in the
    original transcript (see module docstring) can make build_keep_segments
    leave a chunk of real silence in the output even though the text-only
    diff in (a) comes back a perfect match -- text matching alone is blind
    to this because the drifted word's TEXT is still correct, only its
    original timestamp was wrong. Any gap between two consecutive
    re-transcribed words that's well above what tightening should allow
    (max_gap_ms, i.e. roughly max_pause_ms/speed_factor) means real silence
    survived the cut and needs the isolated-resegment-and-retranscribe
    diagnostic described in the module docstring."""
    audio_path = tightened_video + ".verify_audio.mp3"
    subprocess.run(["ffmpeg", "-y", "-i", tightened_video, "-vn", "-acodec", "libmp3lame", audio_path], capture_output=True)

    with open(audio_path, "rb") as f:
        up_resp = requests.post("https://api.assemblyai.com/v2/upload", data=f, headers={"authorization": key}, timeout=120)
    os.remove(audio_path)
    up_resp.raise_for_status()
    upload_url = up_resp.json()["upload_url"]

    t_resp = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        json={"audio_url": upload_url, "speech_models": ["universal-3-5-pro", "universal-2"], "language_code": "es"},
        headers={"authorization": key}, timeout=30,
    )
    tid = t_resp.json().get("id")
    if not tid:
        return {"ok": False, "error": f"AssemblyAI no devolvio id: {t_resp.text}"}

    deadline = time.time() + 300
    result = None
    while time.time() < deadline:
        time.sleep(4)
        result = requests.get(f"https://api.assemblyai.com/v2/transcript/{tid}", headers={"authorization": key}, timeout=30).json()
        if result["status"] in ("completed", "error"):
            break
    if not result or result["status"] != "completed":
        return {"ok": False, "error": (result or {}).get("error", "timeout")}

    actual_words_raw = result.get("words", [])
    actual_norm = [_norm_word(w["text"]) for w in actual_words_raw]
    expected_norm = [_norm_word(w["text"]) for w in expected_words]

    sm = difflib.SequenceMatcher(a=expected_norm, b=actual_norm, autojunk=False)
    ratio = sm.ratio()

    problems = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete") and i2 > i1:
            expected_span = " ".join(w["text"] for w in expected_words[i1:i2])
            actual_span = " ".join(w["text"] for w in actual_words_raw[j1:j2]) if j2 > j1 else "(no se detecto nada aca)"
            approx_ms = expected_words[i1]["startMs"]
            problems.append({
                "approx_new_timestamp_s": round(approx_ms / 1000, 2),
                "se_esperaba": expected_span,
                "se_transcribio": actual_span,
            })

    gap_anomalies = []
    if max_gap_ms is not None:
        threshold_ms = max(max_gap_ms * 2, 800)
        for i in range(len(actual_words_raw) - 1):
            gap_ms = actual_words_raw[i + 1]["start"] - actual_words_raw[i]["end"]
            if gap_ms > threshold_ms:
                gap_anomalies.append({
                    "approx_new_timestamp_s": round(actual_words_raw[i]["end"] / 1000, 2),
                    "gap_ms": round(gap_ms),
                    "entre": f"\"{actual_words_raw[i]['text']}\" -> \"{actual_words_raw[i + 1]['text']}\"",
                })

    return {"ok": True, "match_ratio": round(ratio, 4), "problems": problems[:20], "gap_anomalies": gap_anomalies[:20]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--transcript", required=True, help="AssemblyAI transcript JSON (needs a top-level 'words' array)")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--target-duration-s", type=float, default=None, help="If set and the video is still longer than this after removing pauses, speed it up uniformly to hit it")
    ap.add_argument("--max-pause-ms", type=int, default=DEFAULT_MAX_PAUSE_MS, help=f"Pauses longer than this get cut down to this (default {DEFAULT_MAX_PAUSE_MS}ms) -- not to zero, a natural breath is kept")
    ap.add_argument("--extra-cuts", default=None, help="Path to a JSON file: [{\"start_s\": .., \"end_s\": ..}, ...] -- explicit spans to excise (e.g. a misspoken word), on top of pause removal")
    ap.add_argument("--verify", action="store_true", help="Re-transcribe the tightened output and diff it against the expected words to catch cuts that clipped into speech (needs ASSEMBLYAI_KEY, costs one extra transcription call). Strongly recommended -- a visual/waveform check alone can't tell you if the result is still intelligible.")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.transcript) as f:
        transcript = json.load(f)
    words = transcript["words"]

    video_duration_s = get_duration(args.video)
    keep_segments = build_keep_segments(words, video_duration_s, args.max_pause_ms)
    if args.extra_cuts:
        with open(args.extra_cuts) as f:
            extra = [(c["start_s"], c["end_s"]) for c in json.load(f)]
        keep_segments = apply_extra_cuts(keep_segments, extra)
        print(f"Aplicados {len(extra)} corte(s) explicito(s) adicional(es): {extra}")
    kept_duration_s = sum(e - s for s, e in keep_segments)
    removed_s = video_duration_s - kept_duration_s

    speed_factor = 1.0
    if args.target_duration_s and kept_duration_s > args.target_duration_s:
        speed_factor = round(kept_duration_s / args.target_duration_s, 4)
        speed_factor = min(speed_factor, 1.5)  # don't let it get chipmunk-y past 1.5x

    print(f"Duracion original: {video_duration_s:.1f}s")
    print(f"{len(keep_segments)} segmentos de habla, {removed_s:.1f}s de silencio recortado (pausas > {args.max_pause_ms}ms)")
    print(f"Duracion tras cortar silencios: {kept_duration_s:.1f}s")
    if speed_factor != 1.0:
        print(f"Todavia por encima del objetivo ({args.target_duration_s}s) -- aplicando velocidad x{speed_factor}")
    final_duration_s = kept_duration_s / speed_factor
    print(f"Duracion final estimada: {final_duration_s:.1f}s")

    out_path = os.path.join(args.output_dir, "tightened.mp4")
    source_fps = get_fps(args.video)
    print(f"Recortando y re-codificando a {source_fps:.3f}fps constante (puede tardar un par de minutos)...")
    run_ffmpeg_trim_concat_speed(args.video, keep_segments, speed_factor, out_path, source_fps)

    remap = remap_time_fn(keep_segments, speed_factor)
    remapped_words = []
    for w in words:
        new_start = remap(w["start"] / 1000) * 1000
        new_end = remap(w["end"] / 1000) * 1000
        if new_end <= new_start:
            continue  # word fell entirely inside a trimmed pause -- shouldn't happen, but skip defensively
        remapped_words.append({"text": w["text"], "startMs": round(new_start), "endMs": round(new_end)})

    captions_path = os.path.join(args.output_dir, "captions_remapped.json")
    with open(captions_path, "w") as f:
        json.dump(remapped_words, f, indent=2, ensure_ascii=False)

    report = {
        "video_original": args.video,
        "duration_original_s": round(video_duration_s, 2),
        "duration_after_silence_cut_s": round(kept_duration_s, 2),
        "silence_removed_s": round(removed_s, 2),
        "speed_factor": speed_factor,
        "duration_final_s": round(final_duration_s, 2),
        "n_keep_segments": len(keep_segments),
        "tightened_video": out_path,
        "captions_remapped": captions_path,
    }
    with open(os.path.join(args.output_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nVideo final: {out_path}")
    print(f"Captions remapeadas ({len(remapped_words)} palabras): {captions_path}")
    print(
        "\nIMPORTANTE: cualquier timestamp de b-roll (atMs) que hayas calculado sobre "
        "la transcripcion ORIGINAL ya no es valido -- recalcula los slots de b-roll "
        "usando captions_remapped.json, no el transcript original."
    )

    if args.verify:
        key = get_assemblyai_key()
        if not key:
            print("\n--verify pedido pero falta ASSEMBLYAI_KEY -- salteando la verificacion.", file=sys.stderr)
        else:
            print("\nVerificando el resultado (re-transcribiendo el video recortado)...")
            expected_max_gap_ms = args.max_pause_ms / speed_factor
            v = verify_tightened_output(out_path, remapped_words, key, max_gap_ms=expected_max_gap_ms)
            if not v["ok"]:
                print(f"Verificacion fallo: {v['error']}", file=sys.stderr)
            else:
                print(f"Coincidencia con lo esperado: {v['match_ratio']*100:.1f}%")
                if v["problems"]:
                    print(f"\n{len(v['problems'])} tramo(s) sospechoso(s) -- revisa estos puntos a mano (mira el frame con timeline_check.py y decidi si el corte quedo mal):")
                    for p in v["problems"]:
                        print(f"  [{p['approx_new_timestamp_s']}s] se esperaba \"{p['se_esperaba']}\" -> se transcribio \"{p['se_transcribio']}\"")
                else:
                    print("Sin tramos sospechosos -- el audio recortado se transcribe igual a lo esperado.")
                if v["gap_anomalies"]:
                    print(f"\nALERTA: {len(v['gap_anomalies'])} hueco(s) de silencio anormalmente grande(s) en el resultado ya recortado (esto pasa el diff de texto de arriba porque las PALABRAS son correctas -- es un problema de TIMESTAMPS del transcript original, no de texto. Ver 'KNOWN FAILURE MODE' en este script):")
                    for g in v["gap_anomalies"]:
                        print(f"  [~{g['approx_new_timestamp_s']}s] hueco de {g['gap_ms']}ms entre {g['entre']} (se esperaba <= ~{expected_max_gap_ms:.0f}ms)")
                    print("  Diagnostico: extrae con ffmpeg una copia SIN cortar/acelerar del tramo original sospechoso y re-transcribila sola -- esa transcripcion aislada es la referencia real para el timestamp de inicio de la palabra siguiente.")


if __name__ == "__main__":
    main()
