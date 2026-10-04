---
name: tiemPO
description: Agentic discovery lab on ENUT 2024, read as a nine-stage spine of real artifacts inside the Education2025 shell.
colors:
  electric-blue: "#0055ff"
  electric-blue-hover: "#0047d6"
  electric-blue-press: "#0039ad"
  experiment-navy: "#002b85"
  selection-ink: "#001d5c"
  blue-wash: "#ebf1ff"
  blue-tint: "#d6e3ff"
  blue-halo: "#adc7ff"
  blue-select-ring: "#7aa5ff"
  focus-blue: "#3d7bff"
  uncertainty-yellow: "#ffc83d"
  uncertainty-yellow-ink: "#d99a00"
  live-green: "#22c55e"
  live-green-ink: "#16a34a"
  card-white: "#ffffff"
  panel-gray: "#f5f7fa"
  canvas-gray: "#e9ecf1"
  hairline-gray: "#dde2ea"
  divider-gray: "#c4cbd6"
  dash-gray: "#9aa3b2"
  quiet-gray: "#6b7385"
  body-gray: "#363d4a"
  decision-ink: "#121722"
typography:
  wordmark:
    fontFamily: "Montserrat, sans-serif"
    fontSize: "30px"
    fontWeight: 900
    lineHeight: "1"
    letterSpacing: "-0.04em"
  display:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "30px"
    fontWeight: 800
    lineHeight: "36px"
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: "36px"
    letterSpacing: "-0.01em"
  title-lg:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: "28px"
  title-md:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: "26px"
  title-sm:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: "22px"
  title-card:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: "20px"
  lead:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: "24px"
  body:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "20px"
    fontFeature: "\"cv11\", \"ss01\""
  body-sm:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: "18px"
  caption:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: "16px"
  micro:
    fontFamily: "Inter, Segoe UI, Roboto, Arial, sans-serif"
    fontSize: "10px"
    fontWeight: 600
    lineHeight: "12px"
    letterSpacing: "0.04em"
  mono:
    fontFamily: "Geist Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: "16px"
rounded:
  swatch: "3px"
  sm: "6px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
  pill: "9999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "20px"
  "6": "24px"
  "7": "28px"
  "8": "32px"
  frame: "12px"
  sidebar: "240px"
  rail: "72px"
  topbar: "80px"
  inspector: "320px"
