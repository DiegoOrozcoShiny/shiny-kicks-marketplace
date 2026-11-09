---
name: "shiny-kicks-video-reel"
description: "Edita videos de Shiny Kicks para Reels/TikTok (9:16): pregunta el tema, analiza el video, propone storyboard para autorizar y luego renderiza textos animados, zooms, SFX/música y copy."
---

# Shiny Kicks · Edición de Reels con storyboard aprobado

Flujo para cuando Diego sube un video crudo y llama este skill. **Nunca editar antes de que Diego autorice el storyboard.** Todo en español, directo y estructurado.

## 0. Reglas de marca (siempre)

- Colores: Pure White #FFFFFF, Accent Gold #FFB92E, Black Matte #1A1A1A / #000000.
- Tipografía de video: **Montserrat** Black (900) en textos grandes, en MAYÚSCULAS; Montserrat SemiBold (600) en textos chicos, en minúsculas/tipo oración. Sombra suave negra, sin cajas detrás del texto (texto integrado en la imagen).
- Tono: técnico, sofisticado, sobrio, aspiracional, directo. Nunca informal en exceso.
- Datos fijos: sucursales Metepec y Toluca · WhatsApp 729 157 9406 · +7 años · fórmulas de fabricación propia · tagline "Shiny steps takes you to shiny places…". Confirmar promos y horarios vigentes con Diego (no inventar).
- Formato de salida: 1080×1920, 9:16, 30 fps, H.264 + AAC, `-movflags +faststart`. Zonas seguras de Reels: no poner texto clave en los 220 px superiores, los ~420 px inferiores ni los ~140 px del lado derecho (si un texto del storyboard queda ahí, avisarlo).

## 1. Preguntar el tema (AskUserQuestion)

Antes de analizar a fondo, preguntar en una sola ronda:
1. Tema / objetivo del video (promo, proceso, antes-después, educativo…).
2. Mensaje clave y datos de la oferta (qué, cuándo, condiciones).
3. CTA y canal (WhatsApp por defecto: 729 157 9406).
4. Preferencia de audio (beat original libre de regalías / canción con licencia / solo SFX).

## 2. Analizar el video

```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of compact VIDEO
ffmpeg -i VIDEO -af volumedetect -f null - 2>&1 | grep -E "mean_vol|max_vol"   # ¿trae audio o está en silencio?
ffmpeg -i VIDEO -vf "select='gt(scene,0.25)',showinfo" -f null - 2>&1 | grep -o "pts_time:[0-9.]*"  # cortes
```

- Sacar una cuadrícula de frames a 1 fps y otra a 0.5 s con timestamp (`drawtext`) en los tramos de acción, y **verlas** con Read.
- Identificar: tomas, cortes, momentos de acción exactos (p. ej. cuándo entra cada producto), pausas muertas (candidatas a speed ramp 2x) y el final limpio (ideal para el CTA).
- La historia la debe contar la acción del video; el texto la acompaña (p. ej. conteo 1·2·3 sincronizado con cada par).

## 3. Storyboard para autorizar (Artifact HTML)

Publicar un storyboard como Artifact (página HTML, tema oscuro de marca) con:
- Encabezado: qué pasa en el video, specs (duración original/final, resolución), tipografía y colores.
- Barra de línea de tiempo por bloques: GANCHO → desarrollo → remate → CTA.
- **Una tarjeta por escena**: frame real del video (JPG en base64) con el mockup del texto encima + ficha: tiempo · toma · texto en pantalla (con alternativas en el gancho) · animación del texto · efecto/cámara · audio/SFX.
- Propuesta de audio: 3 opciones (marcar la recomendada) + tabla de SFX por segundo + nota de derechos (cuentas de empresa solo pueden usar la biblioteca comercial de IG/TikTok) + voz en off opcional.
- Sección "Por confirmar antes de editar" (gancho, número/CTA, sucursales, música, ajustes de ritmo).

**Regla crítica aprendida:** los mockups del storyboard deben usar exactamente el mismo CSS (fuente, tamaños en `cqw`, posiciones flex, sombras) que se usará para renderizar el video. En el video final se reutiliza ese CSS tal cual (ver paso 5), para que tipografía, tamaño y posición sean idénticos a lo aprobado.

Esquema de mockup por escena (frame 9:16 con `container-type:inline-size`):
```css
.ov{position:absolute;inset:0;display:flex;flex-direction:column;padding:9cqw;gap:2cqw}
.t{font-weight:900;line-height:.95;text-transform:uppercase;letter-spacing:-.01em;text-shadow:0 2px 10px rgba(0,0,0,.55)}
.s{font-weight:600;font-size:6.5cqw;color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.7)}
.w{color:#fff} .g{color:#FFB92E}
```
Tamaños de referencia: gancho 15–24cqw · número/oferta gigante 40–42cqw · CTA 9–13cqw · lista 12cqw.

Terminar con una pregunta concreta y **esperar autorización**. Aplicar los cambios que pida y republicar el mismo storyboard si hay cambios grandes.

## 4. Estructura narrativa probada

