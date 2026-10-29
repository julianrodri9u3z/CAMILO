# Enriquecimiento visual — que la imagen diga lo que dice la voz

Feedback del usuario tras la primera edición real de prueba (clip de podcast de The Rock, 2026-10-06), que le gustó mucho.
Aplica a **videos futuros**; no es una regla para rehacer lo ya entregado.

## Lo que ya funcionó (conservar)

- Estilo `PodcastClip`: subtítulos **cinéticos** (frase apilada abajo-izquierda, minúscula, palabras clave grandes). Le gustó el formato. Si el video se presta (plano centrado, cara a un lado, mucho espacio libre), también es válido ponerlos **al centro** y fáciles de leer; elegir según el encuadre.
- Música: pista instrumental suave de Jamendo (piano/ambient), ducked 0.05 / full 0.16 → "perfecta". Repetir ese criterio de volumen.
- Rotulación puntual (cartel superior, nombre en pantalla, palabra clave, cifra con brillo) sincronizada con la palabra.

## Cómo pensar el b-roll: analizar el guion y preguntarse "¿cómo muestro esto?"

Antes de elegir un solo clip, leer la transcripción y, por cada idea que se pueda ilustrar, decidir **qué prueba o imagen real la respalda**. Orden de preferencia de fuentes:

1. **La persona misma (si es una celebridad o figura pública).** Buscar en Google Imágenes / redes fotos y clips **de él/ella** relacionados con lo que cuenta (el lugar, la etapa, la familia, el momento).
2. **Actor/actriz: clips de sus películas o series.** Si dice "estaba triste", buscar una escena suya llorando o abatido; si habla de pelear, una escena de acción, etc. Hay muchísimo material en redes.
3. **TikTok antes que stock.** Los clips de apoyo se prefieren **sacados de TikTok** (se sienten reales y nativos); el stock de Pexels/Pixabay queda como último recurso porque se nota "demasiado stock" (además salen en baja resolución, 540×960).
4. **Evidencia del mundo real según lo que se diga:**
   - Habla de una **crisis** → video de noticieros donde hablen de esa crisis.
   - Nombra un **estudio, organización o institución** con respaldo → mostrarlo.
   - Habla de un **estudio científico** → buscarlo. Si **existe**, añadir una **captura donde se lea el titular en un medio** (tarjeta de imagen a pantalla casi completa). Prioridad de medios: **Forbes, Semana, The New York Times, Harvard**, etc. (los más reconocidos). Si no hay uno famoso, usar el de **mejor titular que coincida con lo que se dice**. Si el estudio **no existe, no pasa nada: no se pone nada** (nunca inventar ni retocar una captura).
5. Stock genérico solo si nada de lo anterior aplica.

## Cómo ejecutarlo con las herramientas actuales

- **Buscar candidatos en TikTok por palabra clave** (Apify, ya autorizado): `python3 scripts/find_tiktok_broll.py --query "sad man alone dark room" --out DIR` → `DIR/sheet.jpg` numerada + `candidates.json`. Mirar la hoja y elegir a ojo (los resultados son coincidencias sueltas); preferir clips **sin texto quemado ni marca de agua grande** (o recortarlos con zoom); algunos son generados con IA: decir si se usa uno. Probado: devuelve resultados relevantes (p. ej. hombre sentado en una cama oscura para 'tristeza') muy superiores al stock.
- **Descargar un clip por URL de TikTok** (probado, sin clave): `scripts/fetch_clip_url.py --url <tiktok> --job <slug> --name <nombre> [--start s --end s]` (usa `yt-dlp`, recorta y lo deja normalizado en H.264 dentro de `remotion/public/jobs/<slug>/`).
- **Encontrar el clip/imagen**: buscar con el navegador integrado (Google Imágenes, TikTok) o con WebSearch; el usuario puede pasar los links. La minería de TikTok por Apify necesita que el usuario autorice el conector.
- **Captura de un medio**: abrir la nota en el navegador y capturar el titular (o `Google Chrome --headless --screenshot`), recortar y guardar en `public/jobs/<slug>/`.
- **Insertar imágenes**: `broll[]` acepta ahora `.jpg/.png/.webp` (efecto de zoom lento tipo Ken Burns) además de video; para una captura flotante usar `imageCards`/`proofStacks`.
- Pedir/confirmar antes de renderizar qué piezas reales se encontraron; marcar en el reporte lo que **no** se encontró.
- Nota de uso: clips de películas, noticieros y fotos de terceros pueden activar reclamos de derechos en Meta/TikTok. Es decisión del usuario si es solo prueba interna o pieza para publicar; decirlo en el reporte.

## Bug conocido: imagen "pegada" (video congelado)

En la prueba, en ~3 tramos la imagen de la persona se congelaba 0.5–2 s mientras la voz y los subtítulos seguían bien. Causa: la fuente era **HEVC/H.265** (formato típico de TikTok/iPhone) con B-frames y keyframes cada ~7 s; `OffthreadVideo` la decodifica por búsqueda de tiempo y de forma intermitente repite el último fotograma. Con la misma fuente re-codificada a H.264 con keyframes cortos no hubo congelados en las ventanas probadas.

Prevención obligatoria:
1. `python3 scripts/prepare_source.py --video <crudo> --out remotion/public/jobs/<slug>/raw.mp4` antes de armar el plan (re-codifica solo si hace falta: no-H.264, GOP largo o fps variable).
2. Tras renderizar: `python3 scripts/check_freezes.py --video final.mp4 --source <crudo>` (parte de la auto-revisión). Si hay congelados que la fuente no tiene → normalizar y re-renderizar.
