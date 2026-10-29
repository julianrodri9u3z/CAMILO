# espiritual-voz-off

Voz en off pura sobre b-roll ilustrado (IA) de temática espiritual/angelical —
sin hablante a cámara, ni un avatar real. Nace de una prueba real: un video de
arcángeles con este formato al que se le añadió un CTA nuevo generado con
`video-ads-avatar` (ver ese SKILL.md, sección 4b, para el límite duro de ~8s
por clip de Veo si vas a generar b-roll nuevo con IA para este estilo).

## Look visual

- Imágenes ilustradas/AI (luz dorada, alas, nubes, siluetas alcanzando la luz)
  con cámara lenta tipo Ken Burns — nunca estática del todo.
- Nada de hablante, avatar ni rostro sostenido en cámara.

## Captions — variante `karaoke`

Distinto de los otros 4 variants del motor:

- La frase corta se queda en pantalla completa (no una sola palabra gigante
  como `bold`).
- Solo la palabra que se está diciendo en ese instante se resalta —
  `captionHighlightColor` (cian, `#22D3EE` en el ejemplo real) — el resto de
  la frase se queda en `captionColor` (blanco).
- Mayúsculas, sin contorno (`WebkitTextStroke`), sin rebote/escala — más
  sobrio que `bold`/`bouncy`.

Usa esta variante para cualquier ad de este nicho/formato que traiga ese
mismo patrón de captions — si un nuevo ejemplo de referencia trae un caption
distinto (p.ej. frase sobre tarjeta de color, como se vio en algunos ejemplos
de `voz-en-off-ugc`), no fuerces `karaoke`, documentalo aparte.

## Nivel de aprendizaje

`n_ejemplos_analizados: 0` — este perfil nace de una única prueba real, no de
`analyze_reference.py` corrido sobre el video completo. Tratalo como punto de
partida (el look de captions es fiel al original; ritmo de corte/b-roll/
música son suposiciones razonables, no medidas) hasta que se analice un
ejemplo completo con el flujo de la Parte A.