1. **Gancho (0–1.5 s):** pregunta directa al dolor ("¿TIENES 3 PARES SUCIOS?"), palabra por palabra con slam (escala 145%→100% con rebote) + punch-in 115%→104%, micro-shake de 3 frames y flash blanco de 2 frames.
2. **Transición:** texto puente ("Los sábados / CAMBIAN"), typewriter + subida con máscara; zoom-blur hacia el corte.
3. **Revelación:** oferta gigante en dorado ("3x2") con pop y barrido de brillo.
4. **Desarrollo sincronizado con la acción:** contadores/pasos que aparecen justo cuando ocurre la acción, cada uno con punch-in del 6% (el último del 10%, con glow y flash).
5. **Remate:** "el más barato / ¡GRATIS!" con stamp (escala 210%→100%) + destellos dorados.
6. **Alcance:** lista en cascada que entra desde la izquierda (tenis · gorras · botas · calzado formal).
7. **CTA (≥3 s):** sobre el set vacío o la toma final: desenfoque + degradado oscuro; marca, día/horario, sucursales, "Cotiza por WhatsApp ↓" + número en dorado, con pulso suave. Congelar el último frame y extenderlo +0.5 s si hace falta.

## 5. Pipeline de render (cloud)

1. **Fuente Montserrat:** Google Fonts puede estar bloqueado en el sandbox → `npm pack @fontsource/montserrat@5.0.18` y usar los `.woff2` de los pesos 600 y 900 (`files/montserrat-latin-*-normal.woff2`) con `@font-face file://`.
2. **Capas de texto con Chromium (Playwright):** página de 1080×1920 con el MISMO markup/CSS del storyboard (escalar las sombras ×4.9: `0 10px 49px`). Por cada elemento: dejar visible solo ese, `screenshot(omit_background=True)` → PNG RGBA de pantalla completa + guardar su `getBoundingClientRect` (y el rango de texto) para el centro de las animaciones.
3. **Compositor en Python** (numpy + OpenCV + PIL), leyendo el video fuente a resolución completa con `ffmpeg -f rawvideo` y escribiendo por pipe a `libx264 -crf 17`:
   - Remapeo de tiempo salida→fuente lineal por tramos (speed ramps, freeze final).
   - Cámara: zoom con `warpAffine` sobre el frame original (sin pérdida), punches con easing out-cubic de ~0.3 s, zoom-blur (promedio de 7 escalas) en transiciones, shake, flashes, viñeta suave.
   - Animaciones de capa: slam, pop (easeOutBack), stamp, fade+escala, slide, flip in/out, wipe (typewriter), rise con máscara, barrido de brillo, glow, pulso; destellos dibujados como estrellas de 4 puntas.
   - Antes del render completo, renderizar **frames de prueba** en momentos clave, armar una cuadrícula y revisarla con Read (y compararla con capturas del storyboard).
4. **Verificar** cortes con detección de escenas y duración/resolución con ffprobe.

## 6. Audio

- **Beat original (libre de regalías):** sintetizar en numpy un boom-bap ~92 BPM (bombo, caja, hats con swing, bajo, acordes tipo Rhodes, crackle de vinilo); drop en la revelación, low-pass en el CTA y golpe final.
- **SFX** (siempre, sincronizados): golpe de bajo + impacto en el gancho, ticks de typewriter, whoosh en transiciones, golpe de bolsa/objeto, ding en la revelación, clap + sub en cada contador, riser en el speed ramp, caja registradora en "¡GRATIS!", whoosh ascendente, golpe final.
- **Canción con licencia:** solo si Diego sube el archivo (nunca descargar música). Cortar desde el segundo que indique, detectar beats con `librosa.beat.beat_track`, y anclar cortes, contadores, zooms y entradas de texto a beats/medios beats/dieciseisavos ajustando el remapeo de velocidad (mantener velocidades entre ~0.8x y 2x). Canción de fondo (~0.85) + SFX (~0.45). Marcar el archivo como `_PRUEBA` y advertir que no se publique sin licencia.
- Master: `loudnorm=I=-14:TP=-1.5:LRA=11`, AAC 192 kbps.
- Entregar siempre dos versiones cuando aplique: con música + SFX y solo SFX (para poner audio en tendencia desde la app).

## 7. Entrega

- Archivos en `/mnt/user-data/outputs/` con nombres claros (`ShinyKicks_<Tema>_Reel[_soloSFX|_PRUEBA].mp4`).
- Mensaje final corto: qué lleva cada versión y cualquier diferencia vs. el storyboard (explicarla con honestidad).
- Ofrecer ajustes puntuales (texto, timing, volumen, posición en zonas seguras).

## 8. Copy para el post

Al cerrar, ofrecer el copy de Instagram:
- **Gancho controversial MUY corto en el primer renglón** (3–6 palabras, p. ej. "Deja de lavar tus tenis en casa.") + 2 alternativas.
- Cuerpo: dolor → oferta → detalles con íconos (servicios, horario, sucursales) → autoridad (+7 años, fórmulas propias) → CTA WhatsApp → tagline → hashtags (#ShinyKicks #SneakerLaundry #LimpiezaDeTenis #SneakerCare #Metepec #Toluca #Sneakerheads).
- Entregarlo en bloque de código listo para pegar.
## 9. Scripts de referencia

En `scripts/` está la implementación usada en el Reel "Sábados 3x2" (ajustar rutas, tiempos y textos a cada video nuevo; no ejecutarlos tal cual):
- `layers.py`: genera las capas de texto con Chromium usando el CSS exacto del storyboard.
- `render3.py` + `timing.py`: compositor (remapeo de tiempo anclado a beats, zooms, transiciones, animaciones de texto).
- `audio.py`: beat boom-bap original + SFX. `audio3.py`: canción con licencia de fondo + SFX re-sincronizados.
