# Estilo: Cinematográfico

**Estado:** 8 ejemplos reales analizados (todos de la carpeta `CINEMATOGRAFICO/`
del usuario, subcarpeta de `~/Documents/ESTILOS DE EDICIÓN ADS/ADS GANADORES 20P/`).
Con 8 ejemplos es una restricción fuerte, aunque sigue siendo el estilo MENOS
homogéneo de los seis (ver más abajo) — no hay un único "look cinematográfico"
fijo, hay varias variantes reales conviviendo bajo el mismo nombre. Ver
`cinematografico.json` para los números que usa el motor de Remotion (el JSON
solo guarda las últimas 10 notas por el límite del script `update-profile` —
este archivo es la memoria completa, no confíes solo en el JSON para el
historial).

**Nota sobre la carpeta de origen (2026-09-22):** de los 8 archivos que hay hoy
en `CINEMATOGRAFICO/`, 3 (`18615584...`, `62a55bb5...`, `Ad 26 FB.mp4`, todos
con fecha de modificación 2026-08-22) ya habían sido analizados en la sesión
anterior — son los mismos cine1/cine2/cine3 de más abajo. Los otros 5 (fecha
2025-01/02, o sea archivos más viejos que nunca se habían corrido por el
pipeline) son los ejemplos nuevos cine4-cine8. Si en el futuro se re-visita
esta carpeta, comprobar fecha de modificación antes de re-analizar — un
archivo ya contado no debería volver a sumar al `n_ejemplos_analizados`.

## Sensación que persigue

**Corrección importante respecto al perfil semilla original:** no es un
"trailer lento" de marca premium. Es casi siempre un montaje de **b-roll
motivacional/espiritual** (nicho manifestación / fe / abundancia / éxito) con
voz en off — nunca hay un hablante a cámara sosteniendo el video (cine6 tiene
un fragmento de entrevista, pero es minoritario dentro del montaje). La
sensación "cinematográfica" viene del tipo de imagen (stock premium: siluetas,
atardeceres, libros antiguos, galaxias, dinero) y del color grading, **no** de
un ritmo pausado: la mayoría de los 8 ejemplos cortan tan rápido o más rápido
que un chisme o un UGC.

## Ritmo de corte

