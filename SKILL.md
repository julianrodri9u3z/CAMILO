---
name: editar-anuncios
description: Edita cualquier video crudo (footage propio, clips generados con video-ads-avatar, grabaciones UGC) convirtiéndolo en un anuncio terminado en uno de varios estilos/formatos aprendidos — Cinematográfico, UGC con IA, TikTok, Chisme, Podcast, Voz en Off UGC — usando Remotion como motor de render headless (sin abrir CapCut ni ninguna app). Recorta silencios y ajusta la velocidad para que la duración final quede en rango, transcribe el audio para generar subtítulos animados por palabra, decide el plan de cortes según el ritmo del estilo elegido, busca y descarga automáticamente tomas de apoyo/b-roll (Pexels/Pixabay) según el contenido de la transcripción, busca y descarga música/efectos libres de copyright (Jamendo) o redacta un brief si no hay clave configurada, agrega un CTA final de cuenta regresiva de 5 segundos, y se auto-revisa (frames de cada corte/b-roll/CTA) antes de entregar, corrigiendo lo que note mal. Aprende y refina cada estilo analizando anuncios de referencia que el usuario suba (mide ritmo de corte con ffmpeg, describe transiciones/subtítulos/música/color con TwelveLabs) y fusiona lo aprendido en un perfil por estilo que mejora con cada ejemplo nuevo. Usa esta skill cuando el usuario pida editar, montar, cortar o darle estilo a un video/anuncio ya grabado, pida "convierte este video a estilo TikTok/cinematográfico/UGC/chisme/podcast/voz en off", o suba un anuncio que le funcionó bien y pida que la skill aprenda de él.
---

# Editar Anuncios — motor Remotion + estilos aprendidos

> **OBLIGATORIO antes de cualquier edición: lee y aplica al pie de la letra
> [`references/reglas-de-edicion-antonio.md`](references/reglas-de-edicion-antonio.md)**: volumen 70/30 de
> efectos (−20 a −30 dB bajo la voz), no repetir efectos, cachín en el dinero, música según la emoción,
> solo palabras de peso resaltadas, zona segura, nada sobre los ojos, cifras en verde, b-roll literal y acorde
> al estatus del experto. Si un perfil de estilo o un default choca con esas reglas, **ganan las reglas**.
> Pasa su checklist antes de entregar.

Convierte un video crudo en un anuncio editado, en uno de los estilos/formatos
aprendidos (`cinematografico`, `ugc-ia`, `tiktok`, `chisme`, `podcast`,
`voz-en-off-ugc` — ver `references/estilos/` para la lista viva, se pueden
agregar más -- son abiertos, `update-profile --style <slug-nuevo>` crea uno), usando Remotion (`remotion/`) como motor de render — 100%
headless por CLI, sin depender de una API de CapCut que no existe (ver
contexto en la conversación que originó esta skill: CapCut no ofrece edición
programática pública).

**Caso especial -- añadir un CTA a un video que ya funciona como anuncio:** el flujo completo (transcripción con corte elegido por el usuario, clonación de voz opcional vía ElevenLabs, b-roll de continuidad, y el ensamblaje final que se arma acá) vive en `video-ads-avatar/SKILL.md`, sección "Adding a CTA to an existing video" -- esta skill solo hace el tramo de captions/CTA-outro/render de ese flujo, no lo dispares como un anuncio nuevo desde cero.

## Los estilos son un punto de partida, no una ley -- usa criterio

Los perfiles de `references/estilos/` (`cinematografico`, `ugc-ia`, `tiktok`, `chisme`, `podcast`, `voz-en-off-ugc`, `espiritual-voz-off`, y desde 2026-09-23 `ugc-creador`, `editorial-lifestyle`, `trailer-documental`) (y sus `StyleConfig` en `styles/config.ts`) son el punto de
partida por defecto para ese formato, no un guion que hay que seguir a pie de letra. Antes de armar el
`EditPlan`, mirá el footage/la referencia real que estás emulando y decidí conscientemente qué elementos
de la librería completa (subtítulos, transiciones, y los de motion graphics en
`references/motion-graphics.md`) refuerzan ESE anuncio específico -- aunque eso signifique combinar piezas
de dos estilos, o usar un elemento que ningún perfil trae por defecto todavía (ej. un `revenueChart` en un
`tiktok` si el anuncio es de resultados financieros). Esto es el mismo patrón que `ads-bcc`/`clonar-avatar`
ya usan con sus librerías de referencia: fuente de frases/técnicas probadas, no un contrato que copiar
literal.

