# HyperFrames: motion graphics listos para los anuncios (y cómo usar los prompts de skillry.dev)

**Qué es:** HyperFrames (heygen-com/hyperframes, Apache-2.0) = "escribe HTML, renderiza video". El puente de esta skill descarga el CLI solo la primera vez (`npx --yes hyperframes`; revisa la máquina con `npx hyperframes doctor`). Para además tener sus skills de creación (hyperframes, motion-graphics, talking-head-recut, embedded-captions…): `npx skills add heygen-com/hyperframes`. Render medido en un Mac M3: una tarjeta de 4,5 s tarda ~7 s; el chat de 25 s, ~24 s.

**Cómo se integra con nuestra edición (el puente):** `scripts/make_hf_card.py` (en esta skill)
```bash
python3 ~/.claude/skills/editar-anuncios/scripts/make_hf_card.py list --vertical            # bloques 9:16
python3 .../make_hf_card.py list --search chart                                            # buscar por palabra/tag
python3 .../make_hf_card.py vars --block message-thread-reveal                            # qué se puede cambiar
python3 .../make_hf_card.py render --block message-thread-reveal --job <job> --name chat \
   --vars '{"contactName":"Carlos","questionMessage":"..."}' [--trim 8] [--fit contain|cover]
```
Deja el MP4 (H.264, 1080×1920, 30 fps, silencioso) en `editar-anuncios/remotion/public/jobs/<job>/` e imprime el `broll`.
Bloques 16:9 se acomodan a vertical con `--fit contain` (barras negras) o `cover` (recorta los lados). Imágenes propias
(`cardImage`, `brandLogo`…): pasar la ruta local en `--vars`, el script la copia al proyecto.
Los textos de cada bloque están pensados para su idioma original: mantener el largo de cada frase (±20 %) y revisar el
fotograma antes de insertarlo.

## Bloques verticales útiles para anuncios (los 13 de 9:16)
| Bloque | Para qué sirve en un anuncio |
|---|---|
| `message-thread-reveal` (25 s, usar `--trim`) | conversación en el teléfono: "mira lo que me escribió un cliente"; prueba social, curiosidad |
| `notification-cascade` (14 s) | notificaciones que llegan una tras otra (ventas, mensajes) |
| `slack-notification-ad` (12 s) | pantalla de bloqueo con peticiones que escalan; mostrar la solución al final |
| `ai-chat-reveal`, `chatgpt-exchange`, `claude-exchange` | pregunta → respuesta de IA palabra a palabra; ideal para "le pregunté a la IA…" |
| `notes-reveal` (25 s) | nota que se escribe letra a letra (guion, lista, promesa) |
| `share-sheet-carousel` (7 s) | hoja de compartir con previsualizaciones; "compártelo" |
| `tiktok-follow`, `instagram-follow`, `spotify-card` (4-5 s) | overlays de perfil/seguir; funcionan sobre el video real |
| `heygen-avatar-promo-card` | tarjeta de oferta con tipografía bold |
| `flowchart-vertical` | diagrama de decisión animado |

## Bloques 16:9 que valen la pena (usar `--fit`)
`apple-money-count` (dinero que cuenta), `bar-chart-race`, `data-chart`, `mk-line-graph`, `mk-progress-stat`,
`vfx-iphone-device`, `app-showcase`, `ios26-liquid-glass`, `lt-*` (11 lower thirds), `news-ticker`, `x-post`, `reddit-post`,
`yt-comment-card`, `macos-notification`, `hw-*` (texto a mano), `weight-wave`, `split-flap-board`, transiciones de shader
(`glitch`, `whip-pan`, `light-leak`, `flash-through-white`, `cinematic-zoom`…), mapas (`world-map`, `us-map`…).
Catálogo completo: `make_hf_card.py list` (170 bloques + 222 componentes con `npx hyperframes catalog --type component`).

## Skills de HyperFrames que sirven directo
- `talking-head-recut`: pone tarjetas gráficas (títulos cinéticos, lower thirds, datos, citas) sobre un video de persona hablando, sincronizadas con la transcripción. Es la competencia directa de nuestro `editar-anuncios`; probarla en un video real antes de decidir cuál usa cada caso.
- `embedded-captions`: subtítulos, incluido el estilo "detrás de la persona" (catálogo de 35 estilos).
- `motion-graphics`: unidades cortas de motion (titulares cinéticos, contadores, gráficas, stings, mapas, tweets).
- `media-use`: resolver música/SFX/imágenes/voz con un solo verbo.
Para un motion desde cero, o algo que no está en el catálogo: pedirle a Claude "usa /hyperframes" y describir la pieza.

## skillry.dev/ai-videos/opus-5-5 (galería de prompts)
- 475 videos hechos por creadores con Claude (motion graphics 288, explainers 62, 3D 55, juegos 70). Cada uno muestra el
  prompt que usó. La página dice: "Prompts free to copy… no account needed". No declara licencia sobre los videos (son de cada creador).
- **Cómo funcionan:** un prompt es la descripción de la pieza (formato, duración, estilo, escenas, tipografía, movimiento, música). Se pega en Claude Code con HyperFrames instalado y Claude escribe el HTML y renderiza. No hace falta ningún programa extra.
- **Cómo los usamos:** (1) buscar en la galería un estilo parecido a lo que pide el usuario (URL de cada item: `/ai-videos/opus-5-5/<creador>-<id>`); (2) leer su prompt con WebFetch; (3) **adaptarlo** a nuestra pieza (marca, textos propios, vertical 1080×1920, 4-6 s, silencioso) y renderizarlo con `/hyperframes` o `/motion-graphics`; (4) meterlo a la edición con el mismo flujo de `broll`. No copiar el video ni el prompt tal cual para un anuncio comercial: el prompt es punto de partida y el resultado se firma como pieza propia; si una pieza queda casi idéntica a la de un creador, avisarle al usuario.
- No se descargaron los 475 prompts: se traen bajo demanda, por estilo.

## Opciones del puente que importan en un anuncio
- `--speed 1.5` acelera el bloque (los de interfaz son lentos a propósito) y `--squeeze` recorta sus pausas muertas (esperas de «alguien leyendo»); ambos se aplican antes de `--trim`. Sin `--squeeze`, `qa_render.py` marca esas pausas como «congelados».
- `--vars-file` acepta un JSON con las variables; las imágenes locales se copian solas al proyecto de HyperFrames.
- Los textos de cada bloque están pensados para su idioma original: mantén el largo de cada frase (±20 %) y revisa el fotograma antes de insertarlo.