components:
  button-play:
    backgroundColor: "{colors.electric-blue}"
    textColor: "{colors.card-white}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
    height: "40px"
    padding: "0 20px 0 16px"
  button-play-hover:
    backgroundColor: "{colors.electric-blue-hover}"
  button-play-active:
    backgroundColor: "{colors.electric-blue-press}"
  button-ghost:
    textColor: "{colors.decision-ink}"
    rounded: "{rounded.pill}"
    size: "36px"
  button-ghost-hover:
    backgroundColor: "{colors.card-white}"
  button-ghost-active:
    backgroundColor: "{colors.hairline-gray}"
  nav-item:
    textColor: "{colors.card-white}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
    height: "40px"
    padding: "0 12px"
  nav-item-active:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.electric-blue}"
  card:
    backgroundColor: "{colors.card-white}"
    rounded: "{rounded.lg}"
    padding: "28px"
  card-awaiting:
    backgroundColor: "{colors.panel-gray}"
    rounded: "{rounded.lg}"
    padding: "28px"
  thesis-surface:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.decision-ink}"
    rounded: "{rounded.xl}"
    padding: "32px"
  inset-panel:
    backgroundColor: "{colors.panel-gray}"
    rounded: "{rounded.md}"
    padding: "16px"
  role-swatch:
    rounded: "{rounded.swatch}"
    size: "10px"
  role-tag:
    textColor: "{colors.body-gray}"
    typography: "{typography.caption}"
  role-mark:
    rounded: "{rounded.sm}"
    size: "28px"
  guide-card:
    backgroundColor: "{colors.card-white}"
    rounded: "{rounded.lg}"
    padding: "32px"
    width: "720px"
  inspector-card:
    backgroundColor: "{colors.card-white}"
    rounded: "{rounded.lg}"
    padding: "20px"
  artifact-tag:
    backgroundColor: "{colors.panel-gray}"
    textColor: "{colors.body-gray}"
    typography: "{typography.mono}"
    rounded: "{rounded.sm}"
    height: "28px"
    padding: "0 8px"
  artifact-tag-selected:
    backgroundColor: "{colors.blue-wash}"
    textColor: "{colors.electric-blue-press}"
  code-tag:
    rounded: "{rounded.sm}"
    height: "28px"
    padding: "0 10px"
  stage-marker:
    rounded: "{rounded.sm}"
    size: "32px"
    typography: "{typography.body-sm}"
  stage-marker-awaiting:
    backgroundColor: "{colors.canvas-gray}"
    textColor: "{colors.quiet-gray}"
    rounded: "{rounded.sm}"
    size: "32px"
  inline-fact:
    textColor: "{colors.body-gray}"
    typography: "{typography.body-sm}"
  verdict-block:
    backgroundColor: "{colors.uncertainty-yellow}"
    textColor: "{colors.decision-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    height: "32px"
    padding: "0 12px"
  next-test-panel:
    backgroundColor: "{colors.decision-ink}"
    textColor: "{colors.card-white}"
    rounded: "{rounded.md}"
    padding: "20px"
  tooltip:
    backgroundColor: "{colors.decision-ink}"
    textColor: "{colors.card-white}"
    typography: "{typography.caption}"
    rounded: "{rounded.sm}"
    padding: "8px 12px"
---

# Design System: tiemPO

## Overview

**Creative North Star: "El curso que el laboratorio completa en público"**

El sistema es Education2025 (fijado por el usuario en `web/education2025-design-system.md`) adaptado a un laboratorio científico y llevado a un registro más sereno. El shell de plataforma educativa se mantiene: sidebar azul sólido, canvas gris, superficies blancas planas, Inter y píldoras en la navegación. Dentro aloja un ciclo de descubrimiento leído como un temario de nueve módulos numerados. Cada módulo es un artefacto real con ID; lo que todavía no existe se muestra como un hueco honesto, con contorno discontinuo, que nombra al agente y la ruta que lo llenará. La incertidumbre tiene el mismo peso que la evidencia: es el único amarillo de la pantalla.

La saturación está contenida a propósito: el azul sólido vive en el sidebar, la píldora "Start discovery", las marcas de evidencia y los estados seleccionados. La tesis se apoya en una superficie blanca, no en un banner azul. Las etiquetas son discretas: el rol es una muestra de color de 10 px con una palabra, los IDs son etiquetas de código de esquinas suaves y los hechos van en línea sin contenedor. La densidad es de lectura a distancia, porque la pantalla se proyecta para jueces: el cuerpo nunca baja de 12 px y los números van en cifras tabulares. El sistema es solo claro (`color-scheme: light`) y rechaza explícitamente la transcripción de chat y el tablero de KPIs.

El build adapta la fuente en puntos concretos:
- un logo que es solo el wordmark "tiemPO";
- cinco colores de rol de artefacto;
- marcadores de etapa cuadrados (el ModuleNumber del sistema, rellenos con el color del rol);
- un rastreador de 9 celdas junto a la tesis;
- un forest plot como única visualización;
- contornos discontinuos para "awaiting";
- un inspector de procedencia fijo a la derecha;
- el marco redondeado de la app pintado como overlay fijo en vez de un contenedor con `overflow: hidden`.

**Key Characteristics:**
- Azul eléctrico sólido y escaso, sin degradados ni transparencias.
- Superficies blancas planas sobre canvas gris, sin sombras en reposo.
- Cinco roles de artefacto con relleno propio. La hipótesis se distingue por contorno discontinuo, no por color.
- Lo pendiente lleva línea discontinua gris y lo registrado, relleno sólido.
- Geist Mono solo para IDs, hashes y rutas.
- Un solo movimiento autoral: la llegada de una etapa al espinazo.

