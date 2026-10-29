# Estilo: Podcast

**Estado: basado en UN SOLO ejemplo real** (`PODCAST/Ad 77 FB.mp4`). Tratar
este perfil como un punto de partida débil, no como una restricción fuerte
— conviene que el usuario suba más grabaciones de podcast para afinarlo
antes de confiar en él para un render final. Ver `podcast.json` para los
números que usa el motor de Remotion.

## Sensación que persigue

**Corrección importante respecto al perfil semilla:** el único ejemplo real
no es una conversación de estudio con dos conductores en plano fijo. Es una
**entrevista de una sola persona grabada en exterior** (un jardín), editada
con muchos recursos propios de reels/UGC: subtítulos karaoke palabra por
palabra, b-roll de apoyo intercalado, y hasta un frame de "flash" de color
sólido como transición puntual. Lo que más lo distingue de los otros
estilos del usuario sigue siendo válido: el plano principal dura bastante
más (mediana 4.4s) que en chisme/UGC/voz-en-off (1-3s), y el ritmo general es
más pausado (11.4 cortes/min).

## Ritmo de corte

Pocos cortes para el estándar de los otros estilos del usuario (11.4/min),
pero no tan lento como "casi sin cortes" — hay tomas del plano principal
sostenidas varios segundos, cortadas ocasionalmente para insertar b-roll.

## Transiciones

Corte seco predominante, con algún crossfade puntual. Se observó además un
recurso de "flash" de color sólido (rojo/naranja) de 1-2 frames como
transición entre el plano principal y un inserto — vale la pena confirmarlo
o descartarlo con más ejemplos, porque con un solo video no se puede saber
si es un recurso consistente del estilo o un detalle de este video puntual.

## Subtítulos

Palabra por palabra tipo karaoke (no "frase completa" como asumía el perfil
semilla), fuente gruesa blanca con resaltado amarillo en la palabra clave,
posición centro-baja, animación pop — el mismo look karaoke+amarillo que
comparten casi todos los estilos del usuario, no algo distintivo de podcast.

## Música

Ambiental suave, casi ausente — coincide con la idea del perfil semilla de
que la música no debe competir con la conversación.

## B-roll

Moderado (~35% del tiempo, más que el "mínimo" que asumía el perfil semilla):
insertos de estilo de vida (auto de lujo de noche, tablero con luces)
ilustrando literalmente lo que dice la entrevistada — no son ángulos
alternativos del mismo set de grabación, son b-roll externo.

## Color grading

Natural, luz de exterior, contraste medio — sin gradación de estudio
elaborada. Consistente con una grabación real al aire libre más que un set
armado.

## Cómo se actualiza este perfil

Con un solo ejemplo, cualquier número o patrón de este perfil debe tratarse
como provisional. Avisar al usuario explícitamente si pregunta por este
estilo: "el perfil de podcast está basado en un único video de referencia,
conviene subir más para que sea confiable". Correr
`analyze_reference.py` (metrics + twelvelabs) sobre cada nuevo video de
`PODCAST/` y fusionar con `update-profile --style podcast`; con el segundo
y tercer ejemplo, revisar si el patrón de "entrevista de una persona en
exterior con edición estilo reels" se sostiene o si este primer ejemplo fue
atípico.
