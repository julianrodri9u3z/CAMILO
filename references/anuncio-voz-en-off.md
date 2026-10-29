# Anuncio con voz en off completa sobre avatares, b-roll y motion graphics

Receta probada (2026-10, anuncio de 92 s con 6 avatares de IA, demo de clonación de video y tarjetas de motion). Sirve para cualquier
anuncio donde NADIE habla a cámara: una narración (TTS) cubre imágenes que se cortan al ritmo de cada frase.

## Orden de trabajo
1. **Guion** (adaptar-referencias, o el GPT de copy del usuario). Frases cortas para leerse en voz alta; ≈ 2,3 palabras/s.
2. **Narración**: ElevenLabs (`video-ads-avatar/scripts/elevenlabs_voice.py generate-speech`, voz de la biblioteca o clonada) en UNA sola llamada;
   luego `ffmpeg -af "atempo=1.08,loudnorm=I=-16:TP=-1.5:LRA=7"` (más ágil sin sonar acelerada). Transcribe con AssemblyAI para tener la hora de cada palabra.
3. **Storyboard por frase** (tabla tiempo → imagen). La imagen cambia con la frase: lista que se tacha cuando se nombra cada dolor, ranking cuando dice «por relevancia»…
4. **Materiales**
   - Personas: `video-ads-avatar` → fotos (`generate-image --model gpt-image-2.5-flare`), `animate_avatar.py` (clips mudos), `clone_video.py` (mismo video, otros avatares).
   - b-roll: texto→video con Veo 3.1 fast (~US$0,08/8 s) da mejor look que stock. Si usas stock de Pexels, `fetch_broll.py` ya pide la versión de ≥1900 px de alto.
   - Tarjetas: `make_hf_card.py` (bloques HyperFrames) — usa `--speed`/`--squeeze`.
5. **Base visual**: un solo mp4 1080×1920@30 cuyo audio es la narración. Cada tramo se renderiza con ffmpeg a un número EXACTO de fotogramas
   (`round(t1*30)-round(t0*30)`) y se concatena; así los cortes caen en la palabra. Esa base es el único `clip` del EditPlan.
6. **EditPlan sobre la base**: subtítulos de la narración (`captionBottomPx: 250` los baja para no pisar tarjetas), etiquetas de función
   (`keywordCallouts`), flashes/zoom en los cortes (`pulses`), SFX en cada evento, música con `musicOffsetSeconds` NEGATIVO (= retrasa la música) para que sus
   caídas (`beat_grid.py` las lista) caigan en los momentos fuertes, y `cta` final.
7. `vision_analyze.py --no-png` sobre toda la base (zonas para `dodge_captions.py --bottom-px 250`) y matte solo en la ventana del texto detrás de la persona
   (elige un tramo donde la cabeza tenga aire arriba; con brazos levantados la caja de persona llega al borde y el script lo rechaza). → render → `finalize.py` → `qa_render.py`.

## Trucos que ahorran horas
- **ffmpeg de Mac/Windows a veces no trae `drawtext`**: los textos de las animaciones compuestas van como capas PNG hechas con PIL (fuente Anton) y se superponen con `overlay`.
- **Pantalla dividida original/clon**: dos tiles 540×960 centrados (etiquetas arriba y abajo), el clon cambia de avatar sin reiniciar el tiempo del original; al final, cuadrícula 2×2 de clones.
- **Muro de avatares en vivo**: tiles que entran escalonados (`fade ... alpha=1`) + `showwaves` de la narración real como onda de voz.
- **Mosaico de tarjetas** (2×2) que aparecen cada una en su palabra («un paso, una cuenta, un chat, una notificación»): rellena los cuadrantes vacíos con caras oscurecidas y desenfocadas; nunca dejes un fotograma negro (`qa_render.py` lo marca).
- **Tarjeta opaca sobre b-roll**: `blend=all_mode=screen` con el b-roll oscurecido (`eq=brightness=-0.32`) hace que solo se vea el texto de la tarjeta.
- Una tarjeta por frase; si la voz nombra cosas rápido (cada 0,6 s) no hagas una tarjeta por palabra: haz una sola con tres ítems acelerada (`--speed 1.7`).
- Revisa SIEMPRE una hoja de contactos (un fotograma cada 2,5 s) y la transcripción del audio final (confianza AssemblyAI ≥ 0,98).
