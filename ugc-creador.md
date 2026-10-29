# Estilo: UGC creador (talking head real con overlays)

**Estado:** 12 ejemplos reales analizados (2026-09-23): 9 de `ADS ELIDA - GANAR DINERO/`
(afiliadas brasileñas de Kiwify/TikTok Shop) + 3 reels sueltos de la raíz de
`~/Documents/ESTILOS DE EDICIÓN ADS/` (2 de Instagram tipo Q&A, 1 de TikTok de
@itsfabianacarrasco). Ningún archivo estaba ya contado. Ver `ugc-creador.json`.

**Por qué es un estilo aparte y no `tiktok` ni `ugc-ia`:** al principio estos videos se
fusionaron en `tiktok`, pero el perfil semilla de `tiktok` describe otra cosa (~40
cortes/min, whip pans, palabra gigante con rebote) y ningún ejemplo real lo cumple. `ugc-ia`
(4 ejemplos) es selfie + b-roll aspiracional a ~23 cortes/min. Estos 12 son **plano
secuencia o casi**: la edición es mínima y el ritmo lo ponen los **overlays** encima. Es
además el estilo más cercano a lo que produce `video-ads-avatar` (persona a cámara), así
que es probablemente el más útil para los anuncios con avatar.

## Ritmo de corte

Bimodal, no un promedio:
- **Plano secuencia, 0 cortes** (elida1, 2, 3, 4, root3): el video entero es una toma
  (42s-3min). El interés lo sostienen la acción física (ordenar la cocina, hacer
  malabares con una pelota, caminar), los overlays y los subtítulos.
- **Pocos cortes duros, 0.4-2 cortes/min** (elida5, 6, 7): sketches de auto o recorridos.
- **Editado ligero, 5.7-9.4 cortes/min** (elida8, 9, root1, root2): b-roll de prueba
  (pantallas, eventos) intercalado.
Media 2.9 cortes/min; plano medio ~5.4s solo contando los que sí cortan. **No** aplicar
zoom-punch de UGC-IA ni ritmo TikTok: rompe la sensación de "toma real".

## Overlays (la identidad del estilo) — ver `references/motion-graphics.md`

- **Título "POV" sin caja** arriba (elida1, 5, 7, 9): blanco (cocina/historia) o amarillo
  (sketches del auto), 2-4 líneas, con contorno/sombra. `title.bg = "none"`, `position =
  "topEdge"`.
- **Stickers/logos con rebote** sincronizados a la palabra (elida3, 4, 6): WhatsApp, TikTok
  Shop, Shopee, cohete, carrito. Comparación "A x B" con dos logos y una "x" (elida4).
- **Lista numerada lateral 1-8** cuyos slots se llenan de iconos (elida3).
- **Tarjetas de prueba flotantes**: pantallazo Kiwify (elida1), dashboard "Total faturado"
  (elida8), notificaciones Nubank en lockscreen (elida9), "Ingreso Neto USD 500,00"
  (root2). Solo con capturas reales que aporte el usuario.
- **Sticker de pregunta de Instagram** (root1 al inicio, root2 todo el video) como gancho.
- **Burbujas PIP circulares** de otra persona/clienta (root1) y **flechas rojas** al CTA.
- **Stat neón** ("DEZ → 10.000", elida6) y **CTA tipo sticker**: "CLIQUE EM SAIBA MAIS" en
  letra manuscrita sobre pincelada rosa con destellos (elida8) o serif dorado (elida9).

## Subtítulos (varían, decidir mirando la referencia)

- **`active`** (el más común, ~1/3: elida1, 5, 7, 9 y root2 en variante de énfasis): frase
  de 3-4 palabras, mixed case, blanco grueso con **contorno negro**, palabra activa en
  amarillo. Centro-bajo.
- **`chip`** (elida3, 4, 6): 1-3 palabras en cápsula roja redondeada, texto blanco (o naranja
  con contorno en elida6), pegada al torso.
- **`wordBox`** (elida2): mayúsculas con caja magenta/morada en la palabra enfatizada.
- **`native`** (root1, root3): minúsculas blancas pequeñas, sombra suave, sin contorno — el
  look de subtítulo automático de la app; root3 no tiene ni música.
- Mayúsculas blancas con contorno negro estándar (elida8, elida9).

## Música

`pop synth` en 11 de 12 (según TwelveLabs; fiable para audio, no para cortes), energía
media, suele estar baja bajo la voz. root3 no tiene música. Ducking agresivo: la voz manda.

## Color

Natural tipo iPhone, luz de interior, sin grading elaborado (contraste medio). **No**
sobresaturar como TikTok/chisme: la credibilidad depende de que parezca sin producir.

## Estructuras narrativas observadas

- **Historia → prueba bancaria → promesa → CTA** (elida9).
- **Sketch cómico (Uber) → giro a selfie con CTA** (elida5/7): formato repetible.
- **Pregunta de IG como gancho → respuesta a cámara con pruebas** (root1, root2).
- **Demostración física mientras habla** (ordenar, malabares) para retener en plano
  secuencia (elida1, 3, 4).

## Advertencias

- Los conteos de cortes de TwelveLabs para estos videos son inservibles (dijo "179 cortes"
  en un plano secuencia); se usó ffmpeg + revisión visual.
- Casi todos son de afiliadas de infoproductos (nicho "ganar dinero"): las pruebas son
  capturas de ingresos. **Solo usar pruebas reales del propio cliente**; nunca fabricar
  cifras ni capturas.
- El idioma es portugués/español informal; los subtítulos son de una sola voz.

## Cómo se actualiza este perfil

Igual que los demás: `analyze_reference.py metrics` + `twelvelabs` + `update-profile --style
ugc-creador`. Anotar qué overlays usa cada ejemplo nuevo. `update-profile` no guarda más de
10 notas, así que este archivo es la memoria completa.
