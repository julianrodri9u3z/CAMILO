# Reglas de edición de Antonio — OBLIGATORIAS

Fuente: tres clases de Antonio Mario Espiña (Coherencia, Textos, Volumen de la música y efectos de sonido),
transcritas y estudiadas el 2026-10-28. El usuario pidió aplicarlas **al pie de la letra en cada edición**.
Cuando un perfil de estilo, un default del motor o cualquier otra guía de esta skill choque con estas
reglas, **ganan estas reglas**. Si una regla no se puede cumplir en un video concreto, dilo en el reporte.

**La filosofía:** la agencia vende *piezas audiovisuales premium*: ediciones **sencillas, fluidas y elegantes,
con los detalles pulidos**. No buscamos la súper mega edición. Un solo detalle mal hecho (una letra suelta,
un b-roll que no pega, un efecto muy alto) es "una manchita negra en una sábana blanca": baja la percepción
de valor del experto. Todo es una unidad: audio, subtítulos, b-roll, color y música cuentan la misma emoción.

**Regla del niño de 5 años:** si un niño de 5 años lo entiende y al 50 % de las personas les gusta, se pone.
Si no, se omite.

---

## 1. Volumen de música y efectos de sonido

- **Regla 70/30.** La voz va alrededor de **0** en el medidor. Los efectos de sonido van entre **−20 y −30 dB**
  (lo recomendado, −30). **Nunca por encima de −12.** Un efecto al 40-50 % de la voz la opaca y "no se entiende
  el mensaje": ya no se acepta ni un solo video con efectos altos.
  → `scripts/add_sfx.py` nivela cada efecto midiendo el pico real de la voz (`--db-under 25` por defecto,
  permitido 20-30).
- **No repetir el mismo efecto seguido.** El mismo sonido en poco tiempo suena monótono y le quita esencia al
  video. Se varía (cachín / campana / caja registradora; pop / clic). Excepción: una *secuencia* deliberada
  (enumeración "preguntar, diagnosticar…", una lista que se va contando) sí puede repetir el sonido.
  → `add_sfx.py` cambia cualquier repetición en una ventana de 3 s por otro sonido de la misma familia.
- **Dinero = cachín.** Siempre que se diga dinero, compra, vender, vendí, ganar, una cifra… va un cachín
  (`sfx/cash.wav`). Un concepto clave con nombre propio (el "método X") lleva una campana (`ding`).
- **Los efectos acompañan animaciones.** Cada texto animado, zoom, transición o palabra clave lleva su efecto.
  Si dos textos aparecen juntos, no los animes igual: uno sube y el otro entra distinto.
- **Pocos efectos, bien usados.** Con unos 6 sonidos se hace todo: tensión (riser), transición (whoosh),
  énfasis de una emoción fuerte (hit), acompañar zooms, palabras clave (pop/ding), teclado.
- **Prueba de la cabeza:** reproducir el video con los ojos cerrados e imaginar dónde va cada efecto; si
  con solo los efectos el video te retiene el minuto entero, está hecho.

### Música
- **La música tiene que conectar con la emoción del creativo.** Una canción "de otro estilo" que no conecta
  se cambia. Nada de "música de ascensor".
  - Emoción negativa (cansancio, dolor, pérdida) → música más baja, triste.
  - Emoción positiva / solución → música que sube; algo relajante si es bienestar (cuencos tibetanos en
    limpiezas energéticas).
  - Una historia → música emocional que va subiendo y termina con un beat alto que emociona.
  - **Anuncios de captación** (nueva oportunidad, clase gratuita, ganar dinero) → música **épica**, tipo
    tráiler, con suspenso ("Epic Drama Violin"), que la gente lo sienta.
  - Marca de perfumería / ropa / tienda → la música que suena en esas tiendas (Zara, Bershka…), estilo fashion.
