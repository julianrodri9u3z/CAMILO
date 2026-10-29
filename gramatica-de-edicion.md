# Gramática de edición y puertas de calidad

Qué separa una edición "hecha por una persona" de una "hecha por una IA", destilado de (a) las pruebas reales con el usuario y (b) la revisión del repositorio MIT `MartinDelophy/ai-video-editor` (Timeline Studio; es un editor de navegador, no se integra tal cual — se aprovechan sus ideas de flujo y criterios; ver `references/revision-ai-video-editor.md`).

## Los 8 hábitos de una edición que parece humana

1. **Sonido diseñado, no solo música.** Cada gráfico o corte con peso tiene un sonido corto debajo (whoosh al entrar un b-roll, pop en una palabra clave, golpe grave en una cifra, ding en la garantía/CTA). Una edición donde los gráficos aparecen en silencio delata automatización. → `scripts/make_sfx.py` + `scripts/add_sfx.py` (campo `sfx` del plan). Volúmenes bajos: se sienten, no se oyen.
2. **Look unificado.** Todo el material (principal + b-roll) pasa por el mismo contraste/saturación/temperatura, negros ligeramente levantados y un poco de grano. Lo que hace que un b-roll parezca "pegado" es la diferencia de look. → campo `grade` del plan + `scripts/match_broll_grade.py` (iguala brillo y saturación del insert al clip principal, con límites). Valores sutiles: un grade visible es un defecto.
3. **Audio masterizado.** Normalizar a ~-14 LUFS y -1.5 dBTP (feed de TikTok/Reels). Los renders crudos salen 6-10 dB bajos (el clip de prueba salió a -21.6 LUFS). → `scripts/finalize.py`.
4. **Material real, no stock.** La persona, escenas de sus películas, TikTok, noticias, capturas de estudios reales. → `references/enriquecimiento-visual.md`, `scripts/find_tiktok_broll.py`, `scripts/fetch_clip_url.py`.
5. **Un énfasis principal por plano.** Como mucho un tratamiento principal y uno de apoyo (p. ej. palabra clave + subrayado). No apilar círculo + flecha + zoom + glow porque estén disponibles. Si hay 4+ eventos visuales en 1 s, sobra algo.
6. **Gramática de movimiento:** establecer → guiar → adquirir → sostener → soltar. Un solo movimiento de cámara motivado por plano; **detener el movimiento mientras se lee** un dato, cara o subtítulo; sin rebotes elásticos ni zoom repetido por costumbre.
7. **El audio manda.** La voz (o la locución aceptada) fija el reloj: cortes, gráficos y subtítulos se cronometran contra el audio final, nunca al revés. No cortar respiraciones o pausas que cargan emoción; el recorte de silencios no es aprobación automática.
8. **Tensión con contraste.** Un clímax claro (un pico principal, uno o dos secundarios en 10-20 s), preparación antes y salida después. Ritmo uniforme y todo "en alto" aplana. Para anuncios: el mejor material va en el pico (prueba/cifra/promesa), no en la apertura salvo cold open deliberado.

## Mapa de categorías (qué proteger)

- `talking-head`: significado y expresión; reencuadre suave; énfasis de palabras clave.
- `entrevista/podcast`: atribución y reacciones; cambios de ángulo motivados (los planos de reacción del original se conservan).
- `marketing/producto`: identidad del producto, prueba visible cuando se hace el claim, CTA acordado; nunca inventar claims, métricas ni testimonios.
- `tutorial/demo`: instrucción + acción + resultado son una unidad.
- `narrativo/documental`: causalidad y emoción; los efectos quedan subordinados a la historia.

## Puerta de calidad antes de entregar (rechazar si falla)

`python3 scripts/qa_render.py --video final.mp4 --source <crudo> --plan job.json` revisa: imagen congelada, fotogramas negros, clipping/true peak, volumen fuera de -16..-12 LUFS, silencios largos, subtítulos ilegibles, acumulación de eventos, sonidos demasiado juntos, b-roll < 1.2 s. Además, a ojo (hoja de contactos): temblor visible, subtítulo que tapa cara/manos, texto que cambia antes de que se lea, efecto decorativo apilado, mismatch preview/export. Éxito técnico del export no es aprobación de calidad.

## Orden de producción (resumen)

crudo → `prepare_source.py` → transcribir → plan de cortes y énfasis → material real (`find_tiktok_broll.py`/`fetch_clip_url.py`/capturas) → `match_broll_grade.py` → `add_sfx.py` → stills de verificación → render → `finalize.py` (masterizado) → `qa_render.py` → hoja de contactos → entrega con lista de lo asumido/faltante.
