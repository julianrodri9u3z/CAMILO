# Estilo: Voz en Off UGC

**Estado:** 7 ejemplos reales analizados (todos de la carpeta
`VOZ EN OFF UGC/` del usuario) — el estilo con más ejemplos de los cinco,
tratarlo como una restricción fuerte. Ver `voz-en-off-ugc.json` para los
números que usa el motor de Remotion.

## Sensación que persigue

Confirmado en los 7 ejemplos sin excepción: el avatar/persona **nunca habla
a cámara** — se lo ve de espaldas, de perfil, o simplemente no aparece,
mientras una narración en off cuenta la historia sobre un montaje de
"día en la vida" o de b-roll temático. El nicho de contenido varía bastante
video a video (manifestación/ritual, mascotas/refugio, bienes raíces/mudanza,
vida familiar/doméstica, estilo de vida de lujo), pero el tratamiento de
edición es idéntico en todos — este es el patrón más consistente de los
cinco estilos analizados.

## Ritmo de corte

Medio-rápido con bastante rango: plano mediano entre 1.2s y 2.7s, 12 a 30
cortes/min según el video (promedio ~20 cortes/min). No hay correlación
clara entre ritmo y nicho de contenido — varía por video más que por tema.

## Transiciones

Corte seco domina ampliamente (23 de 27 observadas). Se vio en más de un
ejemplo (voz2 y podcast, que comparte editor/estilo) un recurso de **flash
de color sólido** de 1-2 frames como transición puntual entre escenas — no
es la transición principal pero aparece lo bastante seguido como para
anotarlo como un recurso característico del usuario, no solo de este estilo.

## Subtítulos

Palabra por palabra tipo karaoke en la gran mayoría, fuente sans-serif
gruesa, blanco con caja de resaltado **amarilla**, posición centro-baja,
animación pop — el mismo look que comparten chisme y UGC-IA. Una excepción
notable: voz7 combina ese estilo con tramos de frase completa sobre una
tarjeta blanca redondeada con texto dorado/marrón (formato tipo
instrucción/receta) — vale la pena tenerlo como variante posible, no como la
norma.

## Música

Pop synth en la gran mayoría de los ejemplos (5 de 7); dos ejemplos se
etiquetaron con matices distintos ("pop synth / trend TikTok" y "pop synth
optimista"). Energía media, la intensidad suele subir levemente hacia el
final del video. Cama de fondo constante bajo la narración.

## B-roll

**El estilo con más b-roll de los cinco, confirmado con 7/7 ejemplos**
(`broll_ratio` ~0.95): casi toda la imagen es b-roll/actividad, ya que el
"hablante" nunca aparece a cámara. Gran variedad de escenas según el video:
manos escribiendo, interiores de apartamentos, pantallas de celular, perros
de refugio, dinero, autos de lujo, rascacielos, objetos de ritual (vaso de
agua, vela), family celebrando una mudanza, bebé, cocina, oficina.

## Color grading

Vibrante y saturado, estilo TikTok, cálido, contraste medio-alto en la
mayoría — no es el look "natural sin filtro" que describía el perfil semilla
original; más cercano al mismo tratamiento vibrante que UGC-IA y chisme.

## Cómo se actualiza este perfil

Correr `analyze_reference.py` (metrics + twelvelabs) sobre cada nuevo video
de `VOZ EN OFF UGC/` y fusionar con `update-profile --style voz-en-off-ugc`.
Con 7 ejemplos ya es un perfil sólido para el ritmo/subtítulos/color; lo que
más vale la pena seguir observando es si el "flash de color" como transición
se confirma como recurso recurrente o fue coincidencia en los 2 casos vistos.