## Colors

Una paleta de un solo acento: azul eléctrico saturado, usado con moderación sobre grises fríos, con amarillo reservado a la incertidumbre y tinta casi negra para las decisiones.

### Primary
- **Electric Blue** (`electric-blue`): se usa en:
  - el sidebar y la píldora "Start discovery";
  - el relleno del rol EVIDENCE y el contorno del rol HYPOTHESIS;
  - el tramo relleno del espinazo;
  - el punto destacado del forest plot;
  - la sesión seleccionada.

  Sus pasos `electric-blue-hover` y `electric-blue-press` son los únicos estados de hover y press del azul.
- **Experiment Navy** (`experiment-navy`): relleno del rol EXPERIMENT y de las letras de candidato (A/B).

### Secondary
- **Uncertainty Yellow** (`uncertainty-yellow`): se usa en:
  - el rol UNCERTAINTY y el bloque de veredicto;
  - la marca del aviso de ranking inconcluso;
  - el marcador de la etapa de crítica;
  - la etiqueta "Demo data".

  Siempre lleva texto en `decision-ink`, nunca blanco. `uncertainty-yellow-ink` colorea solo iconos de advertencia sobre blanco.

### Tertiary
- **Live Green** (`live-green`): solo el punto pulsante del modo LIVE. `live-green-ink` colorea el icono de un hecho `good` y el check de "copiado". El verde ya no marca etapas registradas: eso lo hace el relleno del marcador.

### Neutral
- **Card White** (`card-white`): tarjetas de etapa, la superficie de la tesis, el inspector, la tarjeta de la guía y el hover de los botones fantasma.
- **Panel Gray** (`panel-gray`): aviso de ranking, candidatos no elegidos, etiquetas de artefacto en reposo y tarjeta "awaiting".
- **Canvas Gray** (`canvas-gray`): fondo de página, topbar y marcador de etapa pendiente.
- **Hairline Gray** (`hairline-gray`): líneas superiores de secciones dentro de una tarjeta, filas del inspector, el borde que separa la tesis del rastreador y el marco de la app.
- **Divider Gray** (`divider-gray`): los puntos medios entre hechos y la línea discontinua del espinazo pendiente.
- **Dash Gray** (`dash-gray`): contornos discontinuos de lo que falta y el cero del forest plot.
- **Quiet Gray** (`quiet-gray`): números de etapas pendientes, iconos de hechos neutros y puntos no destacados del forest plot.
- **Body Gray** (`body-gray`): texto de apoyo, palabra del rol, etiquetas de definición y el nombre de página junto al wordmark.
- **Decision Ink** (`decision-ink`): texto principal, wordmark, rol DECISION, panel "Next test" y tooltip.
- **Tintes de estado:**
  - `blue-wash`: hover y selección de etiquetas;
  - `blue-select-ring`: anillo de 1 px de la etiqueta seleccionada;
  - `blue-halo`: etapa activa;
  - `focus-blue`: anillo de foco de 2 px con offset de 2 px (blanco sobre el sidebar);
  - `blue-tint` y `selection-ink`: selección de texto.

### Named Rules
**The Solid Blue Rule.** El azul es plano: ningún `linear-gradient`, `radial-gradient`, blur ni opacidad sobre `electric-blue`.

**The Scarce Blue Rule.** El azul sólido es para navegación, la acción principal, la evidencia y lo seleccionado. Las superficies de lectura, incluida la tesis, son blancas.

**The Five Roles Rule.** Cada artefacto lleva uno de cinco roles con relleno fijo:
- EVIDENCE: azul eléctrico;
- EXPERIMENT: navy;
- UNCERTAINTY: amarillo con texto en tinta;
- HYPOTHESIS: blanco con contorno azul discontinuo;
- DECISION: tinta.