Sigue siendo el estilo menos homogéneo en ritmo de los seis, y con más
ejemplos el rango se amplió en vez de cerrarse:
- **Modo rápido** (la mayoría: cine1, cine3, cine4, cine6, cine7, cine8):
  plano mediano 0.97-2.0s, 23-40.5 cortes/min. cine4 es el más rápido de
  todos (40.5 cortes/min); cine7 el más cortado en número absoluto (~100
  cortes duros en 2 minutos).
  - cine3 además acelera notablemente en los últimos segundos ("conteo
    regresivo").
- **Modo medio** (cine5): plano mediano 2.74s, 16.4 cortes/min.
- **Modo lento** (cine2): plano mediano 6.4s, ~5.5 cortes/min — el único de
  los 8 que coincide con la idea clásica de "planos que respiran" de un
  comercial de marca.

Promedio agregado (JSON): ~2.4s de plano, ~24 cortes/min — pero ese promedio
sigue ocultando que conviven al menos 3 velocidades distintas bajo el mismo
nombre. Si el usuario no aclara cuál quiere, el modo rápido es el default más
representativo (6 de 8 ejemplos), pero preguntar o mostrar ambas opciones
sigue siendo válido.

## Transiciones

Predominan los cortes secos en los 8 ejemplos (32 de ~46 transiciones
observadas). Crossfade y zoom-punch aparecen como recurso puntual y
consistente en varios ejemplos. Novedades de este lote: **slide** (cine4,
único caso en todo el estilo hasta ahora) y **match cut** (cine8) — tratarlos
como variación ocasional, no como núcleo del estilo.

## Subtítulos

**Cuatro variantes conviven, no una ni dos:**
- **Karaoke + resaltado amarillo** (cine1, cine3, cine8): palabra por
  palabra, mayúsculas, fuente gruesa, blanco con caja/resaltado amarillo,
  centrado, animación pop. El look "típico" del resto de los estilos del
  usuario.
- **Karaoke SIN resaltado** (cine4, cine5, cine7): mismo formato palabra por
  palabra, pero blanco con solo contorno negro, sin caja ni color de
  énfasis — más discreto que la variante amarilla aunque sigue siendo
  karaoke, no frase completa.
- **Frase completa sin caja** (cine2): 2 líneas, centrada, blanco sólido,
  fade suave — la variante más discreta de todas.
- **Sin subtítulos** (cine6): confirmado visualmente (no solo por
  TwelveLabs) — el video no lleva ningún texto en pantalla.

En resumen: el resaltado de color en captions NO es un rasgo fijo de este
estilo — varía video a video, y hay que decidirlo mirando la referencia
específica que se está emulando, no asumir el default de otro estilo.

## Música

Score cinematográfico / piano ambiental es el género más repetido (7 de 8
ejemplos entre las dos variantes "cinematic score" y "motivacional/pop
energético"); en cine3 la vibe se acerca más a "thriller/documental de
tensión" con energía que sube hacia el final. cine4/cine5 (el lote más
rápido y menos "premium" en b-roll) tienden más a "motivacional/pop
energético" que a score orquestal puro. BPM bajo-medio en general.

## B-roll

**Casi 100% del tiempo es b-roll** en la mayoría de los ejemplos — no hay un
"hablante principal" al que el b-roll apoye (salvo el fragmento de entrevista
de cine6), es voz en off pura sobre un montaje de stock. Dentro de ese
montaje conviven varias SUB-VARIANTES de "prueba"/imaginario, vale la pena
distinguirlas al elegir b-roll para un anuncio nuevo:
- **Stock abstracto/simbólico** (cine3, cine7, cine8): cerebros, libros
  antiguos/Biblia, galaxias, neuronas, gente meditando u orando, dinero,
  relojes, siluetas, pergaminos, manos escribiendo cartas, multitudes,
  microscopios, agua.
- **Biografía real como prueba** (cine5): fotos de una persona pública
  reconocible en distintas etapas de su vida (niña -> adulta exitosa) en vez
  de b-roll simbólico — la "prueba" es la biografía real, no una metáfora
  visual. Técnica distinta, mismo nicho de manifestación/éxito.
- **Captura de chat como prueba social** (cine4): un pantallazo de
  testimonio de WhatsApp intercalado con fotos familiares en blanco y negro
  y objetos de lujo (reloj) — primer caso del estilo con una captura de
  conversación como elemento de prueba.
- **Entrevista + b-roll místico** (cine6): clip de entrevista/podcast
  (auriculares, micrófono, silla de estudio) cortado junto a b-roll
  simbólico (silueta ardiendo/meditando, libro religioso antiguo, familia
  caminando) — el único ejemplo que mezcla un hablante real con el montaje.

El `broll_ratio` real (0.92, del perfil original) sigue siendo representativo
del grueso de los ejemplos — este estilo se parece en estructura a
`voz-en-off-ugc` (avatar nunca sostiene el video), pero con un nicho e
imaginario distinto (espiritual/premium vs. lifestyle cotidiano).

## Color grading

Varía según el ejemplo pero casi siempre con intención (nunca un grading
plano/neutro):
- Saturado y vibrante tipo TikTok, con tonos cálidos predominantes: la
  mayoría de los ejemplos (cine1, cine4, cine5, cine7, cine8).
- Cálido y dorado en atardeceres, más neutro/luminoso en exteriores de día
  (cine2).
- Cálido y desaturado, look "archivo antiguo" (cine3).
- **Código de color POR TEMA dentro del mismo video** (cine6): tonos
  cálidos/dorados en escenas de "milagro"/riqueza, tonos fríos/azules en
  escenas de agua/ciencia — una técnica de grading más deliberada que el
  resto del estilo, y una idea concreta para replicar cuando el guion de un
  anuncio nuevo mezcla dos tipos de contenido distintos (ej. resultado
  financiero + explicación técnica).

Punto común: contraste medio-alto en todos los casos.

## Cómo se actualiza este perfil

Cada vez que el usuario suba un anuncio de referencia marcado como
"cinematográfico", correr el pipeline de `analyze_reference.py` (metrics +
twelvelabs) y fusionar los hallazgos con `update-profile`. **Antes de
re-analizar un archivo de una carpeta ya visitada, comprobar su fecha de
modificación (`stat -f "%Sm" archivo.mp4`)** contra la fecha de
`ultima_actualizacion`/las notas fechadas de este perfil — si coincide con una
fecha ya registrada, es casi seguro el mismo archivo y no debe volver a
contarse. Dado que el ritmo y el look de subtítulos varían tanto entre
ejemplos, al sumar más vale la pena anotar explícitamente a qué sub-variante
se parece el nuevo video (rápido/medio/lento; karaoke-amarillo/karaoke-sin
resaltado/frase completa/sin subtítulos; qué sub-tipo de b-roll) en vez de
dejar que el promedio numérico diluya esas distinciones — el JSON solo
retiene las últimas 10 notas, así que las notas viejas que importan
(cine1/cine2/cine3) hay que preservarlas acá, a mano, cuando se agreguen más
ejemplos nuevos.
