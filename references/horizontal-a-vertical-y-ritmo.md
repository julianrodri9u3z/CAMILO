# Horizontal → vertical y ediciones dirigidas por la música

Probado el 2026-10-06 con un clip de podcast horizontal (1556×720, un solo plano continuo de ~5 min con música encima y sin voz).

## 1. Reencuadre inteligente (cámara virtual)

1. `python3 scripts/prepare_source.py --video raw.mp4 --out remotion/public/jobs/<slug>/raw.mp4` (H.264, obligatorio).
2. `python3 scripts/vision_analyze.py --video raw.mp4 --out DIR --start S --dur D --no-png` — solo cajas de persona/cara/manos (`zones.json`), sin imágenes de máscara: rápido y liviano. Mismo comando en Mac (Apple Vision) y Windows/Linux (MediaPipe).
3. Detectar los cortes de cámara del original: `ffmpeg -i raw.mp4 -vf "select='gt(scene,0.15)',showinfo" -an -f null -` (anotar los `pts_time`).
4. `python3 scripts/make_reframe.py --zones DIR/zones.json --out reframe.json --cuts <cortes>` — la cámara sigue la cara, solo se mueve cuando la persona sale de una zona muerta central y suaviza (~0.7 s); en los cortes de cámara del original salta de golpe. Se incorpora al plan como `plan["reframe"]`.
En Remotion el video se muestra a la escala "cover" × `z` × `clip.zoom`, con el punto de foco en (50 %, 40 %) del cuadro y sin mostrar nunca fuera del original.

**Límite de calidad:** un 720p recortado a vertical se amplía ~2.7×; con zoom 1.3 se amplía ~3.5× y se nota blando. Limitar el zoom a ≤ 1.3 y pedir la fuente en mayor resolución si existe. El grano ayuda a disimularlo.

## 2. Edición dirigida por la música (`make_beat_edit.py`)

`python3 scripts/beat_grid.py --audio raw.mp4 --out beats.json` y luego
`python3 scripts/make_beat_edit.py --src jobs/<slug>/raw.mp4 --beats beats.json --reframe reframe.json --start 0 --end <t> --cuts <cortes> --out job.json`

- **Multicámara desde un plano:** cortes en los pulsos con niveles de zoom rotativos (1.0, 1.15, 1.28…); el tiempo del original NO se salta (la música es su propio audio y queda continua).
- **Ritmo según energía:** intro calmada = segmentos largos; la subida = empuje lento; el **drop** = corte exacto sobre el golpe de graves + destello + temblor + impacto + riser; después del drop un corte por compás, cada 2 pulsos en lo más intenso.
- **Pulsos** (`plan.pulses`): zoom en cada pulso (más fuerte en el tiempo fuerte) solo cuando la música es enérgica; `flash`/`shake` en los drops.
- **Sonido:** riser hacia el drop, golpe en el drop, whooshes suaves en algunos cortes.
- **Look:** contraste/saturación/temperatura/grano (`grade`) + viñeta.
- **No inventa texto**: un clip con música y sin voz no tiene nada que subtitular; poner frases en boca de alguien sería inventar. Si hay voz, usar el flujo normal de subtítulos.
- La ventana se elige en un tiempo fuerte (compás) para que termine en limpio; el audio del original se masteriza con `finalize.py` (~-14 LUFS).

## 3. Cuándo usar qué

- Video hablado: flujo normal (subtítulos cinéticos, énfasis, b-roll real, SFX).
- Video de música (edits, motivacional, montaje): este flujo.
- Siempre: `qa_render.py` antes de entregar y recordar al usuario que el audio/música de terceros puede reclamarse al publicar.