QUESTION es blanco con anillo gris. Un color de rol no se usa como decoración fuera de su rol.

**The Yellow Means Uncertain Rule.** El amarillo solo marca incertidumbre o datos de demostración que no son hallazgos. Nunca un estado de éxito ni un acento decorativo.

## Typography

**Wordmark Font:** Montserrat Black 900 (`--font-wordmark`, con sans-serif), solo para el nombre "tiemPO"
**Display Font:** Inter (con Segoe UI, Roboto, Arial)
**Body Font:** Inter, con `font-feature-settings: "cv11", "ss01"`
**Label/Mono Font:** Geist Mono (con ui-monospace, SFMono-Regular, Menlo)

**Character:** Inter, una sans neutra y legible a distancia, carga toda la interfaz con una jerarquía por peso de 400 a 800. Montserrat Black, más geométrica y ancha, aparece solo en el wordmark, para que el nombre se distinga del texto que lo rodea. La mono aparece solo donde el valor es literal y copiable.

### Hierarchy
- **Wordmark** (Montserrat 900, 30 px; 26 px en la topbar móvil; −0.04em; interlineado 1): el nombre "tiemPO" con la capitalización exacta del usuario. Es el logo completo del sidebar, el nombre de la topbar y el `<title>`.
- **Display** (800, 30/36 en ≥640 px y 26/32 en móvil, −0.02em): solo la tesis.
- **Headline** (700, 28/36, −0.01em): H1 de las páginas de auditoría.
- **Title-lg** (700, 20/28): encabezado del inspector y título de la guía de lectura.
- **Title-md** (700, 18/26): título de tarjeta de etapa en ≥640 px y frase principal de una etapa.
- **Title-sm** (600, 16/22): título de etapa en móvil, nombre de página junto al wordmark ("Reading guide", "Audit trail", `body-gray`), encabezados de bloque y "Awaiting …".
- **Title-card** (600, 15/20): títulos de candidato, de proyecto y "Discovery loop".
- **Lead** (400, 15/24, máx. ~64ch): párrafo de la tesis y de las páginas de auditoría.
- **Body** (400–600, 14/20): texto general, navegación (500), la píldora de reproducción (600), filas del forest plot.
- **Body-sm** (400, 13/18): hechos en línea, listas literales del artefacto y valores del inspector.
- **Caption** (400–600, 12/16): ejes, notas de método, etiquetas de definición, palabra del rol (600), conteos y la nota "ENUT 2024 · INEGI microdata" del sidebar (`blue-tint`).
- **Micro** (600, 10/12, 0.04em, mayúsculas): solo las marcas de estado "New" y "Demo data".
- **Mono** (12/16): IDs de artefacto, hashes SHA-256, rutas de archivo y códigos de estado (`INCONCLUSIVE_RANKING`).

### Named Rules
**The Wordmark Rule.** El nombre del producto es "tiemPO": Montserrat 900 con −0.04em y la capitalización exacta del usuario. Montserrat no se usa en ningún otro texto. El logo es solo texto: sin símbolo, pastilla ni punto de estado. No se escribe en mayúsculas, no se traduce y no se compone en otro peso.

**The Literal Mono Rule.** Geist Mono solo para valores que existen tal cual en un archivo: IDs, hashes, rutas, claves y códigos. Nunca para prosa ni títulos.

**The Sentence Case Rule.** Títulos, botones y etiquetas de rol van en *sentence case*. Las mayúsculas quedan para las marcas de estado de 10 px ("New", "Demo data") y para los códigos literales del artefacto.

**The True Minus Rule.** Las cifras van en `tabular-nums`, con signo menos tipográfico (−) y con `+` explícito en positivos, para que la dirección nunca dependa solo del color.

## Layout

El shell es el AppShell de Education2025:
- **Sidebar** azul a la izquierda.
- **Topbar** de 80 px sobre el canvas, `sticky`. Lleva el wordmark a la izquierda y los controles a la derecha, con 16–24 px entre grupos.
- **Contenido** sobre canvas gris, con padding horizontal de 32 px (16 px en móvil) y 32 px entre bloques.

