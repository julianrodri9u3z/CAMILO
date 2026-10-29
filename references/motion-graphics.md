# Motion graphics — elementos opcionales, cualquier estilo puede usarlos

Hasta 2026-09 el motor solo tenía subtítulos + b-roll + título + keyword callout + CTA. Esto se sintió
básico frente a anuncios reales de proof/finanzas/UGC de alta producción — se amplió con una librería de
elementos de motion graphics, todos opcionales, todos disponibles para cualquier estilo (no exclusivos de
uno). Origen: escaneo real de `~/Documents/ESTILOS DE EDICIÓN ADS/` (VSL FRANQUICIA IA, ADS GAIA, JUAN
CARRIZO) — cada componente de abajo está anclado en una técnica vista en footage real del usuario, no
inventada en abstracto. Ver `components/*.tsx` en `remotion/src/` para el código; este archivo es la guía
de cuándo usar cada uno y cómo llenar sus campos en el `EditPlan`.

**Motor:** todo esto usa `@remotion/shapes` y `@remotion/paths` (ya eran dependencias instaladas, sin usar
hasta ahora) para las formas/animaciones de trazo, en vez de inventar matemática de SVG a mano. No hace
falta ninguna librería nueva.

## `statCallouts` — el número/stat gigante que se estampa en pantalla

Anclado en: JUAN CARRIZO (UGC día-en-la-vida) y VSL FRANQUICIA IA — ambos usan un número enorme al centro
("30%", "$10,000") como golpe de prueba. Distinto de `keywordCallouts` (palabra tema, más chica, arriba,
sin golpe) y de los subtítulos (diálogo hablado, no un punto de prueba).

- `text`: el texto estático ("30%"). Ignóralo si usás `countFrom`/`countTo`.
- `countFrom`/`countTo` + `prefix`/`suffix`: anima un conteo ascendente en vez de una aparición estática —
  úsalo para una cifra de dinero/resultado que debería sentirse "subiendo en vivo" (ej. `prefix: "$"`,
  `countFrom: 0`, `countTo: 10000`).
- Un stat por golpe, 1.5-2.5s de duración típica — no lo dejes tanto tiempo que deje de sentirse un golpe.

## `badges` — etiqueta pequeña tipo píldora, en una esquina

Anclado en: VSL FRANQUICIA IA — una píldora morada con ícono ("Tu primera venta") apareció mientras se
mencionaba un bono. Distinto de `title` (persistente, ancho, tipo titular) — esta es chica, transitoria,
anclada a una esquina (`position`).

- Usalo para ofertas/bonos/credenciales que se mencionan de pasada, no para el mensaje principal.
- `icon`: un solo emoji funciona bien como ícono simple (ver ejemplo abajo).

## `arrows` — flecha señalando algo en pantalla

No anclado en un ejemplo específico del usuario todavía, pero es una técnica estándar de edición de
anuncios (señalar un elemento de una captura de pantalla, un precio, una cara) — barato de construir con
`@remotion/shapes` ya instalado, así que se incluyó igual. `x`/`y` es la PUNTA de la flecha (el extremo
señalado), no la cola — así es más fácil calcular la posición mirando una captura pausada del video fuente.

## `highlightCircles` — círculo/óvalo dibujado a mano alrededor de algo

Mismo caso que `arrows`: técnica estándar, no anclada aún en un ejemplo puntual del usuario, incluida por
ser barata y de alto valor (usa el trazo progresivo de `evolvePath` de `@remotion/paths`, el mismo patrón
"se dibuja solo" que un marcador real). `x`/`y` es el CENTRO; `width`/`height` es el cuadro completo, no un
radio.

## `revenueChart` — gráfico de línea animado con contador (proof de resultados)

Anclado directamente en VSL FRANQUICIA IA: un gráfico de facturación verde con un contador brillante
("$2.883") persiguiendo la línea. El componente más elaborado de esta tanda — se construyó a medida
(no con una librería de gráficos genérica) porque el punto entero es la sincronía dibujo+contador, algo
que una librería de charts no da gratis.

- `points`: cualquier lista de valores crudos (no normalizados) — ej. facturación diaria del período que
  quieras mostrar.
- Como mucho uno por video — es un momento de clímax, no un elemento de fondo.
- Reservalo para anuncios de negocio/dinero con una cifra de resultado real y verificable que el usuario
  te confirme — nunca inventes los números del gráfico.

## `vignette` — viñeta oscura para un tramo dramático

Anclado en ADS GAIA: viñeta pesada + resplandor sobre b-roll simbólico/AI para el ángulo
místico/conspirativo del anuncio. No es exclusivo de `cinematografico` — cualquier estilo puede pedirlo
para el tramo que necesite ese tono más serio. Omití `atMs`/`durationMs` para todo el video, o acotalo a
una sección.

## Variante de subtítulo `"bar"` (nueva, en `Captions.tsx`)

Anclada en VSL FRANQUICIA IA: una barra sólida negra de ancho completo con la línea hablada, distinta de
las 6 variantes anteriores (todas texto flotante sin fondo). Encaja bien en formatos tipo entrevista/
talking-head donde una franja de subtítulo persistente se siente más "producido" que texto hype
palabra-por-palabra.

## `mainClipZoomPunch` (campo de `StyleConfig`, no del `EditPlan`)

`BrollLayer` ya tenía zoom-punch-in en los inserts; ahora el clip PRINCIPAL también puede tenerlo
(`styleConfig.mainClipZoomPunch`). Es una palanca grande para el ritmo "UGC energético" que antes solo
existía en el b-roll. Se agregó como `true` a los mismos estilos que ya tenían `brollZoomPunchIn: true`
(ugc-ia, tiktok, chisme, voz-en-off-ugc) como punto de partida — ajustalo por estilo si un análisis real
dice lo contrario.

