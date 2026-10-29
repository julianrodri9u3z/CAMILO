# Estilo: UGC con IA

**Estado:** 4 ejemplos reales analizados (todos de la carpeta
`FORMATO UGC/` del usuario). Ver `ugc-ia.json` para los números que usa el
motor de Remotion.

## Sensación que persigue

Se siente grabado en celular por una persona real (selfie/UGC), pero **no
es un hablante solo a cámara todo el tiempo** como asumía el perfil semilla:
en los 4 ejemplos reales el plano de la persona se combina con bastante
b-roll aspiracional (lujo, viajes, dinero, eventos) — el nicho dominante que
apareció una y otra vez en estos 4 videos es **contenido de estilo de vida
de alto poder adquisitivo** (yates, autos deportivos, tiendas, bodas,
paisajes de viaje). Sigue sintiéndose casero/directo, pero con más
producción visual que un UGC "puro".

## Ritmo de corte

Rápido y con bastante variación: plano mediano entre 0.5s y 3.8s, 13 a 31
cortes/min según el video (promedio ~23 cortes/min). El ejemplo más lento
(ugc1) es también el que tiene menos b-roll y más plano fijo del hablante;
los tres más rápidos intercalan mucho más con inserts.

## Transiciones

Corte seco casi siempre (17 de 19 observadas). Un jump cut y un crossfade
puntuales — no hay evidencia fuerte de que el jump cut sea un recurso central
del estilo (aparece 1 sola vez en 4 ejemplos).

## Subtítulos

Consistente en los 4: palabra por palabra tipo karaoke (en un ejemplo,
frase completa en algunos tramos), mayúsculas o frase con fuente sans-serif
gruesa, blanco con caja de resaltado **amarilla**, posición centro o
centro-baja, animación pop. Esto es más parecido al look karaoke+amarillo
que comparten chisme y voz-en-off-ugc que a un estilo propio distintivo.

## Música

Pop synth en los 4 ejemplos (antes el perfil semilla mencionaba también
"sonido de trend" y "pop upbeat" genéricos — pop synth es lo que
efectivamente se observó). Energía media a alta, cortes que suelen
sincronizar con el ritmo.

## B-roll

**Corrección importante respecto al perfil semilla:** el `broll_ratio` real
es ~0.54 (más de la mitad del tiempo), no el ~0.2 que asumía el perfil
original. El b-roll no es solo "zoom/punch-in sobre el mismo plano del
avatar" — son insertos externos reales: yates, autos de lujo, tableros de
auto, tiendas, bodas, paisajes, manos escribiendo, libros, fotos de grupo.
Sigue siendo menos b-roll que en `voz-en-off-ugc` (~0.95), pero
significativamente más que "casi nada".

## Color grading

Vibrante y saturado, estilo TikTok, en los 4 ejemplos — **no** es el look
"natural sin filtro tipo cámara de iPhone" que describía el perfil semilla.
Contraste medio-alto, tonos cálidos.

## Cómo se actualiza este perfil

Cada vez que el usuario suba un anuncio de referencia marcado como "UGC con
IA", correr el pipeline de `analyze_reference.py` (metrics + twelvelabs) y
fusionar los hallazgos con `update-profile`. Prestar atención a si el nuevo
ejemplo mantiene el patrón de b-roll de lujo/estilo de vida observado en los
4 primeros — si aparece un ejemplo con un nicho de contenido muy distinto,
anotarlo explícitamente en vez de asumir que "lujo" es intrínseco al estilo.

## Ver también (2026-09-23)

Si el material base es **una sola toma a cámara** (por ejemplo un clip de `video-ads-avatar` sin
cortes internos) o el usuario pide un look de creadora real con overlays, el estilo que encaja
es `ugc-creador` (12 ejemplos, plano secuencia + stickers/tarjetas de prueba), no este: `ugc-ia`
asume selfie + b-roll aspiracional a ~23 cortes/min.