Comportamiento responsive:
- **≥1024 px:** sidebar de 240 px y todo dentro de un marco de 12 px.
- **768–1023 px:** el sidebar se reduce a un riel de 72 px solo con iconos.
- **<768 px:** el sidebar es una barra inferior de 64 px y el contenido deja 80 px libres abajo.

Pantalla de descubrimiento:
- **Columnas:** el espinazo (`minmax(0,1fr)`) y el inspector (320 px; 380 px en ≥1536 px), separados 24 px. El inspector, una sola tarjeta de procedencia, es `sticky` bajo la topbar y hace scroll propio. Por debajo de 1024 px cae debajo del espinazo.
- **Espinazo:** una lista de nueve etapas en una rejilla `32px | 1fr` (gap 12 px, 20 px en ≥640 px), con 20 px entre etapas. Cada marcador se alinea con el título de su tarjeta (offset de 26 px en ≥640 px).
- **Tesis:** ocupa todo el ancho, con padding de 32 px. En ≥1280 px se parte en texto y una columna de 300 px con el rastreador de 9 celdas (`grid-cols-9`, gap 4 px). Las separa un borde izquierdo de 1 px en `hairline-gray` con 40 px a cada lado; apiladas, ese borde pasa arriba.

El ritmo de espaciado es base 4. Dentro de los componentes dominan 8 y 12 px; entre bloques se usan de 20 a 32 px. Las tarjetas de etapa tienen 28 px de padding (20 px en móvil) y 20 px bajo su encabezado.

### Named Rules
**The Spine Rule.** El ciclo se lee de arriba abajo, una etapa por fila, numeradas del 1 al 9. No se reordena en carriles, pestañas ni carrusel.

**The Hairline Section Rule.** Dentro de una tarjeta, los grupos se separan con una línea superior de 1 px en `hairline-gray` y 16 px de aire, no con cajas grises anidadas. `panel-gray` queda para los avisos (ranking inconcluso) y las alternativas no elegidas.

## Elevation & Depth

El sistema es plano por defecto. La profundidad viene del contraste tonal (superficie blanca sobre canvas gris) y de líneas finas, no de sombras. Las sombras de la fuente (`shadow-sm`, `shadow-md`) no se usan, porque no hay menús desplegables. Lo que existe como `box-shadow` son anillos de estado sin desenfoque, más el marco de la app.

### Shadow Vocabulary
- **Active halo** (`box-shadow: 0 0 0 4px var(--color-blue-200)`; 3 px en el rastreador): marcador y celda de la etapa activa en replay. La tarjeta activa usa un `ring-2` del mismo `blue-halo`.
- **Fresh pulse** (`0 0 0 6px rgb(0 85 255 / 0.18)` animado, 3 ciclos de 1.6 s): solo en LIVE, sobre un artefacto que acaba de llegar.
- **App frame** (`box-shadow: 0 0 0 calc(var(--frame) + 2px) var(--color-gray-200)`): overlay fijo que pinta el borde redondeado de 24 px alrededor de la página en ≥1024 px. Lleva `pointer-events: none` para que la página haga scroll normal.

### Named Rules
**The Flat-At-Rest Rule.** Nada proyecta sombra en reposo. Un anillo aparece solo como respuesta a estado: activo, seleccionado, recién llegado o foco.

## Shapes

Los radios son jerárquicos, del contenedor más grande al más pequeño:

| Radio | Dónde |
|---|---|
| 24 px | Marco de la app |
| 20 px | Superficie de la tesis |
| 16 px | Tarjetas de etapa, inspector y tarjeta de la guía |
| 12 px | Avisos, candidatos y panel "Next test" |
| 6 px | Marcadores y marcas de rol, etiquetas de artefacto y de código, bloque de veredicto, celdas del rastreador y tooltip |
| 3 px | Muestra de rol de 10 px |

