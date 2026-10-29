# Estilo: Podcast Clip (composición `PodcastClip`)

**Estado:** creado y aprobado en una prueba real (2026-10-06): clip de entrevista de ~75 s, un solo hablante, vertical. El usuario: "le atinaste bien a la edición", subtítulos y música "perfectos". No aprendido de una serie de referencias; es un punto de partida validado, no una restricción fuerte.

## Receta usada

- Subtítulos `kinetic`: frase de hasta 4 palabras apilada abajo-izquierda, minúscula, sin signos; palabras clave marcadas con `emphasis` (≈12 en 75 s: depression, tough, divorce, gray, blue, saving grace, girl dad). Blanco, sombra suave.
- Cortes duros en límites de frase; el plano largo se parte en clips continuos con `zoom` 1.08–1.12 y `zoomOrigin:"top"` en tramos de >10 s sin cambio de plano de la fuente.
- Rotulación: `title` negro arriba ("<PERSONA> ON <TEMA>"), `lowerThirds` con nombre, `keywordCallouts` (concepto) y `statCallouts` (cifra con glow dorado) en el momento exacto de la palabra; `vignette` 0.35.
- B-roll ≈ 20 % del tiempo, 2.5–4.3 s por inserto, con `scrim: 0.6` para que los subtítulos se lean sobre clips claros.
- Música: instrumental suave (piano), `musicDuckedVolume 0.05`, `musicFullVolume 0.16`.
- Sin CTA final (no había oferta que inventar); se recortó la tarjeta final del programa original.

## Pendiente / mejoras pedidas por el usuario

Ver `references/enriquecimiento-visual.md`: b-roll con la persona/clips de película/TikTok/noticias/capturas de estudios reales en vez de stock, y la corrección del congelado (`prepare_source.py` + `check_freezes.py`).
