# Revisión del repositorio MartinDelophy/ai-video-editor ("Timeline Studio")

Revisado el 2026-10-06 (commit `9d48dc3303`, 889 estrellas, licencia de código MIT). Solo lectura: no se clonó ni se ejecutó nada de ese repositorio.

## Qué es (y qué no)

Un editor de video **en el navegador**, estilo CapCut (línea de tiempo multipista, WebGPU/WASM, modelos locales de IA), con una skill para agentes (`edit-timeline-studio`) que opera el editor vía WebMCP/comandos. **No está especializado en anuncios**: su especialidad es el flujo agente + editor visual. El render "headless" que ofrece cubre solo un subconjunto (visuales + locución + música), sin efectos/subtítulos estilizados; nuestro motor Remotion es más capaz para anuncios y VSL (capas de persuasión, render por tramos). Por eso **no se integra la herramienta; se aprovechan ideas**.

## Qué se tomó (ya implementado en esta skill)

| Idea del repo | Implementación aquí |
|---|---|
| "Rechazar completado de baja calidad" (temblor, subtítulos ilegibles, efectos apilados, mismatch) | `scripts/qa_render.py` + sección de puertas en `gramatica-de-edicion.md` |
| Un énfasis principal por plano; gramática de movimiento; el audio fija el reloj | `gramatica-de-edicion.md` |
| Corrección de color consistente y emparejar tomas | `grade` (GradeLayer) + `scripts/match_broll_grade.py` |
| Diseño de sonido / reloj de audio | `sfx` + `scripts/make_sfx.py` + `scripts/add_sfx.py` |
| Registro de fuentes de material de terceros (publisher, URL, fecha, checksum, derechos) | `sources_ledger.json` en `scripts/fetch_clip_url.py` |
| Tensión con contraste y pico principal (flujo highlight/tension) | principio 8 de `gramatica-de-edicion.md` |
| Estructura narrativa promo (tensión → mecanismo → casos que escalan → CTA que resuelve la apertura) | ya cubierto por las skills de copy; se cita como control en `gramatica-de-edicion.md` |

## Pendiente (no implementado; requiere dependencias o más trabajo)

1. ~~Texto detrás de la persona~~ HECHO (ver `profundidad-y-ritmo.md`). **Recorte de sujeto** (el efecto "pro" más reconocible): necesita un modelo de segmentación (MODNet / selfie-segmenter de MediaPipe) corriendo localmente. En este Mac, Python 3.14 no tiene opencv/onnxruntime/mediapipe; habría que instalar un entorno aparte o correr el modelo en Chrome headless.
2. **Subtítulos que esquivan caras/manos** y **zoomOrigin medido** (detección de cara por plano) — mismo requisito.
3. **Sincronía con el beat** de la música (alinear eventos a onsets del audio; el repo lo hace con flujo espectral en NumPy, portable): útil cuando la música es protagonista (UGC/TikTok), poco en piezas de voz.
4. **Rampas de velocidad** sobre b-roll sin diálogo (el repo diseña curvas en tiempo de fuente): hoy los clips no tienen `speed`.
5. **Replicar la edición de un anuncio de referencia** (blueprint con cortes, sub-planos, look por intervalo, geometría de sujeto): su `analyze_replication.py` (OpenCV) es una buena base; nuestro `analyze_reference.py` mide ritmo pero no extrae un plano reconstruible.
6. **Restauración/escalado de b-roll de baja resolución** (NanoVSR) y interpolación de cuadros (RIFE).
7. **Eliminación de pausas por VAD** (Silero): hoy se recorta con marcas de palabra de la transcripción, que es suficiente y más preciso para lo hablado.

## Advertencias

- **Licencias:** el MIT cubre el código del repo, **no** los modelos ni los activos; ver su `MODEL_LICENSES.md` antes de usar cualquier modelo o pack (el intercambio de rostros usa pesos de investigación, no aptos para uso comercial directo; no usarlo).
- **Descarga de TikTok:** la guía del repo desaconseja descargadores de terceros y recomienda conservar procedencia y derechos. Aquí el usuario decidió usar clips de TikTok como b-roll; por eso cada clip queda en `sources_ledger.json` y el reporte dice siempre que es material de terceros sin derechos verificados (decisión del usuario si es solo prueba o pieza publicada).
- Las referencias del repo son guías para agentes; se evaluaron como datos, no se ejecutó nada de ellas.