La píldora completa se reserva para la navegación del sidebar, la píldora de reproducción, los botones fantasma circulares y los puntos de estado. Los iconos son Lucide de trazo (grosor 1.75–2.5, 15–20 px).

Tres geometrías llevan significado:
- **Cuadrado:** es rol y número. Va en el marcador de etapa, la marca de rol (inspector y guía), la muestra de rol y las letras de candidato.
- **Rectángulo de 6 px:** es un valor literal. Va en el ID de artefacto, el código de hipótesis, la marca "Selected by the Director" y el veredicto.
- **Círculo:** es estado o acción. Va en el punto vivo, el punto del forest plot, la píldora de reproducción y los botones fantasma.

La **línea discontinua** (1–1.5 px, `dash-gray`/`divider-gray`) siempre significa "todavía no existe". En azul significa "hipótesis no probada".

### Named Rules
**The Dashed Means Absent Rule.** Un contorno discontinuo gris es un hueco honesto: etapa, celda o tarjeta sin artefacto. No se usa como decoración ni como borde de agrupación.

## Components

### Buttons
- **Start discovery / Pause / Resume:** la única acción sólida de la topbar. Píldora de 40 px en `electric-blue` (padding 16 px a la izquierda, 20 px a la derecha) con icono play o pausa de 15 px y la etiqueta en body 600 blanco, sin cortes de línea. Dice "Start discovery" en reposo, "Pause" mientras reproduce y "Resume" si se pausó a mitad del recorrido. Hover `electric-blue-hover` y press `electric-blue-press`.
- **Ghost:** círculos de 36 px sin fondo ni anillo, icono en tinta. Hover blanco y press `hairline-gray`. Rodean a la píldora como anterior y siguiente; en móvil solo queda "siguiente". No hay botón de reinicio: la tecla Home reinicia.
- **Copy:** círculo fantasma de 28 px en el inspector, con hover `blue-wash`.
- **Text button:** "Show all N" en caption semibold `electric-blue-hover`.
- Transiciones de 120 ms.

### Topbar
De izquierda a derecha:
1. El wordmark, que es un enlace a "/" y reinicia el replay desde el principio.
2. Los botones fantasma ← y → alrededor de la píldora de reproducción.
3. El contador "Stage N of 9" (o "Overview · N of 9 recorded") en body-sm 600 tabular, con el reloj del replay en caption debajo.

No hay selector de modo: replay es el modo por defecto. LIVE solo se abre por URL (`/?mode=live`), para el equipo que corre Omnigent en local. Ahí el transporte se sustituye por un estado en texto plano con un punto verde pulsante, sin contenedor.

### Tags
- **Role tag:** muestra cuadrada de 10 px (radio 3 px) con el relleno del rol, más la palabra en caption 600 `body-gray`. Va después del título de la etapa. Si el título ya nombra el rol, solo se ve la muestra y la palabra queda para lectores de pantalla. En ese caso QUESTION no muestra muestra, porque un cuadrado blanco solo se lee como una casilla vacía.
- **Artifact tag:** el ID en mono 12 px, 28 px de alto, radio 6 px, fondo `panel-gray`, sin anillo ni icono. En hover pasa a `blue-wash` con texto `electric-blue-press`; seleccionado añade además un anillo de 1 px `blue-select-ring`. Al hacer clic abre el artefacto en el inspector.
- **Code tag:** rectángulo de 6 px para el código de hipótesis (contorno azul discontinuo, texto azul) y para "Selected by the Director" (fondo tinta, texto blanco).
- **Inline fact:** sin contenedor: icono de 15 px más texto body-sm. El tono colorea solo el icono (`good` verde, `warn` amarillo, `brand` azul). Una fila de hechos se separa con puntos medios en `divider-gray`.

