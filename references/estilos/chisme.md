# Estilo: Chisme

**Estado:** 4 ejemplos reales analizados (todos de la carpeta
`FORMATO CHISME/` del usuario, dentro de
`~/Documents/ESTILOS DE EDICIÓN ADS/ADS GANADORES 20P/`). Ver `chisme.json`
para los números que usa el motor de Remotion.

**Nota sobre la carpeta de origen (2026-09-22):** 3 de los 4 archivos
(`Ad 60/79/83 FB.mp4`, fecha de modificación 2026-08-22) ya habían sido
analizados en la sesión anterior — son chisme1/chisme2/chisme3 de más abajo.
El cuarto (`d9cf35d3...`, fecha 2025-02, más viejo) es el ejemplo nuevo,
chisme4. Comprobar fecha de modificación antes de re-analizar un archivo de
esta carpeta si se vuelve a visitar.

## Sensación que persigue

**Ya no es solo chisme de celebridades — el nicho real es más amplio.** Los
primeros 3 ejemplos son chisme/tabloide de **celebridades reales**
(relaciones, apariciones) usando metraje de archivo (alfombra roja,
conciertos, fotos de paparazzi, besos en público) como "la prueba" de lo que
se cuenta. El cuarto ejemplo (chisme4) tiene la MISMA estructura de edición
(corte duro, karaoke amarillo, ritmo rápido) pero es una narrativa tipo
**"storytime" financiero/bíblico** (manos con documentos, una máquina
contadora de billetes, una Biblia antigua) — sin nada de celebridades.
Conclusión: lo que define "chisme" en la carpeta del usuario parece ser la
ESTRUCTURA (narración con gancho dramático + corte duro + karaoke) más que un
nicho de contenido fijo — no asumir que el próximo ejemplo también será sobre
famosos.

## Ritmo de corte

Rápido, con un rango amplio entre ejemplos: plano mediano entre 0.8s y
3.37s, 15.7 a 33 cortes/min según el video (promedio ~22 cortes/min). No hay
un solo "ritmo de chisme" fijo — el editor lo ajusta según cuánto material de
archivo hay disponible para cada historia. chisme4 (el "storytime"
financiero, sin metraje de archivo real) es el más lento de los 4 — puede ser
que la falta de metraje de archivo dramático explique el ritmo más pausado,
no solo el tema.

## Transiciones

Corte seco casi siempre (21 de 25 observadas). Zoom-punch como énfasis
puntual en los momentos de mayor impacto; crossfade es raro (1 de 25).

## Subtítulos

Palabra por palabra tipo karaoke, mayúsculas, fuente sans-serif muy gruesa,
texto blanco con **caja de fondo de color sólido** en la palabra clave,
posición centro-baja, animación pop. El color de la caja **no es fijo**:
se vio amarillo (el más común, incluido en chisme4), dorado y también
morado/violeta según el video — tratar el color como variable, no como una
constante de marca.

## Música

Varía entre stinger dramático/suspenso ligero (más cercano al perfil semilla
original), pop synth/pop dramático con energía alta (chisme de celebridades),
y "storytime motivacional" sin sincronía marcada con la batida (chisme4,
único caso de este género hasta ahora) — depende del tono de la historia.
Común a los primeros 3: la intensidad tiende a subir con los cortes.

## B-roll

Uso medio-alto (~64% del tiempo, más que el 30% que asumía el perfil
semilla): metraje de archivo de las celebridades (besos, alfombra roja,
conciertos, estadios, tiendas de lujo) y algunos inserts de apoyo (manos,
notas escritas, dinero, pantallas de celular) intercalados con el
narrador/texto que cuenta la historia — en los 3 ejemplos de celebridades.
chisme4 no tiene metraje de archivo de celebridades en absoluto: es manos con
documentos/dinero, una Biblia antigua, una máquina contadora de billetes y
reacciones de personas — el mismo tipo de inserto de apoyo que el resto, pero
sin el "material de archivo" que define a los otros tres.

## Color grading

Sin un look único de marca: vibrante/saturado y cálido en 3 de 4 ejemplos
(look TikTok/Reels, incluido chisme4), más apagado y "de archivo" en uno de
los de celebridades — depende del material fuente disponible más que de una
decisión de grading deliberada. Contraste medio-alto en todos.

## Cómo se actualiza este perfil

Correr `analyze_reference.py` (metrics + twelvelabs) sobre cada nuevo video
de `FORMATO CHISME/` y fusionar con `update-profile --style chisme`. **Antes
de re-analizar un archivo de una carpeta ya visitada, comprobar su fecha de
modificación** contra las fechas ya registradas en las notas — evita
duplicar un ejemplo ya contado en `n_ejemplos_analizados`. Dado que el
nicho de contenido puede variar (celebridades vs. storytime financiero/moral,
visto en chisme4), anotar explícitamente el tema del nuevo ejemplo además del
ritmo/material de archivo disponible — eso explica mejor la variación que el
promedio numérico solo, y ayuda a decidir si "chisme" es el estilo correcto
para un guion que no sea sobre celebridades.
