# Estilo: TikTok

**Estado:** perfil semilla (0 ejemplos reales analizados). **Nota 2026-09-23:** se probaron 12 videos de creadoras (ADS ELIDA + reels sueltos) y NO encajaron aquí (son plano secuencia, ~3 cortes/min, no ~40): pasaron al estilo nuevo `ugc-creador`. Los 2 reels de JUAN CARRIZO (48-55 cortes/min, tipografía cinética) son lo más parecido a este semilla y quedaron en `editorial-lifestyle` (candidato). Este perfil sigue sin ejemplos propios — genérico hasta que se
analice al menos un anuncio de referencia con `analyze_reference.py`. Ver
`tiktok.json` para los números que el motor de Remotion usa en cada render.

## Sensación que persigue

Nativo de la plataforma, rápido, denso en estímulos — compite por atención cada
medio segundo. Es el más agresivo de los tres estilos.

## Ritmo de corte

- Plano promedio ~1.4s, el más rápido de los tres (~40 cortes/min). El ritmo casi
  nunca baja — si algo, se acelera hacia ganchos/remates.

## Transiciones

Slide/whip pan rápido entre planos, zoom punch-in en los cortes clave, hard cuts
en el resto. Todo suma velocidad — nada de crossfades lentos.

## Subtítulos

Palabra por palabra tipo karaoke pero más grandes y "rebotados" (spring/bounce en
vez de fade). Fuente bold/condensada.

**Color por defecto ya corregido en el motor** (`styles/config.ts`, estilo
TIKTOK): relleno blanco sólido con contorno negro grueso (`captionColor:
"#000000"` = contorno, `captionHighlightColor: "#FFFFFF"` = relleno) para la
palabra activa, calibrado contra una referencia real del usuario (@immortal.unc)
que no tenía video descargable para correr `analyze_reference.py` -- por eso no
hay métricas de `n_ejemplos_analizados` de esto todavía, pero el default de
color YA no es genérico, no lo cambies a cian/amarillo neón sin que el usuario
lo pida explícitamente.

### Título superior (banner)

Este estilo también soporta un banner de título fijo arriba del frame (campo
`title` del EditPlan, ver Parte B paso 7b de `SKILL.md`) -- caja blanca
redondeada, texto negro bold mayúscula, una sola línea salvo pedido contrario,
posicionado justo encima de la cabeza del sujeto. Es un elemento aparte de los
subtítulos karaoke de abajo, úsalo solo si el usuario pide un título tipo
"POV: ..." además de los subtítulos.

## Música

Sonido de trend o trap/hyperpop, energía alta y constante, cortes idealmente
sincronizados a la batida cuando se pueda estimar el tempo.

## B-roll

Uso medio-alto (~35%), insertos rápidos (pantallas de celular, memes, reacciones,
detalles) que refuerzan el gancho verbal casi en tiempo real.

## Color grading

Saturado, vibrante, contraste alto — el opuesto del cinematográfico. Puede tener
un look "sobreexpuesto" intencional típico del contenido nativo de la app.

## Cómo se actualiza este perfil

Cada vez que el usuario suba un anuncio de referencia marcado como "TikTok",
correr el pipeline de `analyze_reference.py` (metrics + twelvelabs si hay clave)
y fusionar los hallazgos con `update-profile`. Después de fusionar, releer el
JSON actualizado y ajustar el texto de arriba a mano si algo cambió de forma
notable.
