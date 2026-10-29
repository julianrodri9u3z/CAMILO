# Profundidad, subtítulos que esquivan y ritmo con la música

Tres capacidades que cierran la brecha con una edición humana. Probadas el 2026-10-06 con el clip de entrevista de prueba.

## 1. Texto detrás de la persona (`behindText`)

Tres capas: video normal → texto grande → copia del video recortada con la máscara de la persona. La cabeza y los hombros quedan **delante** del texto.

Pasos:
1. `python3 scripts/vision_analyze.py --video raw.mp4 --out DIR [--start S --dur D]` — máscaras por fotograma (`DIR/matte/m_000001.png`, RGBA, alfa = persona) y `DIR/zones.json` (cara, manos, caja de la persona). El comando es **el mismo en todos los sistemas** y elige el motor solo: **macOS → Apple Vision** (sin instalar nada; ~17 fotogramas/s; la primera vez compila el Swift, ~40 s, requiere Xcode Command Line Tools) y **Windows/Linux (o Mac sin Swift) → MediaPipe** en un entorno privado que crea `python3 scripts/vision_setup.py --yes` (~400 MB, pide permiso al usuario; necesita Python 3.9-3.12). Medido contra Apple Vision en los mismos fotogramas: IoU de la máscara 0.985, mismas caras/manos, ~12 fotogramas/s. `python3 scripts/env_check.py` dice cuál toca y qué falta.
2. `python3 scripts/add_behind_text.py --plan job.json --zones DIR/zones.json --matte-dir DIR/matte --job <slug> --text "DEPRESSION" --at-ms 500 --dur-ms 1700 [--color "#FFD84A"]` — calcula la posición con la altura medida de la cabeza, copia solo las máscaras necesarias a `remotion/public/jobs/<slug>/matte/` y agrega la entrada al plan.
3. Verificar con `remotion still` en el medio de cada ventana.

Reglas (aprendidas probándolo):
- **Ventanas de 1.5-3 s en un plano estable donde la cabeza no toca el borde superior.** El script se niega si no hay espacio ("head touches the top edge"): en primeros planos no hay dónde poner el texto detrás.
- **Texto largo y ancho** (9+ caracteres, ej. "DEPRESSION", "YEARS LATER"): solo se tapa el centro. Una palabra corta ("2017") queda casi toda oculta tras la cabeza: usar una frase más larga o no aplicarlo.
- Solo en estilos de corte duro (transition `none`); nunca sobre b-roll (el script lo verifica).
- Una o dos veces por video, en el gancho y en un giro; es el efecto más reconocible y se gasta si se abusa.
- La máscara y el recorte (`zoom`) del clip se aplican igual a la copia, así que sigue alineada.
- Multiplataforma: ver arriba. Si `env_check.py` dice que falta el motor de visión y el usuario no quiere instalarlo, omitir `behindText` y la esquiva de subtítulos (no son imprescindibles). La parte MediaPipe está probada en Mac; en Windows se espera que funcione igual (mismo código, ruedas oficiales de Python 3.9-3.12) pero aún no se ha probado allí.

## 2. Subtítulos que esquivan caras y manos

`python3 scripts/dodge_captions.py --plan job.json --zones DIR/zones.json`

Para cada frase de subtítulo (mismo agrupamiento que la variante `kinetic`: pausa > 450 ms o 4 palabras) mide el solapamiento de la posición por defecto con las cajas de cara/manos (con el zoom del clip aplicado) y, si pasa de un umbral, mueve esa frase a izquierda/centro/derecha y/o la sube. Las frases que ya están libres no se tocan, para que el look sea constante. Escribe `anchor`/`liftPx` en la primera palabra de la frase. En la prueba: 54 frases revisadas, 6 movidas, solapamiento medio 0.067 → 0.010.
Pendiente: la variante `native`/`boxed` aún no lee `anchor`.

## 3. Cortes y gráficos alineados con la música

"Oír" numéricamente, sin oído:
- `python3 scripts/beat_grid.py --audio music.mp3 --out beats.json` — BPM, rejilla de pulsos, tiempos fuertes (downbeats), onsets y **drops de graves**. Solo numpy + ffmpeg. **Validado contra pistas sintéticas con verdad conocida**: tempo con error < 0.5 %, error de cada pulso mediana 14-19 ms (p90 ≤ 28 ms) a 95/120/140 BPM. (La primera versión se enganchaba a los hi-hats; se corrigió con flujo espectral ponderado por bandas.)
- `python3 scripts/beat_snap.py --plan job.json --beats beats.json [--tol-ms 140] [--align-drop VIDEO_MS --drop-index N]` — mueve el inicio de overlays/b-roll al pulso más cercano dentro de la tolerancia (los cortes ligados al habla **no** se tocan) y/o fija `musicOffsetSeconds` para que un drop caiga exactamente en un momento clave (revelación de precio, primer CTA). Imprime la distancia media al pulso antes/después (en la prueba: 146 ms → 74 ms).
- Orden correcto: `beat_snap` **antes** de `add_sfx` (para que los sonidos sigan a los eventos ya movidos).
- Útil cuando la música es protagonista (UGC, montaje, promo). En piezas guiadas por la voz con música a -25 dB no se siente: usar `--tol-ms 0` o saltarlo.

## Oídos para verificar: qué se puede y qué no

1. **Números (fiables):** `qa_render.py` (LUFS, picos, silencios), diferencia entre dos renders para localizar cada efecto, relación efecto/mezcla en dB, espectro de cada sonido. Así se descubrió que el golpe grave tenía 98.6 % de energía por debajo de 120 Hz: **inaudible en bocinas de celular**.
2. **Modelo que escucha (NO fiable como verificador):** `python3 scripts/listen_check.py --video final.mp4` (TwelveLabs Pegasus, clave ya configurada). Se probó dos veces y es inconsistente: la primera dijo "música de fondo sutil, ningún efecto" en una mezcla con 6 efectos (coherente con los números: whooshes 9-14 dB bajo la voz); la segunda, con una mezcla que sí tenía música y 9 efectos más audibles, dijo "no hay música ni otras capas, ningún efecto". Un modelo de video que ignora capas enteras no sirve para aprobar un mix: se conserva solo como segunda opinión orientativa y nunca sustituye a los números ni al usuario.
3. **Oído humano (final):** la decisión de gusto es del usuario; se le pide escuchar y se le dice qué escuchar.
Alternativas si se quiere más: la API de audio de Gemini (requiere una clave del usuario) o modelos de audio locales (pesados).

## Principios de movimiento tomados del kit `motion-video` (zip del usuario)

Regla "cero retenciones muertas" (todo elemento sigue en deriva suave tras llegar: `behindText` ya lleva una deriva de escala), eventos que se solapan 4-12 fotogramas, salidas que continúan el impulso, resortes suaves en tarjetas, desenfoque de movimiento en lo rápido. El kit es un motor distinto (canvas, motion graphics desde cero, sin footage); de él se reutilizaron ideas: el análisis de drops (`music.py`), el recorte de persona (`cutout.swift` → `vision_analyze.swift` por fotograma) y la biblioteca de sonidos sintetizados.
