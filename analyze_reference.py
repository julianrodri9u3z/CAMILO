#!/usr/bin/env python3
"""
Ingests ONE reference ad (an example the user says worked well) and extracts
the objective, measurable side of its editing style: cut timing/rhythm (via
ffmpeg scene detection -- deterministic, no API needed) and, optionally, a
TwelveLabs read of the qualitative side (transition types, caption look,
music mood/genre, b-roll usage, color grading).

This script deliberately does NOT decide what the style "is" -- it only
measures and extracts raw material. Claude looks at the extracted frames +
the TwelveLabs text (or the frames alone if there's no TWELVELABS_KEY) and
writes the actual judgment calls into a small delta JSON, which the
`update-profile` subcommand then merges into references/estilos/<style>.json
as a running (not overwritten) profile -- same "script measures, Claude
judges" split used by the analizar-anuncios-meta skill.

Usage:
    python3 analyze_reference.py metrics --video ad.mp4 --output-dir out/
    python3 analyze_reference.py twelvelabs --video ad.mp4 --output-dir out/
    python3 analyze_reference.py update-profile --style tiktok --delta delta.json
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

import requests

import bcc_env  # keys live in ~/.bcc-toolkit/.env (they survive plugin updates); the skill's own .env is still honoured
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = bcc_env.ENV_PATH   # messages point at the persistent file
ESTILOS_DIR = os.path.join(SKILL_DIR, "references", "estilos")

SCENE_THRESHOLD = 0.35  # ffmpeg scene score above which a frame counts as a cut
MAX_NOTAS = 10  # cap on free-text notes kept per style profile

PROMPT_EDICION = """Você descreve a EDICAO de um anuncio em video, nao a fala nem o produto.
Devolva EXATAMENTE nesta estrutura, em espanhol, sem nada alem dela:

RITMO DE CORTE: sensacao geral de velocidade (lento/medio/rapido) e se o ritmo muda ao longo do video (ex: comeca lento e acelera no final).

TRANSICOES: tipos de transicao usados entre planos -- corte seco, crossfade, whip pan, zoom, deslizamento, match cut, etc. Um por linha comecando com "- ", com aproximadamente quantas vezes aparece cada um.

SUBTITULOS: existem? (sim/nao). Se sim: estilo (palavra por palavra tipo karaoke vs frase completa), posicao na tela, fonte (fina/grossa), cor do texto, cor de destaque se houver, animacao (fade, pop, bounce).

MUSICA: genero ou vibe percebida (ex: cinematic score, pop synth, lo-fi, trap trend de TikTok), energia (baixa/media/alta), se muda de intensidade acompanhando o video, se os cortes parecem sincronizados com a batida.

B-ROLL: ha planos de apoio/insercao (nao o falante principal)? frequencia aproximada (baixa/media/alta) e que tipo de imagem (produto, mãos, lugares, texturas, telas de celular).