Cuando te desvíes de lo que el perfil del estilo dice por defecto, decilo brevemente en el reporte al
usuario ("usé `filmBurn` en vez del `fade` de siempre porque la referencia tenía ese look de corte de
película") -- así la desviación es una decisión visible, no una deriva silenciosa. Si la desviación
funcionó bien y se repite, es candidata a convertirse en el nuevo default del perfil (actualizá el
`.md`/`.json` del estilo, no solo `config.ts`).


> **Anuncio fatigado que solo se quiere resubir con cambios técnicos (metadata, zoom, color, velocidad):** usa `refrescar-anuncio` (`~/.claude/skills/refrescar-anuncio/SKILL.md`). También sirve como paso final después de montar aquí un gancho nuevo.

> **VSLs (videos de venta de más de 6 minutos):** no se editan con esta skill sino con `editar-vsl` (`~/.claude/skills/editar-vsl/SKILL.md`), que usa este mismo motor (composición `Vsl`) y añade estructura por bloques, render por tramos y auditoría.

## Piezas de la skill

- **`remotion/`** — proyecto Remotion con una composición por estilo. Cada una es
  un wrapper fino sobre `src/components/Edit.tsx` parametrizado por
  `src/styles/config.ts`. `Edit.tsx` también agrega, si el EditPlan trae `cta`,
  un outro de cuenta regresiva de 5s (`src/components/CountdownCTA.tsx`) — es
  compartido por todos los estilos, no hay que reimplementarlo por estilo. Ya
  tiene `node_modules/` instalado y fue verificado con renders de humo
  end-to-end (clips + transición + captions + b-roll + música + CTA) — no hace
  falta re-verificar el engine, solo usarlo. La librería de motion graphics
  (`references/motion-graphics.md`) y las transiciones ampliadas también se
  verificaron con un render de humo dedicado en 2026-09 (`--gl=angle` incluido).
- **`references/estilos/<style>.json`** — el perfil aprendido de cada estilo
  (números que el motor usa). Empieza como semilla genérica (`n_ejemplos_analizados: 0`)
  y se refina con cada anuncio de referencia analizado.
- **`references/motion-graphics.md`** — la librería de elementos opcionales que CUALQUIER estilo puede
  usar: stats grandes, badges, flechas, círculos de resaltado, gráfico de facturación animado, viñeta,
  variante de subtítulo en barra, zoom-punch en el clip principal, y transiciones ampliadas. Leela antes
  de armar un `EditPlan` con algo más que subtítulos+b-roll básico.
- **`references/estilos/<style>.md`** — la guía legible del mismo estilo, para tu
  propio juicio al tomar decisiones que el JSON no cubre (qué keywords buscar de
  b-roll, cómo describir la música al usuario, etc.). Actualízala a mano después
  de cada `update-profile`.
- **`scripts/analyze_reference.py`** — ingesta un anuncio de referencia: mide
  ritmo de corte con ffmpeg (determinístico), opcionalmente describe transiciones/
  subtítulos/música/color con TwelveLabs, y fusiona lo aprendido en el perfil.
- **`scripts/tighten_pacing.py`** — recorta silencios entre palabras (usando los
  timestamps de la transcripción, no detección de audio) y, si todavía queda
  largo, acelera video+audio de forma pareja hasta una duración objetivo.
  Devuelve el video recortado MÁS los timestamps de las palabras remapeados a
  la nueva línea de tiempo — cualquier caption/b-roll tiene que calcularse
  DESPUÉS de este paso, nunca antes.
- **`scripts/fetch_broll.py`** — busca y descarga b-roll de Pexels/Pixabay según
  keywords, y lo deja listo dentro de `remotion/public/`.
- **`scripts/enhance_voice.py`** — mejora la voz de grabaciones de celular (EQ, de-esser, compresión en 2 etapas, +6 dB a un limitador; suave reducción de ruido). Validada con números: sube ~14-17 dB un audio muy bajo y la confianza de transcripción de AssemblyAI no baja (0.980 → 0.982). NO quita el eco de un cuarto con paredes duras ni música filtrada: para eso hace falta un aislador de voz con IA (ElevenLabs Voice Isolator / Adobe Podcast), que sube el audio a un servicio externo: ofrecerlo y avisar. Corre antes de transcribir y de armar el plan (usa `--out-video` para obtener el video con la voz limpia).
- **Recorte para quitar texto quemado:** si el video trae un título pegado arriba, `zoomOrigin: "bottom"` con zoom ≥ 1.35 lo saca de cuadro (y se puede poner el título propio con `title`).
- **Tarjetas de motion graphics con HyperFrames** — `python3 scripts/make_hf_card.py list --vertical` / `vars --block <bloque>` / `render --block <bloque> --job <job> --name <n> --vars '{...}' [--speed 1.5 --squeeze --trim 6]` renderiza uno de los ~170 bloques listos (chat de celular, notificaciones, «seguir» de TikTok/IG, respuesta de IA, gráficas, mapas, lower thirds, transiciones) con TUS textos e imágenes y lo deja como `broll` a pantalla completa. Licencia Apache-2.0; solo necesita Node + ffmpeg. Guía y lista de bloques: `references/hyperframes.md`. Además, la skill hermana **`motion-video`** (incluida en el toolkit) trae plantillas propias con `make_card.py`: `steps`, `equation`, `compare`, `hook` (titular de apertura), `phone` (celular 3D con TUS capturas), `cta`, `strike`, `ranking`, `anatomy`, `wall`; se insertan igual como `broll`. Se prepara una vez con su `setup.sh` (ver `motion-video/SKILL.md`).
- **Anuncio con voz en off completa** (nadie habla a cámara: avatares, b-roll y tarjetas cortados al ritmo de una narración) — receta, orden de trabajo y trucos en `references/anuncio-voz-en-off.md`. Usa `captionBottomPx` del EditPlan (distancia de los subtítulos al borde inferior) para bajar los subtítulos cuando hay tarjetas a pantalla completa, y `dodge_captions.py --bottom-px` con el mismo valor.
- **`scripts/env_check.py`** — **córrelo al empezar cualquier sesión de edición**: detecta el sistema operativo y qué funciones están disponibles (edición base, texto detrás de la persona, TikTok, claves) y qué hacer para habilitar las que falten. Planifica solo con lo que diga OK.
- **`scripts/make_reframe.py` + `make_beat_edit.py`** — pasar un video HORIZONTAL a vertical con una cámara virtual que sigue a la persona, y montar ediciones dirigidas por la música (multicámara desde un plano, pulsos al beat, flash/temblor/golpe en el drop). Ver `references/horizontal-a-vertical-y-ritmo.md`.
- **`scripts/prepare_source.py`** — normaliza el video crudo a H.264 con keyframes cortos (obligatorio antes de armar el plan: las fuentes HEVC de TikTok/iPhone producen tramos congelados en el render).
- **`scripts/check_freezes.py`** — detecta imagen congelada en el render final (parte de la auto-revisión).
- **`scripts/fetch_clip_url.py`** — descarga y recorta un clip desde una URL (TikTok, etc.) para usarlo como b-roll real.
- **`references/enriquecimiento-visual.md`** — cómo elegir b-roll con criterio (persona, clips de película, TikTok, noticias, capturas de estudios) en vez de stock genérico.
- **`scripts/vision_analyze.py` + `add_behind_text.py` + `dodge_captions.py`** — texto que pasa DETRÁS de la persona y subtítulos que esquivan caras/manos. **Detecta el sistema solo**: Apple Vision en Mac (nada que instalar) o MediaPipe en Windows/Linux (`vision_setup.py --yes`, ~400 MB, pedir permiso al usuario). **`scripts/beat_grid.py` + `beat_snap.py`** — rejilla de pulsos/drops de la música y alineación numérica de gráficos y del drop con un momento clave. **`scripts/listen_check.py`** — "oídos" (modelo que escucha) para verificar el audio. Ver `references/profundidad-y-ritmo.md`.
- **`scripts/make_sfx.py` / `scripts/add_sfx.py`** — genera una librería de efectos de sonido (whoosh, pop, golpe, ding…) y los coloca solos sobre los eventos del plan (`sfx`). Sin sonido diseñado una edición suena automática.
- **`scripts/match_broll_grade.py`** + campo `grade` del plan — look unificado (contraste, saturación, temperatura, grano) y b-roll igualado al clip principal.
- **`scripts/finalize.py`** — masterizado a -14 LUFS (dos pasadas) + codificación final. **`scripts/qa_render.py`** — puerta de calidad (congelados, negros, clipping, volumen, silencios, legibilidad). Ambos son obligatorios antes de entregar.
- **`scripts/find_tiktok_broll.py`** — busca b-roll real en TikTok por palabra clave (Apify) y arma una hoja de contactos para elegir.
- **`references/gramatica-de-edicion.md`** — los 8 hábitos de una edición que parece humana y las puertas de calidad; **`references/revision-ai-video-editor.md`** — qué se aprovechó del repo ai-video-editor y qué queda pendiente.
- **`scripts/fetch_music.py`** — busca y descarga música libre de copyright y
  de uso comercial permitido desde Jamendo, con manifiesto de atribución
  (artista + licencia). Pexels/Pixabay NO tienen API de música (se investigó y
  confirmó) — Jamendo es la fuente real para esto.
- **`scripts/timeline_check.py`** — genera una imagen con filmstrip de
  miniaturas + forma de onda de audio para una ventana de tiempo dada, usada
  en la auto-revisión (paso 10 de la Parte B) para detectar de un vistazo
  saltos visuales o pops de audio en un punto de corte.
- **Dónde viven las claves (toolkit v1.2.3+):** en un solo archivo persistente, `~/.bcc-toolkit/.env` (Windows: `C:\Users\<usuario>\.bcc-toolkit\.env`), compartido por todas las skills y que **sobrevive a las actualizaciones** del plugin (la carpeta del plugin se reemplaza en cada una). Los scripts también siguen leyendo el `.env` de esta skill. Comprueba con `scripts/env_check.py` (solo dice puesta/falta). Tras una actualización corre `scripts/env_check.py --fix` (reinstala las dependencias del motor).
- **`.env`** — claves: `ASSEMBLYAI_KEY`, `TWELVELABS_KEY` (opcional), `PEXELS_API_KEY`,
  `PIXABAY_API_KEY`, `JAMENDO_CLIENT_ID` (gratis en devportal.jamendo.com — el
  usuario tiene que crear esa cuenta él mismo, Claude no puede crear cuentas),
  `APIFY_TOKEN` (mismo token que ya usan las skills de minería de TikTok, solo
  para `fetch_broll_tiktok.py` -- ver paso 5b).
  Mismo patrón que las otras skills de video: nunca pegues una clave real en el
  chat ni la imprimas — pide al usuario que edite el archivo directamente
  (`open -a TextEdit ~/.claude/skills/editar-anuncios/.env`).

## Regla dura de Remotion (no obvia, rompe el render si se ignora)

Remotion **solo sirve archivos locales desde `remotion/public/`**, referenciados
con rutas relativas vía `staticFile()` — nada de paths absolutos ni `file://`.
Además, el bundler **no seguí symlinks de forma confiable en las pruebas** (un
symlink a un archivo real dio 404 silencioso; una copia real funcionó siempre).
Por eso: **copia siempre los archivos de entrada** (footage crudo, b-roll, música)
dentro de `remotion/public/jobs/<job-slug>/` con `cp`, nunca con `ln -s`, antes de
renderizar. `fetch_broll.py` ya hace esto solo para el b-roll que descarga; para el
video crudo del usuario y para la música, cópialos ahí vos mismo como parte del
paso 4 de abajo.

## Runbook — un proceso en background (tighten_pacing, transcripción) parece colgado

Esto ya pasó varias veces, siempre justo después de un corte de sesión/compactación: el
proceso sigue "vivo" en `ps aux` pero deja de avanzar, con uso de CPU casi nulo durante
varios minutos (compará el CPU time de dos chequeos separados por un minuto -- si no
sube, no está trabajando de verdad). No te quedes esperando indefinidamente:

1. Si es una llamada a AssemblyAI (`--verify`, o cualquier transcripción), el ID de la
   transcripción ya se pidió -- podés consultarlo directo: `GET
   https://api.assemblyai.com/v2/transcript/{id}` con el header `authorization`. Si
   `status: completed`, el resultado ya existe del lado de AssemblyAI, solo que el
   proceso local nunca llegó a leerlo.
2. Si es `tighten_pacing.py` en el paso de extracción de segmentos, revisá cuántos
   `segNNN.mp4` ya existen en `<output-dir>/tightened.mp4.segs_tmp/` -- si el número no
   sube entre dos chequeos, está colgado ahí, no simplemente yendo lento.
3. Matá el proceso y terminá el paso a mano en vez de seguir esperando (por ejemplo,
   completar el concat manualmente si los segmentos ya están, o volver a pedir la
   transcripción si hace falta) -- documentado con más detalle en el runbook
   equivalente de `video-ads-avatar/SKILL.md`.
4. Si matás el proceso mientras escribía un archivo, ese archivo puede quedar corrupto
   (`moov atom not found` en un .mp4) -- verificá con `ffprobe` antes de confiar en él.

## Parte A — Aprender de un anuncio de referencia (opcional pero recomendado)

Hacé esto cada vez que el usuario suba un anuncio que le funcionó bien, indicando
a qué estilo pertenece.

**Banco de referencias del usuario:** `~/Documents/ESTILOS DE EDICIÓN ADS/` tiene ~50 videos de referencia
propios, en dos categorías distintas:
- **`ADS GANADORES 20P/`** mapea 1:1 a los estilos ya nombrados (subcarpetas `FORMATO UGC`,
  `CINEMATOGRAFICO`, `FORMATO CHISME`, `VOZ EN OFF UGC`, `PODCAST`) -- máxima palanca: cada video de acá
  refina directamente un perfil existente vía el flujo de abajo. Priorizalo primero.
- El resto (`ADS ELIDA - GANAR DINERO/`, `ADS GAIA/`, `JUAN CARRIZO/`, y las carpetas `VSL ...`) son por
  campaña/nicho, no por estilo -- útiles sobre todo para escanear técnicas de motion graphics nuevas (ver
  `references/motion-graphics.md`, que ya nació de un escaneo de varias de estas) más que para refinar un
  perfil de estilo puntual. No asumas que un video de acá "es" alguno de los 6 estilos nombrados sin
  mirarlo -- puede no encajar en ninguno limpiamente.

No proceses las ~50 de una sola pasada sin que el usuario lo pida -- es caro en tiempo/créditos de
TwelveLabs. Avisá cuánto cubriste y qué queda pendiente.

1. **Métricas de ritmo (siempre, no necesita clave):**
   ```bash
   python3 ~/.claude/skills/editar-anuncios/scripts/analyze_reference.py metrics \
     --video /ruta/al/anuncio.mp4 --output-dir /tmp/ref-analysis/<nombre>
   ```
   Es un heurístico (detección de escenas de ffmpeg), no una medición exacta —
   el propio script te lo recuerda en su salida. Si el número de cortes no
   coincide con lo que ves al mirar los frames en `cut_frames/`, reintenta con
   `--threshold` más bajo (más sensible) o más alto.

2. **Lectura cualitativa (TwelveLabs, opcional):**
   ```bash
   python3 ~/.claude/skills/editar-anuncios/scripts/analyze_reference.py twelvelabs \
     --video /ruta/al/anuncio.mp4 --output-dir /tmp/ref-analysis/<nombre>
   ```
   Sin `TWELVELABS_KEY`, salta este paso y juzgá vos mismo mirando los frames de
   `cut_frames/` (before/at/after de cada corte) — mismo patrón de fallback que
   `analizar-anuncios-meta`.

3. **Tu propio juicio, por encima de ambas herramientas:** ni ffmpeg ni TwelveLabs
   deciden el estilo — vos sí. Mirá los frames y (si corriste twelvelabs) el
   `analysis.txt`, y armá un delta JSON con lo que realmente observás:
   ```json
   {
     "shot_duration_s": 1.8,
     "cuts_per_min": 32,
     "broll_ratio": 0.25,
     "transition_types": ["hard_cut", "hard_cut", "zoom_punch"],
     "music_genre": ["trap"],
     "caption_style_notes": "palabra por palabra, mayúsculas, resaltado verde lima",
     "color_grading_notes": "alto contraste, algo sobreexpuesto",
     "free_note": "usa freeze-frame justo antes del CTA, 2 de 3 veces"
   }
   ```
   Todos los campos son opcionales — poné solo lo que realmente observaste, nunca
   inventes un número por completar el JSON.

4. **Fusioná al perfil:**
   ```bash
   python3 ~/.claude/skills/editar-anuncios/scripts/analyze_reference.py update-profile \
     --style tiktok --delta /tmp/ref-analysis/<nombre>/delta.json
   ```
   Esto actualiza `references/estilos/tiktok.json` con un promedio corrido (no
   sobrescribe) y te muestra el perfil resultante. Después, **actualizá a mano**
   `references/estilos/tiktok.md` si algo cambió de forma notable frente a lo que
   ya decía.

**Nivel de aprendizaje = cuántos ejemplos hay.** Con 0-1 ejemplos analizados,
tratá el perfil como punto de partida genérico y apoyate en criterio editorial
general. Con 3+ ejemplos del mismo estilo, tratalo como una restricción fuerte —
el objetivo es que el edit nuevo se parezca lo más posible a esos ejemplos
reales, no a una idea genérica de "cinematográfico". Decíselo al usuario: cuantos
más anuncios de referencia suba por estilo, más fiel será el resultado.

## Parte B — Editar un video nuevo

### 1. Reunir datos (en el chat)

- El **video crudo** (ruta local).
- El **estilo**: uno de los que existan en `references/estilos/` (preguntá si
  no está claro).
- Un **nombre corto de job** (slug sin espacios, ej. `lanzamiento-agosto`).
- **Duración objetivo**, si el video crudo es largo (más de ~2 min): el
  promedio real de los anuncios ganadores del usuario para funnels de venta
  vía WhatsApp/contribución ronda **1:45 (105s)** — usalo como default si el
  usuario no da un número, pero decilo explícitamente en vez de asumirlo en
  silencio.

### 2. Transcribir con timestamps por palabra (AssemblyAI)

Mismo servicio y patrón de claves que `analizar-anuncios-meta` (env var →
`.env` de esta skill → preguntar al usuario si no está en ningún lado).
AssemblyAI devuelve un array `words` con `text`/`start`/`end` en ms.

**La API de AssemblyAI cambió su formato de parámetros** (detectado en
producción): el campo `speech_model` (string) fue reemplazado por
`speech_models` (lista) -- usar `{"speech_models": ["universal-3-5-pro", "universal-2"], "language_code": "es"}`
al crear el transcript. Si un día esto vuelve a fallar con un 400, leé el
mensaje de error de la API primero -- suelen decir exactamente qué parámetro
cambió, no asumas que el código viejo sigue valiendo.

Reglas de calidad de la transcripción (las mismas que ya usás en
`analizar-anuncios-meta`): `confidence` bajo → reintentar con
`language_detection`; nunca inventar una palabra que no se entendió.

### 3. Recortar silencios y ajustar la duración

**Casi siempre corresponde este paso** para footage crudo (no tanto para clips
ya cortos de `video-ads-avatar`). Corre siempre con `--verify`:

```bash
python3 ~/.claude/skills/editar-anuncios/scripts/tighten_pacing.py \
  --video /ruta/al/video-crudo.mp4 --transcript /tmp/ref-analysis/<slug>/transcript.json \
  --output-dir /tmp/ref-analysis/<slug>/tightened --target-duration-s 105 --verify
```

Esto (a) recorta las pausas más largas que `--max-pause-ms` (default 450ms,
dejando una pausa natural, no cero) y (b) si todavía queda por encima del
objetivo, acelera video+audio parejo -- con un tope de 1.5x para no degradar
la voz demasiado.

**KNOWN FAILURE MODE -- desincronización progresiva de audio/video (ya
corregido, pero verificar si reaparece):** el recorte por segmentos usa
`setpts=PTS/speed_factor`, que no cae en una grilla de frames limpia con un
`speed_factor` fraccionario -- sin forzar un frame rate constante de salida,
cada segmento termina en VFR (frame rate variable). Al concatenar muchos
segmentos VFR, el error de timing se acumula de forma invisible hasta que,
bien entrado el video, el audio se nota corrido respecto al video (caso
real: perfecto al inicio, corrido audible al ~75% de un video de 27 clips).
El script ya fuerza `-r <fps de la fuente>` tanto por segmento como en el
concat final -- si el síntoma vuelve a aparecer, es la primera pista a
revisar (`ffprobe -show_entries stream=r_frame_rate,avg_frame_rate` en el
`tightened.mp4`: si difieren, es VFR).

**A partir de acá, el video de trabajo es `tightened.mp4` y
las captions son `captions_remapped.json`, no el archivo/transcripción
original** -- son otra línea de tiempo.

**KNOWN FAILURE MODE -- concatenar dos fuentes con distinto sample rate de audio desincroniza todo, no solo un poco.** Caso real: se unió un video original (audio a 44100Hz) con un tramo renderizado por Remotion (audio a 48000Hz, el default del motor) usando el demuxer `concat` de ffmpeg -- el resultado reportaba video y audio con duraciones que diferían por más de 10 segundos en un archivo de ~3 minutos (el demuxer no resamplea, solo concatena streams; con sample rates distintos el segundo tramo se interpreta a la velocidad equivocada). Señal para detectarlo: `ffprobe -show_entries stream=codec_type,duration` en el archivo final -- si el stream de audio y el de video difieren en más de ~1s, es esto. Fix: antes de concatenar CUALQUIER par de fuentes de distinto origen (footage crudo + render de Remotion, o dos renders con configs distintas), forzá el mismo `-ar` (sample rate) en el re-encode de cada tramo -- `-ar 48000` en ambos, por ejemplo -- y solo entonces corré el concat.

**`--verify` es obligatorio, no opcional.** Feedback real de un usuario: con
un video de 3+ min, un recorte que a nivel de imagen/audio se veía perfecto
(sin saltos ni pops en `timeline_check.py`) igual dejó "muchas palabras que
no se entienden" -- la revisión visual no alcanza para detectar esto, porque
un corte puede estar técnicamente limpio (sin invadir el límite de una
palabra) y aun así el resultado sonar atropellado. `--verify` re-transcribe
`tightened.mp4` y compara contra las palabras que se esperaba conservar --
esa comparación SÍ detecta el problema (en el caso real: 94.4% de coincidencia,
20 tramos sospechosos, varios con la palabra directamente ausente de la
transcripción del resultado). Al leer el reporte:
- Diferencias de formato de número ("250 mil" vs "250,000") son ruido de
  normalización de AssemblyAI, no un problema real -- ignoralas.
- Un "(no se detecto nada aca)" frente a una palabra esperada SÍ es señal
  real de que ese corte dañó el audio -- investigalo con
  `timeline_check.py --at-s <el timestamp que imprime>` y, si hace falta,
  volvé a correr con `--max-pause-ms` más alto (menos agresivo) o bajá el
  `--target-duration-s` para necesitar menos velocidad.

Si el video sigue largo tras el tope de 1.5x (pasa con footage muy extenso,
ej. un guion de +3 min), decíselo al usuario con números concretos (cuánto
silencio se recortó, a qué velocidad llegó, cuánto falta) en vez de forzarlo
en silencio -- la solución real ahí es recortar contenido del guion, no
estirar más la velocidad.

Si el usuario compartió un repo propio para esto, evalualo y considerá si
conviene usarlo en vez de o junto con este script -- no lo ejecutes a ciegas
sin mirar qué hace primero.

### 4. Decidir el plan de cortes

Con `captions_remapped.json` (paso 3) y el perfil del estilo elegido
(`references/estilos/<style>.json`):
- Si el video crudo ya está bien ritmado (ej. viene de `video-ads-avatar`, clips
  cortos por diseño), puede bastar con **un solo `clip`** cubriendo todo el
  archivo — el ritmo del estilo entonces lo aporta el b-roll y las transiciones,
  no recortes internos.
- Si el video es un solo take largo (grabación cruda de UGC), lo normal es
  seguir usando **un solo `clip`** que cubra todo `tightened.mp4` (ya viene sin
  huecos raros) y lograr el ritmo del estilo con la DENSIDAD de b-roll (paso 5),
  no cortando el mismo plano en fragmentos artificiales -- cortar en pedazos la
  misma toma de una sola cámara se ve raro; el b-roll es lo que aporta variedad
  visual real.

### 5. B-roll automático

> **Antes de buscar stock, lee `references/enriquecimiento-visual.md`**: preferir material real (la persona, clips de película, TikTok, noticieros, capturas de estudios/medios reales) y usar stock solo como último recurso.

Identificá los momentos concretos del guion donde un inserto de apoyo suma
(mencionan un lugar, un objeto, una acción, una emoción visualizable) —
apuntá a que el tiempo total de b-roll ronde el `broll_ratio` del perfil, sin
forzarlo si eso obliga a meter clips irrelevantes solo para llenar cupo
(calidad > ratio exacto, decilo si te quedaste corto a propósito). Armá
`slots.json` sobre `captions_remapped.json` (paso 3), no sobre timestamps
viejos:

```json
[
  {"query": "hands typing on laptop keyboard", "atMs": 4500, "durationMs": 1500},
  {"query": "city street at night neon lights", "atMs": 9000, "durationMs": 2000}
]
```

Las queries van en inglés (Pexels/Pixabay indexan mejor así) y deben ser
descriptivas y concretas, no abstractas ("hands typing on laptop", no "trabajo").

El b-roll se renderiza siempre en silencio (`BrollLayer.tsx` fuerza `muted`
en el `OffthreadVideo`) -- un stock de video puede traer su propio audio
(ruido ambiente, música de fondo del clip original) que no tiene por qué
sonar sobre la voz del anuncio. Esto ya está resuelto en el motor; si en
algún momento el b-roll se escucha, es una regresión en ese componente, no
algo que corregir por job.

```bash
python3 ~/.claude/skills/editar-anuncios/scripts/fetch_broll.py \
  --job <slug> --slots /tmp/ref-analysis/slots.json
```

El script ya deja los clips descargados dentro de `remotion/public/jobs/<slug>/`
y te imprime el array `broll` listo para pegar en el EditPlan. Si alguna
búsqueda no encuentra resultado, el script lo declara — no inventes un `src`
para ese slot, dejalo afuera o buscá manualmente. El paso 9 (auto-revisión)
es donde se detectan y corrigen los matches que quedaron flojos — no hace
falta que la primera búsqueda sea perfecta.

#### 5b. Alternativa: b-roll sacado de TikTok (cuando el stock se siente muy genérico)

Feedback real del usuario: el banco de Pexels/Pixabay a veces se siente
demasiado genérico para nichos como espiritualidad/manifestación. Para esos
casos hay una fuente alternativa, `fetch_broll_tiktok.py`, que busca en
TikTok mismo (mismo actor de Apify `clockworks/tiktok-scraper` que ya usan
las skills de minería) en vez de en el stock. **Es un flujo de DOS pasos,
nunca uno solo** -- no lo uses como reemplazo automático de `fetch_broll.py`,
úsalo cuando ese banco no está dando el look que el usuario pide.

```bash
python3 ~/.claude/skills/editar-anuncios/scripts/fetch_broll_tiktok.py search \
  --query "candle aesthetic satisfying no talking" --count 6 --output-dir /tmp/broll-tt/<slot>
```

Esto es barato (unos $0.02, solo texto + portada, sin bajar video todavía) y
guarda `cover_NN.jpg` por candidato. **Paso obligatorio antes de descargar
nada:** mirá cada portada con la herramienta de lectura de imágenes y
descartá cualquiera con rostro identificable o texto/marca/@handle quemado
en el video -- de nichos como espiritualidad, muchos resultados directos
("velas encendidas mesa espiritual") vienen con talking-head o títulos
grabados en el video, así que probá una query más "estética/ASMR/sin hablar"
si la primera tanda no da nada limpio (confirmado en pruebas reales: la
query directa dio 0/5 candidatos limpios, la query estética dio 2/5). Recién
con un índice elegido:

```bash
python3 ~/.claude/skills/editar-anuncios/scripts/fetch_broll_tiktok.py download \
  --candidates /tmp/broll-tt/<slot>/candidates.json --index 1 \
  --job <slug> --name <nombre-del-slot> --at-ms 4500 --duration-ms 2000 --trim-start-s 0.5
```

Descarga solo ese clip, lo recorta al tramo que realmente hace falta (nunca
uses el TikTok completo), lo deja sin audio, y lo copia a
`remotion/public/jobs/<slug>/` -- imprime la misma entrada `broll` lista
para el EditPlan que `fetch_broll.py`. También escribe un manifiesto con el
autor y la URL original (trazabilidad, no licencia -- ver nota de riesgo
abajo).

**Riesgo de copyright, ya evaluado y aceptado por el usuario para este caso
puntual:** a diferencia de Pexels/Pixabay, un TikTok ajeno no está
licenciado para reuso comercial -- el filtro de "sin rostro/marca" de arriba
es la mitigación acordada, no una eliminación total del riesgo. No uses esta
fuente por defecto sin que el contexto lo pida (el usuario se quejó
puntualmente de que el stock se sentía genérico); seguí prefiriendo
`fetch_broll.py` cuando el stock ya da un resultado que sirve.

### 6. Música y efectos (Jamendo, libre de copyright)

El usuario autorizó elegir/descargar música real desde un repositorio libre de
copyright (a diferencia de su banco propio de 400 pistas, que sigue sin estar
accesible — para ESE banco seguí sin elegir por tu cuenta, ver regla abajo).
Pexels/Pixabay no tienen API de música; la fuente es **Jamendo**.

Si `JAMENDO_CLIENT_ID` está configurado en `.env`:

```bash
python3 ~/.claude/skills/editar-anuncios/scripts/fetch_music.py \
  --job <slug> --tags "<tags del genero/mood del perfil>" --min-duration-s <duracion_del_video>
```

Usá `generos_musica_observados` del perfil del estilo como base de los tags
(traducilos a tags de género en inglés que Jamendo reconozca: "pop synth" ->
`pop,synth`, "cinematic score" -> `cinematic,orchestral`, etc.). El script
filtra a licencias de uso comercial permitido y te devuelve `musicPath` listo
para el EditPlan, más un manifiesto con artista/licencia — revisalo, algunas
licencias CC-BY piden atribución aunque el uso comercial esté permitido.

Si `JAMENDO_CLIENT_ID` **no** está configurado (todavía dice el placeholder):
no puede crear la cuenta el usuario mismo en devportal.jamendo.com (gratis,
sin tarjeta) y pegar el client_id en `.env`. Mientras tanto, caé al brief de
antes en vez de bloquear el resto del render:

> **Brief de música — estilo TikTok:** trap/hyperpop, ~140 BPM, energía alta y
> constante. Buscá en tu banco algo con esa energía y bajámelo a
> `remotion/public/jobs/<slug>/music.mp3` — con eso seteo `musicPath` y
> re-renderizo (rápido, no hace falta rehacer b-roll ni subtítulos).

### 7. CTA de cuenta regresiva (outro compartido, 5s)

Agregalo al final de **todos** los videos que generes, salvo que el usuario
pida explícitamente que no. Necesita:
- **`text`**: el texto del CTA, en 2 líneas cortas separadas por `\n` (mayúsculas,
  imperativo -- "¡HAZ CLIC PARA...!"). Es específico del producto/oferta, así
  que pedíselo al usuario o inferilo del guion (ej. la llamada a la acción que
  ya está al final del video) -- no reutilices el mismo texto para productos
  distintos sin confirmarlo.
- **`backgroundSrc`**: un clip de b-roll sutil que combine con el tono pedido
  (para este nicho: "espiritual pero no tan explícito" -- velas, luz suave,
  agua, nada de iconografía religiosa directa salvo que el usuario la pida).
  Buscalo con `fetch_broll.py` igual que cualquier otro b-roll.
- **`musicSrc`** (opcional): una pista corta y del mood pedido (acá: "muy
  espiritual" -- tags tipo `ambient,meditation,spiritual` en Jamendo).

```json
"cta": {
  "text": "¡HAZ CLIC PARA\nACCEDER A LOS CÓDIGOS!",
  "backgroundSrc": "jobs/<slug>/cta_bg.mp4",
  "musicSrc": "jobs/<slug>/cta_music.mp3"
}
```

El componente (`CountdownCTA.tsx`) ya maneja la cuenta regresiva 5→1, el
anillo animado y el chevron -- no hay que tocar el TSX por job, solo llenar
estos 3 campos. `totalDurationInFrames` en el EditPlan sigue siendo SOLO la
duración del contenido principal -- el motor le suma el CTA solo. El tamaño
del chevron ya fue agrandado (`width="210" height="186"`) tras feedback de
que casi no se percibía -- no lo achiches de vuelta sin que el usuario lo pida.

**El default de 150 frames asume 30fps -- si el job es a otro fps, el conteo sale mal.** `DEFAULT_CTA_DURATION_IN_FRAMES = 150` da justo 5s a 30fps, pero un job a 24fps (p.ej. contenido que viene de clips de Veo/`video-ads-avatar`, que renderiza a 24fps) queda con 150/24 = 6.25s y una cuenta que no baja limpio 5→4→3→2→1 (se vio en un caso real: mostraba 6 y saltaba a 4). Si el `fps` del EditPlan no es 30, poné `cta.durationInFrames` explícito = `5 * fps` para que la cuenta sea realmente de 5 segundos.

**Música del CTA -- pendiente de decisión del usuario:** el usuario pidió usar
una pista específica (rippeada de un TikTok ajeno, confirmado vía metadata
ffprobe) "de ahora en adelante" para los CTA del nicho manifestación/
espiritualidad. Se usó una vez porque el usuario lo pidió explícitamente,
pero el riesgo de copyright/cuenta publicitaria fue señalado y el usuario
todavía no confirmó si seguir con esa pista puntual o volver a Jamendo por
defecto -- volvé a preguntarlo la próxima vez que haga falta música de CTA
para este nicho en vez de asumir cualquiera de las dos opciones en silencio.

### 7b. Título superior (banner, opcional)

Si el usuario pide un título fijo arriba del video (estilo "POV: ..." de
TikTok UGC, distinto de los subtítulos palabra-por-palabra), usá el campo
`title` del EditPlan en vez de inventar una solución nueva -- ya existe un
componente para esto (`TitleBanner.tsx`, wireado en `Edit.tsx`):

```json
"title": { "text": "TE VA A BUSCAR" }
```

- **Una sola línea por defecto.** El componente no fuerza un salto de línea
  (`whiteSpace: "pre-line"`) -- si el usuario te pasa el título como texto
  corto, dejalo en una sola línea; metele un `\n` vos mismo solo si el
  usuario específicamente pide 2 líneas o el texto es realmente largo.
- **Posición ya calibrada:** justo encima de la cabeza del sujeto (no pegado
  al borde superior del frame) -- funciona bien para el framing selfie/talking
  head típico de este pipeline. Si el video tiene un encuadre muy distinto
  (ej. plano abierto, cámara fija lejos), revisá con `timeline_check.py` si
  sigue quedando bien posicionado antes de entregar; si no, es un ajuste de
  `marginTop` en `TitleBanner.tsx`, no algo para resolver por job en el JSON.
- El texto exacto del título es específico del anuncio -- pedíselo al usuario
  o inferilo del guion, igual que el texto del CTA.

### 8. Preparar assets y armar el EditPlan

**Primero normaliza la fuente:** `python3 ~/.claude/skills/editar-anuncios/scripts/prepare_source.py --video <crudo> --out remotion/public/jobs/<slug>/raw.mp4` (si ya la recortaste con tighten_pacing, normaliza ese resultado). Una fuente HEVC/long-GOP produjo congelados intermitentes de 0.5-2 s en el render.

```bash
mkdir -p ~/.claude/skills/editar-anuncios/remotion/public/jobs/<slug>
cp /tmp/ref-analysis/<slug>/tightened/tightened.mp4 ~/.claude/skills/editar-anuncios/remotion/public/jobs/<slug>/raw.mp4
```
(usá el video YA recortado del paso 3, no el original crudo; el b-roll y la
música ya quedaron copiados por sus scripts respectivos -- todo con `cp`,
nunca `ln -s`).

Armá `job.json` siguiendo el schema de `remotion/src/EditPlan.ts` — `clips[].src`,
`broll[].src`, `musicPath` y `cta.backgroundSrc`/`cta.musicSrc` son todos
**rutas relativas a `remotion/public/`** (ej. `"jobs/lanzamiento-agosto/raw.mp4"`),
nunca absolutas. `captions` sale de `captions_remapped.json`, no del transcript
original. `totalDurationInFrames` = duración del contenido principal en
segundos × `fps` (30 por defecto) -- sin contar el CTA.

### 9. Renderizar

Antes de renderizar: `match_broll_grade.py` (si hay b-roll), define `grade` sutil en el plan (p. ej. `{"contrast":1.05,"saturation":1.04,"temperature":0.12,"fade":0.03,"grain":0.14}`) y corre `add_sfx.py --intensity low|medium|high` (low para emotivo/documental, medium por defecto, high para UGC/VSL enérgico). `add_sfx.py` ya aplica las reglas de Antonio: nivela cada efecto a `--db-under 25` dB bajo el pico medido de la voz (rango permitido 20-30), cambia repeticiones seguidas por otro sonido y pone cachín (`sfx/cash.wav`) en las palabras de dinero; marca con `emphasis: true` en `captions` solo las palabras de peso, que también reciben efecto. Detalle en `references/gramatica-de-edicion.md`.

```bash
cd ~/.claude/skills/editar-anuncios/remotion
npx remotion render src/index.ts UgcIA /ruta/salida/final.mp4 --props=/tmp/ref-analysis/<slug>/job.json --gl=angle
```
(el nombre de composición según el estilo elegido). El render es headless, no
hace falta ninguna app abierta.

**`--gl=angle` es obligatorio, no opcional, desde que se sumaron transiciones
con shader (`zoomBlur`, `crossZoom`, `filmBurn`, `dreamyZoom` — ver
`references/motion-graphics.md`).** Sin ese flag, esas 4 transiciones fallan
con `Failed to create WebGL2 context` (probado 2026-09 en este Mac: Chrome
headless no tiene GPU real por defecto). Las demás transiciones (`fade`,
`slide`, `none`, `wipe`, `iris`, `pushCut`) son CSS puro y no lo necesitan,
pero el flag no les hace daño — ponlo siempre, sin excepción, para no
depender de acordarte cuál estilo usa cuál transición.

Si el archivo final pesa mucho (Remotion renderiza con bitrate alto por
defecto), re-codificá con ffmpeg antes de entregar:
`-c:v libx264 -crf 26 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k`
suele bajar el peso 3-4x sin pérdida visible en redes.

### 10. Auto-revisión (obligatorio, antes de entregar)

Entrega siempre masterizada: `python3 scripts/finalize.py --video render.mp4 --out final.mp4` y luego `python3 scripts/qa_render.py --video final.mp4 --source <crudo> --plan job.json` (si hay FAIL, corregir y re-renderizar). Corre además `python3 scripts/check_freezes.py --video final.mp4 --source <crudo>`: si el render tiene imagen congelada que la fuente no tiene, normaliza la fuente (paso 8) y vuelve a renderizar.

No entregues el primer render sin mirarlo. Usá `scripts/timeline_check.py`
(filmstrip de miniaturas + forma de onda de audio en una sola imagen, técnica
adaptada del proyecto video-use) en vez de sacar frames sueltos con ffmpeg --
una sola imagen te muestra de un vistazo si hay un salto visual raro Y si hay
un pop de audio en el mismo punto:

```bash
python3 ~/.claude/skills/editar-anuncios/scripts/timeline_check.py \
  --video final.mp4 --at-s 62.4 --window-s 2 --output /tmp/check_62s.png
```

Revisá con esto: cada punto de corte de `tighten_pacing.py` (usá los gaps de
`captions_remapped.json` para ubicarlos -- un gap == `--max-pause-ms` exacto
es un corte real), cada inserto de b-roll (¿el clip muestra realmente lo que
la query pedía? ¿la transición de entrada/salida se ve limpia?), 2-3 momentos
de subtítulos (¿se leen bien, no se cortan?), y el CTA final (¿el
número/anillo/texto se ven?). Mirá cada imagen resultante con la herramienta
de lectura de imágenes.

**Ojo con silencios que "sobrevivieron" el corte de `tighten_pacing.py`
pese a que los timestamps parecían correctos:** esto ya pasó una vez (un
hueco de varios segundos entre dos palabras) y la causa real no fue un bug
de código sino que AssemblyAI había marcado el timestamp de una palabra con
~2.5s de drift, con confidence alto y texto perfecto -- el corte de
silencios confió en un dato de entrada malo. Si corriste `tighten_pacing.py`
con `--verify`, esto ahora se detecta solo (compara los gaps del RE-
transcript contra lo esperado, no solo el texto) e imprime una alerta
"hueco de silencio anormalmente grande" con el diagnóstico a seguir -- leé
esa salida antes de ponerte a investigar el corte a mano.

Si encontrás un b-roll que no calza (pasó en la primera entrega de este
video: "factura vencida" trajo un clip de mesa con botellas, no facturas) —
volvé a buscarlo con otra query más específica y re-renderizá (con el motor
actual el render es por archivo completo, no por tramo -- avisá si el tiempo
de espera es un problema, pero priorizá corregir antes de entregar).

**Tope de 3 pasadas de auto-revisión** (mismo criterio que video-use): si
después de 3 rondas de corregir y re-renderizar todavía queda algo mal,
dejá de intentarlo en loop y entregá igual, señalando explícitamente qué
quedó sin resolver -- no lo escondas, y no te quedes reintentando para
siempre.

### 11. Entregar

Enviá el mp4 final con `SendUserFile`. Junto con él, reportá:
- Qué estilo se usó y con cuántos ejemplos reales estaba entrenado ese perfil en
  el momento del render (`n_ejemplos_analizados`) — si es 0-1, aclará que el
  resultado es más genérico y que subir referencias mejora la fidelidad.
- Duración final vs. objetivo, y qué se hizo para llegar ahí (silencio
  recortado, velocidad aplicada).
- Qué b-roll y música se usó y de dónde salió (manifiestos de `fetch_broll.py`
  / `fetch_music.py` tienen fuente/licencia de cada uno).
- Cualquier hallazgo de la auto-revisión que quedó sin resolver.

## Reglas que no pueden violarse

- Nunca inventes una palabra de la transcripción, un número de corte, o un
  resultado de búsqueda de b-roll que no existe — declará la limitación.
- Música: solo desde Jamendo (uso comercial permitido) o el brief manual — nunca
  bajes/uses una pista con copyright real (YouTube, Spotify, etc.) por tu cuenta.
  Para el banco propio de 400 pistas del usuario, seguís sin elegir vos — eso
  sigue siendo brief, no descarga.
- Nunca uses `ln -s` para meter un archivo en `remotion/public/` — copialo.
- Nunca pases una ruta absoluta o `file://` como `src` en el EditPlan.
- Nunca muestres el valor de una API key en el chat.
- Nunca crees una cuenta (Jamendo u otra) en nombre del usuario — pedísela a
  él, es una regla dura del entorno, no solo de esta skill.
- El JSON de perfil (`references/estilos/*.json`) se fusiona con `update-profile`,
  nunca se edita a mano con números inventados.
- Nunca entregues un render sin pasar por el paso 10 (auto-revisión) primero.