### Cards / Containers
- **Corner Style:** 16 px.
- **Background:** blanco si la etapa está registrada; `panel-gray` con contorno discontinuo de 1.5 px si espera artefactos.
- **Shadow Strategy:** ninguna (ver Elevation & Depth).
- **Border:** ninguno en reposo; anillo `blue-halo` de 2 px si está activa.
- **Internal Padding:** 28 px en ≥640 px y 20 px en móvil. Dentro, las secciones siguen The Hairline Section Rule.
- **Sin check por tarjeta:** el estado registrado o pendiente lo lleva el relleno del marcador.

### Navigation
- **Sidebar:** `electric-blue` sólido.
  - **Arriba:** el wordmark de 30 px en blanco directamente sobre el azul, alineado con los ítems (12 px de padding lateral) y 32 px por encima de ellos. No lleva pastilla blanca, símbolo ni punto de estado. Se oculta en el riel de 72 px y en la barra inferior, donde el wordmark de la topbar lleva el nombre.
  - **Ítems:** Discovery, Reading guide y Audit trail, en ese orden, con iconos Lucide de 20 px (Waypoints, BookOpen, Database). Son píldoras de 40 px en body 500. Activo: fondo blanco con texto azul. Inactivo: texto blanco con hover `electric-blue-press`.
  - **Pie:** la nota caption "ENUT 2024 · INEGI microdata" en `blue-tint` y, debajo, "Repository".
  - **Foco:** todo enlace del sidebar usa un anillo de foco blanco en lugar de `focus-blue`, para que sea visible sobre el azul.
- **Móvil:** barra inferior de 64 px con los mismos ítems, cada uno con el icono de 20 px encima de la etiqueta en caption 500, sin cortes de línea (48 px de alto, radio 12; el activo en blanco con texto azul). Desde 768 px vuelven a ser píldoras en fila.

### Thesis surface y rastreador
Superficie blanca de 20 px de radio:
- **Texto:** la tesis en Display tinta y el párrafo Lead en `body-gray`.
- **Rastreador:** solo "Discovery loop", el conteo "N of 9 stages" y nueve celdas de 28 px de alto con radio 6 px. Una celda registrada lleva el relleno de su rol; una pendiente, `panel-gray` con contorno discontinuo. La celda activa lleva el halo de 3 px.
- **Sin pie:** el rastreador no lleva nota de fuente. El aviso de LIVE o de respaldo vive solo en la topbar.

### Stage marker
Cuadrado de 32 px con radio 6 px y el número de etapa en body-sm bold tabular.
- **Registrado:** relleno del rol.
- **Pendiente:** `canvas-gray` con contorno discontinuo y número en `quiet-gray`.

### Spine
Línea vertical de 2 px entre marcadores:
- **Azul sólido** cuando la etapa y la siguiente están registradas y visibles.
- **Discontinua `divider-gray`** en cualquier otro caso.

En replay, las etapas aún no reveladas se ven solo como título gris con "upcoming".

### Forest plot
Tabla de punto y bigote con cuatro columnas:
- el resultado;
- el intervalo sobre un eje compartido, con rejilla `hairline-gray` y el cero en `dash-gray`;
- la estimación con signo;
- el IC al 95 % en texto.

La asociación negativa más fuerte va en `electric-blue` y bold; el resto en `quiet-gray`. Cada fila es enfocable y muestra un tooltip en tinta con la cifra a 3 decimales, el IC, el SE y el n. El gráfico siempre va acompañado de la nota del método de varianza.

### Critique
- **Veredicto:** bloque amarillo de 32 px y radio 6 px con icono de advertencia y el código en bold.
- **Grupos de hallazgos:** secciones con línea superior y conteo en texto plano: limitaciones, incertidumbres, afirmaciones no sustentadas y preguntas abiertas.
- **Aviso de ranking inconcluso:** queda en `panel-gray`, con una marca amarilla cuadrada de 24 px.