COLOR GRADING: impressao geral de cor -- saturado/dessaturado, quente/frio, contraste alto/baixo, algum estilo reconhecivel (cinematografico, natural tipo iPhone, vibrante tipo TikTok).
"""


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


def get_key(name, help_url):
    key = os.environ.get(name)
    if not key:
        key = load_env_file(ENV_FILE).get(name)
    if not key or key.startswith("pega-aqui"):
        print(
            f"{name} no esta configurada. Abre {ENV_FILE} y agrega:\n  {name}=tu-clave\n"
            f"(consiguela en {help_url})",
            file=sys.stderr,
        )
        return None
    return key


def check_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"{tool} no esta instalado o no esta en PATH (brew install ffmpeg).", file=sys.stderr)
            sys.exit(1)


def get_duration(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video],
        capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def detect_cuts(video, threshold=SCENE_THRESHOLD):
    """Runs ffmpeg scene-change detection and returns sorted cut timestamps (s)."""
    result = subprocess.run(
        ["ffmpeg", "-i", video, "-vf", f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    cuts = [float(m) for m in re.findall(r"pts_time:([\d.]+)", result.stderr)]
    return sorted(set(round(c, 2) for c in cuts))


def extract_cut_frames(video, cuts, frames_dir):
    os.makedirs(frames_dir, exist_ok=True)
    for i, t in enumerate(cuts):
        for label, offset in (("before", -0.12), ("at", 0.02), ("after", 0.2)):
            ts = max(0.0, t + offset)
            dest = os.path.join(frames_dir, f"cut{i:02d}_{label}.jpg")
            subprocess.run(
                ["ffmpeg", "-y", "-ss", str(ts), "-i", video, "-frames:v", "1", dest],
                capture_output=True,
            )


def run_metrics(args):
    check_ffmpeg()
    os.makedirs(args.output_dir, exist_ok=True)

    duration = get_duration(args.video)
    cuts = detect_cuts(args.video, threshold=args.threshold)
    boundaries = [0.0] + cuts + [duration]
    shot_durations = [round(b - a, 2) for a, b in zip(boundaries, boundaries[1:]) if b - a > 0.05]

    frames_dir = os.path.join(args.output_dir, "cut_frames")
    extract_cut_frames(args.video, cuts, frames_dir)

    audio_path = os.path.join(args.output_dir, "audio.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", args.video, "-vn", "-acodec", "libmp3lame", audio_path],
        capture_output=True,
    )

    metrics = {
        "video": args.video,
        "duration_s": round(duration, 2),
        "cut_timestamps_s": cuts,
        "shot_durations_s": shot_durations,
        "cuts_per_min": round(len(cuts) / (duration / 60), 1) if duration > 0 else 0,
        "median_shot_s": sorted(shot_durations)[len(shot_durations) // 2] if shot_durations else duration,
        "cut_frames_dir": frames_dir,
        "audio_path": audio_path,
    }
    metrics_path = os.path.join(args.output_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Duracion: {duration:.1f}s -- {len(cuts)} cortes detectados -- {metrics['cuts_per_min']} cortes/min -- plano mediano {metrics['median_shot_s']}s")
    print(f"Frames de cada corte (before/at/after) en: {frames_dir}")
    print(f"Audio extraido en: {audio_path}")
    print(f"metrics.json: {metrics_path}")
    print(
        "\nSiguiente paso: mira los frames de cut_frames/ para juzgar el TIPO de "
        "transicion (si 'before' y 'at' se ven mezclados -> crossfade/gradual; si "
        "son completamente distintos -> corte seco). Para musica/subtitulos/color, "
        "corre el subcomando 'twelvelabs' si hay clave, o inspecciona los frames a ojo."
    )
    print(
        "\nESTO ES UN HEURISTICO, no una medicion exacta: la deteccion de escenas de "
        "ffmpeg puede fallar en videos con edicion muy sutil (crossfades largos) o "
        "sobre-contar con mucho movimiento de camara. Si el numero de cortes no "
        "cuadra con lo que ves al mirar el video, ajusta --threshold (mas bajo = "
        "mas sensible, detecta mas cortes; mas alto = menos sensible) y vuelve a "
        "correr -- no reportes estos numeros como si fueran exactos sin chequearlos."
    )


def get_or_create_index(H, B, index_name):
    existing = requests.get(f"{B}/indexes", headers=H, params={"index_name": index_name}).json()
    for idx in existing.get("data", []):
        if idx["index_name"] == index_name:
            return idx["_id"]
    created = requests.post(
        f"{B}/indexes", headers=H,
        json={"index_name": index_name, "models": [{"model_name": "marengo3.0", "model_options": ["visual", "audio"]}]},
    )
    created.raise_for_status()
    return created.json()["_id"]


def run_twelvelabs(args):
    key = get_key("TWELVELABS_KEY", "twelvelabs.io")
    if not key:
        print("Sin TWELVELABS_KEY -- salta este paso y juzga a ojo con los frames de 'metrics'.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    H = {"x-api-key": key}
    B = "https://api.twelvelabs.io/v1.3"

    index_id = get_or_create_index(H, B, "editar-anuncios")

    with open(args.video, "rb") as f:
        task = requests.post(f"{B}/tasks", headers=H, data={"index_id": index_id}, files={"video_file": f})
    task.raise_for_status()
    task_id = task.json()["_id"]

    print("Subiendo y procesando en TwelveLabs (puede tardar unos minutos)...")
    video_id = None
    deadline = time.time() + 600
    while time.time() < deadline:
        status = requests.get(f"{B}/tasks/{task_id}", headers=H).json()
        if status.get("status") == "ready":
            video_id = status["video_id"]
            break
        if status.get("status") == "failed":
            print(f"TwelveLabs fallo al procesar el video: {status}", file=sys.stderr)
            sys.exit(1)
        time.sleep(8)

    if not video_id:
        print("Timeout esperando a TwelveLabs.", file=sys.stderr)
        sys.exit(1)

    vinfo = requests.get(f"{B}/indexes/{index_id}/videos/{video_id}", headers=H)
    vinfo.raise_for_status()
    asset_id = vinfo.json().get("asset_id", video_id)

    resp = requests.post(
        f"{B}/analyze", headers=H,
        json={
            "model_name": "pegasus1.5",
            "video": {"type": "asset_id", "asset_id": asset_id},
            "prompt_v2": {"input_text": PROMPT_EDICION},
            "temperature": 0.2,
            "stream": False,
        },
        timeout=300,
    )
    resp.raise_for_status()
    text = resp.json().get("data", "")

    out_path = os.path.join(args.output_dir, "analysis.txt")
    with open(out_path, "w") as f:
        f.write(text)
    print(f"Analisis de edicion/musica guardado en: {out_path}")


def _merge_numeric_mean(profile, key, new_value, n_before):
    prev = profile.get(key)
    if prev is None:
        profile[key] = round(new_value, 2)
    else:
        profile[key] = round((prev * n_before + new_value) / (n_before + 1), 2)


def _merge_tally(profile, key, new_items):
    tally = profile.setdefault(key, {})
    for item in new_items or []:
        tally[item] = tally.get(item, 0) + 1


def run_update_profile(args):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.style):
        print("--style must be lowercase words joined by dashes (e.g. trailer-documental).", file=sys.stderr)
        sys.exit(1)
    os.makedirs(ESTILOS_DIR, exist_ok=True)
    profile_path = os.path.join(ESTILOS_DIR, f"{args.style}.json")

    if os.path.isfile(profile_path):
        with open(profile_path) as f:
            profile = json.load(f)
    else:
        profile = {"style": args.style, "n_ejemplos_analizados": 0, "transiciones_observadas": {}, "generos_musica_observados": {}, "notas_libres": []}

    with open(args.delta) as f:
        delta = json.load(f)

    n_before = profile.get("n_ejemplos_analizados", 0)

    for numeric_key in ("shot_duration_s", "cuts_per_min", "broll_ratio", "music_bpm_estimate", "transition_duration_ms"):
        if numeric_key in delta:
            _merge_numeric_mean(profile, numeric_key, delta[numeric_key], n_before)

    if "transition_types" in delta:
        _merge_tally(profile, "transiciones_observadas", delta["transition_types"])
    if "music_genre" in delta:
        _merge_tally(profile, "generos_musica_observados", delta["music_genre"])

    for note_key in ("caption_style_notes", "color_grading_notes", "broll_type_notes", "free_note"):
        if delta.get(note_key):
            entry = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] {delta[note_key]}"
            notas = profile.setdefault("notas_libres", [])
            notas.append(entry)
            profile["notas_libres"] = notas[-MAX_NOTAS:]

    profile["n_ejemplos_analizados"] = n_before + 1
    profile["ultima_actualizacion"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    print(f"Perfil actualizado ({profile['n_ejemplos_analizados']} ejemplo(s) analizados en total): {profile_path}")
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    print(
        "\nRecuerda tambien actualizar references/estilos/"
        f"{args.style}.md a mano con lo aprendido de este ejemplo (el JSON es "
        "el estado maquina, el .md es la guia legible que usas al editar)."
    )


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("metrics", help="Heuristic cut/rhythm extraction via ffmpeg scene detection (no API key needed)")
    p1.add_argument("--video", required=True)
    p1.add_argument("--output-dir", required=True)
    p1.add_argument("--threshold", type=float, default=SCENE_THRESHOLD, help=f"ffmpeg scene-score threshold (default {SCENE_THRESHOLD}); lower = more sensitive")
    p1.set_defaults(func=run_metrics)

    p2 = sub.add_parser("twelvelabs", help="Qualitative editing+music read via TwelveLabs (optional, needs TWELVELABS_KEY)")
    p2.add_argument("--video", required=True)
    p2.add_argument("--output-dir", required=True)
    p2.set_defaults(func=run_twelvelabs)

    p3 = sub.add_parser("update-profile", help="Merge a learning delta into references/estilos/<style>.json")
    p3.add_argument("--style", required=True, help="Style slug (lowercase-with-dashes). Any existing references/estilos/<style>.json, or a NEW slug to create a fresh profile (e.g. trailer-documental) -- styles are open-ended, not a closed list")
    p3.add_argument("--delta", required=True, help="Path to a small JSON with this example's observations")
    p3.set_defaults(func=run_update_profile)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