- **Nivel parejo.** La música se mantiene estable bajo la voz. Si tiene picos ("va bajito y de repente
  explota"), se corta y se baja en el pico con keyframes hasta que quede pareja.
- **El drop en un momento clave.** El momento en que la música explota se coloca en un punto importante
  (por ejemplo, "Soy [nombre]…"), después de un riser.
- **El editor decide la música, no el experto.** El experto sabe si "le gusta o no"; nosotros somos los
  expertos en edición: identificar la emoción y elegir con criterio.

## 2. Textos: títulos, subtítulos y banners

- **Solo se resaltan palabras de peso**: palabras de venta, el llamado a la acción ("comenta SISTEMA"),
  y las que cargan el mensaje de *esa* narrativa. Lo demás va en subtítulo normal. Los títulos van más grandes.
- **Los subtítulos siguen la estética del experto.** Hay expertos minimalistas y otros más juguetones. El
  default de la agencia es **minimalista y fluido**.
- **Cortes coherentes de frase.** Nunca dejar una sola letra o una palabra suelta ("a", "y") sola en pantalla;
  nunca una palabrota gigante al lado de una "cata chiquitica". Agrupar por sentido ("venderle a alguien"
  junto). Que el subtítulo no pase tan rápido que no se lea.
- **Animaciones:**
  - Si los subtítulos están espaciados, bastan 2 animaciones suaves (hacia arriba / difuminado).
  - En videos dopamínicos y densos hay que variar mucho más: animaciones distintas y efectos distintos.
    Lo predecible aburre.
  - Nada de animaciones que impiden leer.
  - Las animaciones temáticas (Navidad, Halloween) se usan una vez, estratégicamente, donde la narrativa lo pide.
- **Tipografía legible, sin complicarse:** Montserrat, Poppins, Arial. Los títulos van con una tipografía de títulos.
  **Prohibido mezclar mayúsculas y minúsculas raras** (vocales con tilde en minúscula y el resto en mayúscula).
- **Contraste.** El color del texto tiene que contrastar con el fondo y con el banner; si "se mezclan los dos
  colores", no se lee. Los banners y cuadros de texto siempre legibles, que no se corten por los lados.
- **Zona segura (TikTok/Reels).** Todo texto, título, banner o emoji va dentro de la zona segura: nada bajo la
  interfaz de arriba (Explorar / Siguiendo / Para ti), ni en la columna de botones de la derecha, ni abajo donde
  va el copy de la descripción.
- **Nunca texto sobre los ojos ni la cara.** Ni en el A-roll ni en el b-roll, ni en un personaje de IA, ni en
  un animal: los ojos son lo primero que miramos. → `scripts/dodge_captions.py` y `vision_analyze.py`.
- **Psicología del color:**
  - Verde = esperanza / dinero. Una cifra de ganancia **siempre en verde**, nunca en rojo.
  - Rojo = pasión, furia. Negro = misterio, emoción negativa. Blanco = paz. Amarillo = marketing.
  - Una marca personal usa negro, blanco y un color.
- **Línea de tiempo ordenada.** Capas fijas (subtítulos en su pista, b-roll en la suya…). "Como editas, así vives."

## 3. Coherencia (b-roll y narrativa)

- **El b-roll es literal a lo que se dice.** "Si se menciona perro negro, se pone un perro negro." Un perfume
  cítrico con notas dulces → naranjas y fresas detrás del frasco.
- **Todo el ecosistema sigue la emoción:**
  - Emoción negativa (robo, quiebra, hambre, tristeza) → b-roll triste, en **blanco y negro**, música sad,
    efectos sad, eco suave en la voz para más tensión y un riser.
  - Emoción positiva → b-roll luminoso y música que sube.
  - Un video que pasa de lo negativo a lo positivo cambia todo el paquete en ese punto.
- **El b-roll respeta el estatus y el estilo del experto.** Si el experto quiere verse caro y elegante →
  b-roll elegante (suéter negro básico, buen pantalón, reloj, cadena). **Nunca** b-roll de gorra para atrás,
  chanclas o pantaloneta, ni aunque el experto lo mande. Un experto de estilo fresco sí admite b-roll fresco:
  hay que respetar su esencia.
- **Percepción premium.** B-roll estético y de alta calidad que transmita estatus y valor (el cerebro asocia
  estatus con supervivencia). Si el material del experto no alcanza, generar b-roll con IA de calidad.
- **Color primero.** Antes de editar, corregir color para que todas las tomas tengan una tonalidad completa
  y pareja (`grade` del EditPlan + `match_broll_grade.py`).
- **Zooms con medida.** Si el material ya viene con zooms del filmmaker, añadir muy pocos. Mantener la
  **línea de ojos** a la misma altura entre tomas y zooms.
- **Varias tomas → la mejor parte de cada una**, ordenadas para que la narrativa tenga sentido.
- **Autoridad.** Si aparece alguien conocido, mostrar su prueba social (por ejemplo, un motion con su
  Instagram y número de seguidores).

## Checklist antes de entregar (además de `qa_render.py`)

1. ¿Efectos entre −20 y −30 dB bajo la voz, sin ninguno que la opaque?
2. ¿Ningún efecto repetido seguido salvo secuencias? ¿Cachín en cada mención de dinero?
3. ¿La música conecta con la emoción de cada tramo, a nivel parejo, con el drop en un momento clave?
4. ¿Solo palabras de peso resaltadas, frases bien cortadas, sin letras sueltas, tipografía legible, buen contraste?
5. ¿Todo el texto en zona segura y nada sobre ojos ni cara (A-roll y b-roll)?
6. ¿Cifras de ganancia en verde?
7. ¿Cada b-roll es literal a lo que se dice, va con la emoción y con el estatus del experto?
8. ¿Color parejo entre tomas y línea de ojos estable?
9. ¿Lo entendería un niño de 5 años? Si algo no, quitarlo.