## Transiciones ampliadas (`TransitionKind` en `styles/config.ts`)

Antes solo había `fade`/`slide`/`none` (hechas a mano). Ahora también están disponibles las
`presentations` propias de `@remotion/transitions` (dependencia ya instalada, sin usar hasta 2026-09):
`zoomBlur`, `crossZoom`, `wipe`, `iris`, `filmBurn`, `dreamyZoom`, `pushCut`. Puntos de partida por
estado de ánimo (no verificados contra referencia real todavía, son la intuición de por qué existen —
confirmá contra una referencia real antes de fijarlo como default de un estilo):
`zoomBlur`/`crossZoom` para UGC/TikTok con energía, `filmBurn` para cinematográfico/chisme,
`dreamyZoom` para espiritual/voz-en-off, `wipe`/`iris` para una revelación tipo chisme.

**`zoomBlur`, `crossZoom`, `filmBurn` y `dreamyZoom` necesitan WebGL2** — sin `--gl=angle` en el render
fallan con `Failed to create WebGL2 context` (ver SKILL.md paso 9). `fade`, `slide`, `wipe`, `iris`,
`pushCut` son CSS puro, no lo necesitan, pero el flag no molesta — ponelo siempre.

## Segunda tanda (2026-09-23): anclada en ADS ELIDA, ADS GAIA, JUAN CARRIZO y reels sueltos

Todos opcionales y con `x`/`y` = CENTRO en el marco de referencia 1080x1920. Las capturas/logos
son archivos que aporta el usuario (van en `remotion/public/jobs/<slug>/`); **nunca fabricar
pruebas** (capturas de ingresos, notificaciones bancarias, testimonios).

| Campo del EditPlan | Qué es | Visto en |
|---|---|---|
| `stickers` | Emoji o logo (`src`) que aparece con rebote junto a la persona, sincronizado a una palabra. Dos stickers + una "x" = encabezado "A x B". | elida3, 4, 6 |
| `listSidebar` | Lista numerada 1..N en el borde izquierdo; cada slot se llena con un icono cuando se nombra el item. Uno por video. | elida3 |
| `imageCards` | Tarjeta flotante con sombra: pantallazo de pago, dashboard, lockscreen con notificaciones. | elida1, 8, 9, root2 |
| `questionStickers` | Sticker de pregunta de Instagram ("Hazme una pregunta"). Sin `atMs`/`durationMs` = todo el video. | root1, root2 |
| `bubbles` | Burbuja circular PIP (imagen o video mudo): clienta, reacción, llamada. | root1 |
| `lowerThirds` | Nombre + credencial con barra oscura y línea de acento. | ADS GAIA (7) |
| `brandBugs` | Marca persistente en una esquina superior (texto y/o logo). | ADS GAIA |
| `title` con `bg:"none"`, `position:"topEdge"`, `color` | Título "POV: ..." sin caja pegado arriba (blanco o amarillo). | elida1, 5, 7, 9 |
| `captions[].emphasis` | Marca la palabra a resaltar (usada por `wordBox` y `kinetic`). | elida2, gaia6, carrizo |

**Nuevas variantes de subtítulo** (`captionVariant` en `styles/config.ts`):
- `active` — 3-4 palabras, mixed case, contorno negro, la palabra hablada en `highlightColor`
  (el look más común de creadora, ~1/3 de los ejemplos). Distinto de `karaoke` (mayúsculas, anclado arriba).
- `chip` — 1-3 palabras en cápsula de color (`highlightColor`), texto `color`.
- `wordBox` — mayúsculas con caja de color solo en la(s) palabra(s) con `emphasis`; sin ninguna marcada, en la palabra activa.
- `native` — minúsculas blancas con sombra, sin contorno: el subtítulo automático de la app.
- `boxed` — frase entera sobre caja ajustada (`color` = texto, `highlightColor` = caja): subtítulo de broadcast.
- `kinetic` — palabras apiladas de a una, izquierda, la de `emphasis` enorme y en negrita.

Las variantes se probaron con un render de humo (stills) antes de documentarse; los captions se
dibujan **encima de todos los overlays** para que una tarjeta o sticker nunca los tape.

**Estilos nuevos** que usan estos elementos: `ugc-creador` (12 ejemplos), `editorial-lifestyle`
(2, candidato), `trailer-documental` (7). Ver `references/estilos/*.md`.

## Cómo probar un componente nuevo antes de confiarlo a una campaña real

No hay una composición de humo permanente para esto (se armó y se borró una temporal, `_Demo.tsx`, durante
la sesión que agregó esta librería). Para verificar algo nuevo: generá un clip de fondo plano
(`ffmpeg -f lavfi -i color=c=0x30261c:s=1080x1920:d=9 ...`), copialo a `remotion/public/jobs/<slug>/`,
armá un `EditPlan` mínimo que dispare el elemento en cuestión, renderizá con `--gl=angle`, y sacá frames
con `ffmpeg -ss <t> -frames:v 1` en los instantes donde el elemento debería estar visible — mismo patrón
que el resto de la auto-revisión de esta skill (paso 10).

## Lote 3 — elementos de VSL

`CtaButton`, `CountdownTimer`, `PriceStack`, `GuaranteeSeal`, `TitleCard`, `ProofStack`, `ComparisonTable` (+ `StatCallout` con `x/y/size/glow`, y `Clip.zoom/zoomOrigin`). Campos en `EditPlan.ts` (`ctaButtons`, `countdownTimer`, `priceStacks`, `guaranteeSeals`, `titleCards`, `proofStacks`, `comparisonTables`). Composición `Vsl`. Cómo usarlos por bloque: skill `editar-vsl` (`references/recetas-visuales.md`). Solo con material real del usuario.