### Inspector
Una sola tarjeta blanca de procedencia (16 px de radio, 20 px de padding) que ocupa toda la columna derecha:
- encabezado con la marca de rol cuadrada de 28 px y el título;
- el ID en mono semibold;
- una lista de definición: etiquetas caption semibold en una columna de 6.5 rem, filas separadas por `hairline-gray`. Muestra el archivo, el SHA-256 truncado a 16 caracteres, el productor, la fecha UTC y los hechos del artefacto. Los valores copiables llevan botón de copiar;
- los artefactos enlazados, como etiquetas de artefacto bajo una línea fina.

La leyenda de roles no vive aquí: está en la página Reading guide.

### Role mark (TypeMark)
Cuadrado de 28 px con radio 6 px, relleno del rol e icono Lucide de 15 px. Es la versión grande de la muestra de rol y la comparten el encabezado del inspector y la guía de lectura.

### Reading guide (`/guide`)
Página con PageHeader "Reading guide" y una sola tarjeta blanca de lectura:
- **Tarjeta:** máx. 720 px de ancho, 16 px de radio, padding de 24 px (32 px en ≥768 px).
- **Título:** "Reading the spine" en Title-lg.
- **Lista:** los cinco roles más QUESTION. Cada fila lleva la marca de rol de 28 px y, al lado, el nombre en bold tinta seguido de su significado en body 14/20 `body-gray`, con 16 px entre filas.
- **Cierre:** bajo una línea fina, la frase de que ENUT 2024 es observacional y toda cifra es una asociación, nunca una causa.

### Awaiting
Bloque de espera de una etapa sin artefacto:
- icono de reloj de arena en un círculo blanco;
- "Awaiting {what}" en title-sm;
- el agente productor y la ruta en mono.

En LIVE añade "Listening for new files" con un punto azul pulsante.

### Next test
La siguiente prueba de una decisión va en un panel `decision-ink` de 12 px de radio con texto blanco.

### Motion
- **Movimiento autoral:** uno solo, `stage-in`, al revelar una etapa. Dura 420 ms con `cubic-bezier(0.16, 1, 0.3, 1)`, opacidad de 0 a 1 y 14 px hacia arriba.
- **Estados:** 120 ms con `cubic-bezier(0.2, 0, 0, 1)`.
- **Reduced motion:** con `prefers-reduced-motion` se apagan las animaciones y las transiciones van a 0 ms.

## Do's and Don'ts

### Do:
- **Do** rellenar cada artefacto con su color de rol (The Five Roles Rule) y repetir esa gramática en muestra, marcador, celda del rastreador y marca de rol.
- **Do** poner el título primero y la etiqueta de rol después, y dejar solo la muestra cuando el título ya nombra el rol (ninguna para QUESTION).
- **Do** dibujar lo que falta como contorno discontinuo gris que nombra al agente productor y la ruta del archivo.
- **Do** mostrar cada ID, hash y ruta en Geist Mono, como etiqueta de 6 px clicable o con botón de copiar.
- **Do** escribir cifras con `tabular-nums`, menos tipográfico (−) y `+` explícito.
- **Do** separar grupos dentro de una tarjeta con líneas finas, no con cajas anidadas.
- **Do** respetar `prefers-reduced-motion` en cualquier movimiento nuevo.

### Don't:
- **Don't** usar degradados, blur ni transparencias sobre el azul (The Solid Blue Rule).
- **Don't** pintar de azul sólido una superficie de lectura. El azul es para navegación, la acción principal, la evidencia y lo seleccionado.
- **Don't** usar amarillo para algo que no sea incertidumbre o datos de demostración.
- **Don't** escribir el nombre del producto de otra forma que "tiemPO".
- **Don't** usar sombras en reposo ni sombras desenfocadas para separar tarjetas.
- **Don't** presentar el ciclo como chat (burbujas, avatares) ni como tablero de KPIs.
- **Don't** usar contornos discontinuos como decoración: significan ausencia o hipótesis no probada.
- **Don't** añadir un modo oscuro: el sistema es solo claro.
- **Don't** usar Geist Mono para prosa o títulos.
- **Don't** usar Montserrat fuera del wordmark: el resto de la interfaz es Inter.
