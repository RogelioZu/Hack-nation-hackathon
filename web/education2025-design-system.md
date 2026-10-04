# EDUCATION2025 — Sistema de diseño

Especificación extraída de las tres pantallas de la plataforma educativa (Catálogo, Dashboard y Detalle de curso). Todo el documento está organizado de lo general a lo particular:

```
1. Principios
2. Tokens (color · tipografía · espaciado · radios · sombras · iconos · motion)
3. Layout (app shell y grids)
4. Componentes
   4.1 Átomos
   4.2 Moléculas
   4.3 Organismos
5. Plantillas y páginas (árbol de componentes)
6. Contenido / copy
7. Tokens exportables (CSS + JSON)
```

> **Regla principal de color:** el azul es **sólido, eléctrico y sin degradados**. Ningún componente usa `linear-gradient`, `radial-gradient`, blur ni transparencias sobre el azul. Donde el diseño original tenía un degradado (sidebar y banner), se sustituye por `--blue-500` plano.

---

## 1. Principios

| Principio | Aplicación |
|---|---|
| Azul plano como identidad | El azul eléctrico `#0055FF` es el único color de marca. Se usa en sidebar, banner, botones, progreso y estados activos. |
| Superficies limpias | Fondo gris claro + tarjetas blancas sin sombra fuerte. La jerarquía se marca con tamaño y peso tipográfico, no con decoración. |
| Redondeo jerárquico | El radio crece con el tamaño del contenedor: badge → pill, miniatura → 12, tarjeta → 16, contenedor principal → 24. |
| Estado visible | Lo completado siempre lleva check verde; lo pendiente, gris; lo activo, azul. |

---

## 2. Tokens

### 2.1 Color

#### Marca — Azul eléctrico (sólido)

| Token | Hex | Uso |
|---|---|---|
| `--blue-50` | `#EBF1FF` | Fondos de hover suaves, fondo de chips en hover |
| `--blue-100` | `#D6E3FF` | Texto secundario sobre azul (versión, metadatos en sidebar) |
| `--blue-200` | `#ADC7FF` | Bordes de hover en tarjetas |
| `--blue-300` | `#7AA5FF` | Ilustraciones, detalles |
| `--blue-400` | `#3D7BFF` | Focus ring |
| **`--blue-500`** | **`#0055FF`** | **Primario: sidebar, banner, botones, barras de progreso, chip activo** |
| `--blue-600` | `#0047D6` | Hover de primario, texto de enlace |
| `--blue-700` | `#0039AD` | Pressed de primario, nav item hover en sidebar |
| `--blue-800` | `#002B85` | Badge "Сертификат" |
| `--blue-900` | `#001D5C` | Texto sobre fondos azul claro |

Contraste del texto blanco sobre `--blue-500`: **5.6 : 1** (cumple WCAG AA para cualquier tamaño).

#### Neutros

| Token | Hex | Uso |
|---|---|---|
| `--gray-0` | `#FFFFFF` | Superficie de tarjetas, texto sobre azul |
| `--gray-50` | `#F5F7FA` | Superficie secundaria (filas del acordeón, fondo de tiles) |
| `--gray-100` | `#E9ECF1` | **Canvas / fondo del área de contenido** |
| `--gray-200` | `#DDE2EA` | Track de barras de progreso, bordes |
| `--gray-300` | `#C4CBD6` | Borde de radio/checkbox, check pendiente |
| `--gray-400` | `#9AA3B2` | Texto terciario, placeholders |
| `--gray-500` | `#6B7385` | Texto secundario (duraciones, metadatos) |
| `--gray-700` | `#363D4A` | Texto de cuerpo alternativo |
| `--gray-900` | `#121722` | Texto principal y títulos |

#### Semánticos

| Token | Hex | Uso |
|---|---|---|
| `--green-500` | `#22C55E` | Check de completado, badge "Профессия", punto de estado del logo |
| `--green-600` | `#16A34A` | Texto sobre verde claro |
| `--yellow-400` | `#FFC83D` | Badge "Популярно" |
| `--yellow-600` | `#D99A00` | Texto del aviso de racha ("Осталось 1 день…") |
| `--red-500` | `#EF4444` | Errores, badge de notificación (no visible, reservado) |

#### Alias semánticos (lo que deben consumir los componentes)

| Alias | Valor |
|---|---|
| `--color-bg-canvas` | `--gray-100` |
| `--color-bg-surface` | `--gray-0` |
| `--color-bg-surface-muted` | `--gray-50` |
| `--color-bg-brand` | `--blue-500` |
| `--color-text-primary` | `--gray-900` |
| `--color-text-secondary` | `--gray-500` |
| `--color-text-tertiary` | `--gray-400` |
| `--color-text-on-brand` | `--gray-0` |
| `--color-text-on-brand-muted` | `--blue-100` |
| `--color-text-link` | `--blue-600` |
| `--color-border` | `--gray-200` |
| `--color-success` | `--green-500` |
| `--color-warning` | `--yellow-600` |
| `--color-focus` | `--blue-400` |

### 2.2 Tipografía

Familia: **Inter** (soporta cirílico y latino). Fallback: `"Inter", "Segoe UI", Roboto, Arial, sans-serif`.

| Token | Tamaño / interlineado | Peso | Uso en el diseño |
|---|---|---|---|
| `display` | 64 / 60 | 800 | "15%" del banner |
| `display-sm` | 36 / 36 | 700 | "скидка" del banner |
| `h1` | 28 / 36 | 700 | "Добрый день, Нина В!" |
| `h2` | 20 / 28 | 700 | Título del header "EDUCATION2025" |
| `h3` | 18 / 24 | 700 | Título de curso en tarjeta de progreso |
| `h4` | 16 / 22 | 600 | Títulos de sección ("Ваши профессии", "Видео") |
| `title-card` | 15 / 20 | 600 | Título de CourseCard |
| `body` | 14 / 20 | 400 | Texto general, nav items (500) |
| `body-strong` | 14 / 20 | 600 | Títulos de filas del acordeón, "Сертификат" |
| `body-sm` | 13 / 18 | 400 | Subtítulos, texto del banner |
| `caption` | 12 / 16 | 400 | Duraciones, fechas, "18 из 32" |
| `micro` | 10 / 12 | 600 | Badges, etiquetas de logros, "Продолжить просмотр" |

Reglas: títulos en *sentence case*; el único texto en mayúsculas es la marca "EDUCATION2025" y el código promocional.

### 2.3 Espaciado (base 4)

| Token | px |
|---|---|
| `--space-1` | 4 |
| `--space-2` | 8 |
| `--space-3` | 12 |
| `--space-4` | 16 |
| `--space-5` | 20 |
| `--space-6` | 24 |
| `--space-8` | 32 |
| `--space-10` | 40 |
| `--space-12` | 48 |

### 2.4 Radios (jerárquicos)

| Token | px | Aplica a |
|---|---|---|
| `--radius-sm` | 6 | Checkbox, número de módulo |
| `--radius-md` | 12 | Miniaturas de video, filas del acordeón, tiles de racha/logros, imágenes de curso |
| `--radius-lg` | 16 | Tarjetas (CourseCard, cards del dashboard) |
| `--radius-xl` | 20 | Banner promocional |
| `--radius-2xl` | 24 | Contenedor de la app (marco exterior) |
| `--radius-pill` | 999 | Botones, chips, badges, inputs, nav items, barras de progreso |

### 2.5 Elevación

El diseño es plano. Solo dos niveles:

| Token | Valor | Uso |
|---|---|---|
| `--shadow-none` | `none` | Todas las tarjetas en reposo |
| `--shadow-sm` | `0 1px 2px rgba(18, 23, 34, 0.06)` | Dropdown de usuario, tarjeta en hover |
| `--shadow-md` | `0 8px 24px rgba(18, 23, 34, 0.10)` | Menús desplegables abiertos |

### 2.6 Iconografía

Estilo lineal, trazo 1.75 px, esquinas redondeadas (equivalente a Lucide).

| Icono | Uso | Tamaño |
|---|---|---|
| `home` | Главная | 20 |
| `layers` / `library` | Все курсы | 20 |
| `briefcase` | Центр карьеры | 20 |
| `settings` | Настройки | 20 |
| `wallet` | Платежи | 20 |
| `log-out` | Выйти | 20 |
| `bell` | Notificaciones | 18 |
| `message-circle` | Mensajes | 18 |
| `chevron-down` / `chevron-up` | Dropdown, acordeón | 16 |
| `search` | Buscador | 16 |
| `undo-2` | "Назад" | 16 |
| `play` (relleno) | Continuar video | 12 |
| `check` | Estado completado | 12 |
| `star` | Aviso de racha | 12 |
| `corner-down-right` | CTA del banner | 18 |

### 2.7 Motion

| Token | Valor | Uso |
|---|---|---|
| `--duration-fast` | 120 ms | Hover de botones y chips |
| `--duration-base` | 200 ms | Apertura del acordeón, rotación de chevron |
| `--ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | Todas las transiciones |

Respetar `prefers-reduced-motion: reduce` (transiciones a 0 ms).

---

## 3. Layout

### 3.1 App shell

```
┌──────────────────────────────────────────────────────────────┐
│┌────────┐┌──────────────────────────────────────────────────┐│
││        ││ Topbar (80px)                                    ││
││Sidebar ││──────────────────────────────────────────────────││
││ azul   ││                                                  ││
││ sólido ││ Content (padding 24–32px, bg --gray-100)         ││
││        ││                                                  ││
│└────────┘└──────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

| Elemento | Valor |
|---|---|
| Ancho de referencia | 1440 px |
| Contenedor de la app | `--radius-2xl`, `overflow: hidden` |
| Sidebar colapsado | 72 px (solo iconos) — pantalla Catálogo |
| Sidebar expandido | 240 px (icono + texto) — Dashboard y Detalle |
| Topbar | 80 px de alto, padding horizontal 32 px, fondo `--gray-100` |
| Content | padding 0 32 px 32 px, gap entre bloques 24 px |

### 3.2 Grids por página

| Página | Estructura |
|---|---|
| Catálogo | Banner a ancho completo → debajo: FilterPanel 240 px + gap 24 + CourseGrid (2 columnas, gap 16) |
| Dashboard | 2 columnas `2fr 1fr`, gap 24. Izquierda: saludo + racha, profesiones, cursos. Derecha: continuar viendo, logros |
| Detalle de curso | BackLink arriba → 2 columnas `280px 1fr`, gap 24. Izquierda: tarjetas de resumen apiladas. Derecha: lista de videos |

### 3.3 Breakpoints

| Nombre | Mín. | Cambios |
|---|---|---|
| `mobile` | 0 | Sidebar se convierte en barra inferior; todo a 1 columna; FilterPanel en bottom sheet |
| `tablet` | 768 | Sidebar colapsado (72 px); CourseGrid 1 columna |
| `desktop` | 1200 | Layout completo descrito arriba |

---

## 4. Componentes

Cada componente indica: **anatomía**, **especificaciones**, **variantes / estados** y **props**.

### 4.1 Átomos

#### Button

| Variante | Fondo | Texto | Borde | Alto | Padding |
|---|---|---|---|---|---|
| `primary` | `--blue-500` | blanco | — | 40 | 0 20 |
| `secondary` | blanco | `--blue-600` | 1 px `--blue-500` | 40 | 0 20 |
| `ghost` | transparente | `--gray-500` | — | 32 | 0 8 |
| `disabled` | `--gray-50` | `--gray-400` | — | 32 | 0 16 |

- Radio: `--radius-pill`. Tipografía: `body` 500.
- Estados primary: hover `--blue-600`, pressed `--blue-700`, focus ring 2 px `--blue-400` con offset 2 px.
- Ejemplo de `disabled` en el diseño: botón "Скачать" (descargar certificado).
- Props: `variant`, `size: sm | md`, `iconLeft?`, `iconRight?`, `disabled`, `onClick`.

#### IconButton

| Variante | Tamaño | Fondo | Icono |
|---|---|---|---|
| `brand` | 36 × 36 | `--blue-500` | blanco 18 |
| `brand-lg` | 40 × 40 | `--blue-500` | blanco 18 (CTA del banner) |
| `play` | 28 × 28 | `--blue-500` | blanco 12 |
| `on-brand` | 40 × 40 | blanco | `--blue-500` 18 |

- Siempre circular. Hover `--blue-600`. Requiere `aria-label`.
- Usos: campana, mensajes (topbar), play (continuar video), flecha del banner.

#### Badge

| Variante | Texto ejemplo | Fondo | Texto |
|---|---|---|---|
| `profession` | Профессия | `--green-500` | blanco |
| `certificate` | Сертификат | `--blue-800` | blanco |
| `course` | Курс | `--blue-500` | blanco |
| `popular` | Популярно | `--yellow-400` | `--gray-900` |

- Alto 18, padding 0 8, `--radius-pill`, tipografía `micro`.
- Se agrupan en fila con gap 4. Máximo 2 por tarjeta.

#### Chip (filtro seleccionable)

- Alto 28, padding 0 12, `--radius-pill`, `caption` 500.
- Reposo: fondo blanco, borde 1 px `--blue-500`, texto `--blue-600`.
- Hover: fondo `--blue-50`.
- Seleccionado: fondo `--blue-500`, texto blanco, sin borde visible.
- Grupo con selección única (`role="radiogroup"`). Ejemplo: Любое / Курс / Профессия.

#### Input (búsqueda)

- Alto 36, `--radius-pill`, fondo blanco, sin borde en reposo, padding 0 16.
- Placeholder `body-sm` `--gray-400` ("Найти").
- Icono `search` 16 a la derecha, color `--gray-900`.
- Focus: borde 1.5 px `--blue-500` + ring `--blue-400`.

#### Radio

- 14 × 14 circular. Reposo: borde 1.5 px `--gray-300`, fondo blanco.
- Seleccionado: relleno `--blue-500` con punto blanco central de 6 px.
- Etiqueta `caption` `--gray-900`, gap 8. Separación vertical entre opciones 8.

#### Checkbox

- 14 × 14, `--radius-sm` (4–6), borde 1.5 px `--gray-300`.
- Marcado: fondo `--blue-500`, check blanco.
- Etiqueta igual que Radio.

#### Avatar

- 24 × 24 circular con imagen. Fallback: iniciales sobre `--blue-50`, texto `--blue-600`.

#### StatusCheck

| Estado | Fondo | Icono |
|---|---|---|
| `done` | `--green-500` | check blanco |
| `pending` | `--gray-300` | check blanco |
| `none` | — | no se muestra |

- Tamaños: 16 (sobre miniaturas y acordeón), 20 (tiles de racha).

#### ProgressBar

- Alto 6 (en tarjetas de lista) o 10 (tarjeta de progreso de curso).
- Track `--gray-200`, relleno `--blue-500` plano, ambos `--radius-pill`.
- Props: `value`, `max`. Accesible con `role="progressbar"` y `aria-valuenow / aria-valuemax`.

#### LegendDot

- Punto 10 × 10 circular + texto `caption`.
- Variantes: `brand` (`--blue-500`, "18 просмотрено"), `muted` (`--gray-200`, "32 осталось").

#### Logo

- Marca: tres barras verticales + barra corta, color `--blue-500` sobre pill blanca.
- Variante `full`: icono + "EDU" + punto verde 6 px (`--green-500`) en la esquina superior derecha.
- Variante `mark`: solo icono, blanco sobre el sidebar azul (sidebar colapsado).

#### Divider

- 1 px `--gray-200`. Se usa en la tarjeta de progreso antes de "0/1 практическая работа".

---

### 4.2 Moléculas

#### NavItem

```
[icono 20] [label]
```

- Alto 40, padding 0 12, gap 12, `--radius-pill`, `body` 500.
- Reposo: texto e icono blancos sobre azul.
- Hover: fondo `--blue-700`.
- **Activo: fondo blanco, icono y texto `--blue-500`** (sustituye al pill translúcido del original para cumplir "sin difuminado").
- Variante `collapsed`: solo icono centrado en círculo de 40 × 40; activo = círculo blanco.
- Items: Главная, Все курсы, Центр карьеры, Настройки, Платежи. Al pie: Выйти.

#### UserMenu (trigger)

```
[Avatar 24] [Нина В] [chevron-down]
```

- Alto 36, padding 0 12 0 6, fondo blanco, `--radius-pill`, gap 8, `body-sm` 500.
- Abre un dropdown con `--shadow-md`, radio 12.

#### SearchField

- Input de búsqueda (átomo) a ancho completo del FilterPanel.

#### FilterGroup

```
Título (h4 → 14/600)
└─ Chips | Radios | Checkboxes
```

- Gap título → opciones: 12. Gap entre grupos: 24.
- Grupos del diseño:
  - **Вид** (Tipo) → Chips: Любое, Курс, Профессия
  - **Сложность** (Dificultad) → Radios: Неважно, Новичок, Любитель, Профессионал
  - **Тематика** (Temática) → Checkboxes: Английский язык, Программирование, Дизайн, Финансы

#### PromoCode

- Pill blanco, alto 32, padding 0 24, texto `--blue-600` 13/700 en mayúsculas ("ENG-PROMO-2025").
- Clic copia al portapapeles; feedback: texto cambia a "Скопировано" 2 s.

#### DayTile (racha)

```
  ( ✓ )
  8 авг
   ПН
```

- 56 × 72, fondo blanco, `--radius-md`, contenido centrado, gap 4.
- StatusCheck 20 arriba, fecha `caption` `--gray-500`, día `body-strong`.
- Estados: `done` (check verde), `today` (check gris + borde 1.5 px `--blue-500`), `future` (check gris).

#### StreakHint

- Icono `star` 12 + texto `caption` 500 `--yellow-600`.
- Ejemplo: "Осталось 1 день до достижения СТРИК".

#### VideoThumbnail

```
┌──────────────┐
│ ✓            │  ← StatusCheck 16, top-left 8px
│   imagen     │
└──────────────┘
4.2 Отличия от десктопа
```

- Imagen ratio 16:10, `--radius-md`, `object-fit: cover`.
- Caption debajo: `caption` `--gray-900`, margen superior 6.
- Hover: borde 2 px `--blue-500`.

#### AchievementTile

- 56 × 80, fondo blanco, `--radius-md`, ilustración 32 arriba, etiqueta `micro` centrada (máx. 2 líneas).
- Bloqueado: ilustración en escala de grises y etiqueta `--gray-400`.
- Ejemplos: Первый день, Идеальное ДЗ, Урок в подарок.

#### ProgressMeta

- Fila con ProgressBar y contador alineado a la derecha ("18 из 32", `caption` `--gray-500`).

#### ProgressLegend

- Dos LegendDot en fila, gap 24.

#### SectionHeader

- Título `h4` + acción opcional a la derecha (enlace `body-sm` `--blue-600`). Margen inferior 12.

#### BackLink

- Círculo 28 blanco con icono `undo-2` + texto "Назад" `caption` `--gray-500`. Gap 8.

#### ModuleNumber

- Cuadrado 28 × 28, fondo blanco, `--radius-sm`, número `caption` 600 centrado.

---

### 4.3 Organismos

#### Sidebar

| Propiedad | Valor |
|---|---|
| Fondo | `--blue-500` **sólido** |
| Ancho | 240 (expandido) / 72 (colapsado) |
| Padding | 24 16 |
| Estructura | Logo + versión → NavItems (gap 8) → espacio flexible → Выйти |

- Bloque del logo (expandido): pill blanca pegada al borde izquierdo (radio solo a la derecha), alto 56, con Logo `full`. A su derecha, versión "v 2.0.14 / 2025" en `micro` `--blue-100`.
- Nav: `<nav aria-label="Principal">`.

#### Topbar

```
EDUCATION2025                       [🔔] [💬] [UserMenu ▾]
```

- Alto 80, `display:flex`, `justify-content: space-between`, `align-items: center`.
- Título `h2`, `--gray-900`.
- Acciones: IconButton `brand` ×2 + UserMenu, gap 12.

#### PromoBanner

```
┌────────────────────────────────────────────────────────────────────┐
│ [ilustración]  15%   На все курсы             ┌──────────────────┐ │
│                скидка английского языка…      │ Подробнее… [→]   │ │
│                       [ENG-PROMO-2025]        └──────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

| Propiedad | Valor |
|---|---|
| Fondo | `--blue-500` sólido (sin degradado) |
| Alto | 140 |
| Radio | `--radius-xl` |
| Padding | 24 32 |
| Ilustración izquierda | Line-art blanco, 160 px, puede sobresalir por arriba |
| Hero | "15%" `display` + "скидка" `display-sm`, blancos |
| Descripción | `body-sm` blanco, máx. 220 px |
| PromoCode | debajo de la descripción |
| Bloque derecho | Panel blanco `--radius-lg`, padding 16, texto `body-sm` `--blue-600` + IconButton `brand-lg` |
| Ilustración decorativa | Gato line-art blanco en esquina superior derecha |

#### FilterPanel

- Ancho 240, sin fondo propio (sobre canvas).
- Contenido: SearchField → FilterGroup Вид → FilterGroup Сложность → FilterGroup Тематика.
- Gap 24 entre bloques.

#### CourseCard

```
┌───────────────────────────────────────────────┐
│ ┌────────┐  [Профессия] [Сертификат]          │
│ │ imagen │  1С-программист                    │
│ │ 88×88  │                                    │
│ └────────┘  6 месяцев                         │
└───────────────────────────────────────────────┘
```

| Propiedad | Valor |
|---|---|
| Fondo | blanco |
| Radio | `--radius-lg` |
| Padding | 16 |
| Alto mínimo | 120 |
| Imagen | 88 × 88, `--radius-md`, ilustración/3D sobre fondo claro |
| Contenido | Badges (gap 4) → título `title-card` (máx. 3 líneas) → duración `caption` `--gray-500` anclada abajo |
| Hover | borde 1 px `--blue-200` + `--shadow-sm` |
| Interacción | Toda la tarjeta es un enlace |

Props: `image`, `badges[]`, `title`, `duration`, `href`.

#### CourseGrid

- `grid-template-columns: repeat(2, 1fr)`, gap 16.

#### WelcomeBlock

- `h1` saludo → `body-sm` subtítulo `--gray-700` → StreakHint → fila de DayTile (gap 8).
- Gap vertical 8 entre textos, 16 antes de la fila de días.

#### ContinueWatchingCard (dashboard)

- Fondo blanco, `--radius-lg`, padding 16.
- `micro` "Продолжить просмотр" `--gray-500` → `body-strong` "4. Специфика мобильных платформ" → fila de 2 VideoThumbnail (gap 12).

#### LearningProgressCard (profesiones y cursos)

```
┌──────────────────────────────────────────────┐
│ ┌──────┐  Дизайн мобильных приложений        │
│ │ img  │  от нуля до продвинутого уровня     │
│ └──────┘  ████████████░░░░░░        18 из 32 │
└──────────────────────────────────────────────┘
```

- Fondo blanco, `--radius-lg`, padding 16, ancho máx. 380.
- Imagen 64 × 64 `--radius-md` + título `title-card` + ProgressMeta.
- Variantes: `profession`, `course` (misma estructura).

#### AchievementsList

- SectionHeader "Ваши достижения" + fila de AchievementTile (gap 8).

#### ResumeCard (detalle de curso)

- Fondo blanco, `--radius-lg`, padding 12.
- Miniatura 80 × 56 `--radius-md` + texto (`micro` "Продолжить просмотр", `body-strong` título, `caption` "18 из 32") + IconButton `play` abajo a la derecha.

#### CourseProgressCard

- Fondo blanco, `--radius-lg`, padding 20.
- `micro` "Ваш прогресс курса" → `h3` título del curso → ProgressBar (alto 10) → ProgressLegend → Divider → `caption` "0/1 практическая работа".
- Gap vertical 12.

#### CertificateRow

- Fondo blanco, `--radius-lg`, padding 12 16, flex con `space-between`.
- `body-strong` "Сертификат" + Button `disabled` "Скачать" (pasa a `primary` cuando el curso está completo).

#### ModuleAccordion (lista de videos)

```
Видео
┌───────────────────────────────────────────────┐
│ [1]  О Курсе                          ✓   ⌄   │
├───────────────────────────────────────────────┤
│ [4]  Специфика мобильных платформ         ⌃   │
│      [thumb ✓]  [thumb]  [thumb]              │
└───────────────────────────────────────────────┘
```

| Propiedad | Valor |
|---|---|
| Contenedor | fondo blanco, `--radius-lg`, padding 20, título `h4` "Видео" |
| Fila (cerrada) | fondo `--gray-50`, `--radius-md`, alto 52, padding 0 12, gap 8 entre filas |
| Contenido de fila | ModuleNumber → título `body-strong` (flex 1) → StatusCheck → chevron |
| Fila (abierta) | chevron rota 180°; panel con grid de VideoThumbnail (3 columnas, gap 12, padding 12) |
| Accesibilidad | Cabecera = `<button aria-expanded>`; panel con `role="region"` |

---

## 5. Plantillas y páginas

### Plantilla: AppShell

```
AppShell
├── Sidebar (variant: collapsed | expanded)
└── Main
    ├── Topbar
    └── Content (slot)
```

### Página 1 — Catálogo (`/courses`)

```
AppShell [sidebar: collapsed, activo: Все курсы]
└── Content
    ├── PromoBanner
    └── CatalogLayout
        ├── FilterPanel
        │   ├── SearchField
        │   ├── FilterGroup "Вид" (Chips)
        │   ├── FilterGroup "Сложность" (Radios)
        │   └── FilterGroup "Тематика" (Checkboxes)
        └── CourseGrid
            └── CourseCard × n
```

### Página 2 — Dashboard (`/`)

```
AppShell [sidebar: expanded, activo: Главная]
└── Content (2fr | 1fr)
    ├── Columna izquierda
    │   ├── WelcomeBlock
    │   │   ├── h1 + subtítulo
    │   │   ├── StreakHint
    │   │   └── DayTile × 5
    │   ├── SectionHeader "Ваши профессии"
    │   │   └── LearningProgressCard (profession)
    │   └── SectionHeader "Ваши курсы"
    │       └── LearningProgressCard (course) × n
    └── Columna derecha
        ├── ContinueWatchingCard
        └── AchievementsList
            └── AchievementTile × 3
```

### Página 3 — Detalle de curso (`/courses/:id`)

```
AppShell [sidebar: expanded, activo: Все курсы]
└── Content
    ├── BackLink
    └── CourseLayout (280px | 1fr)
        ├── Columna izquierda
        │   ├── ResumeCard
        │   ├── CourseProgressCard
        │   └── CertificateRow
        └── ModuleAccordion
            └── ModuleItem × n
                └── VideoThumbnail × n (cuando está abierto)
```

---

## 6. Contenido / copy

Textos originales (ruso) con traducción de referencia.

### Navegación y header

| Original | Español |
|---|---|
| Главная | Inicio |
| Все курсы | Todos los cursos |
| Центр карьеры | Centro de carrera |
| Настройки | Ajustes |
| Платежи | Pagos |
| Выйти | Salir |
| Нина В | Nina V (usuaria) |

### Catálogo

| Original | Español |
|---|---|
| 15% скидка | 15% de descuento |
| На все курсы английского языка по промокоду: | En todos los cursos de inglés con el código: |
| Подробнее об акции и условиях активации промокода | Más sobre la promoción y cómo activar el código |
| Найти | Buscar |
| Вид: Любое · Курс · Профессия | Tipo: Cualquiera · Curso · Profesión |
| Сложность: Неважно · Новичок · Любитель · Профессионал | Dificultad: Indiferente · Principiante · Aficionado · Profesional |
| Тематика: Английский язык · Программирование · Дизайн · Финансы | Temática: Inglés · Programación · Diseño · Finanzas |

### Cursos del catálogo

| Título | Badges | Duración |
|---|---|---|
| 1С-программист | Профессия, Сертификат | 6 месяцев |
| Графический дизайнер | Профессия | 12 месяцев |
| Нейросети. Практическое применение | Курс | 3 недели |
| Дизайн мобильных приложений от нуля до продвинутого уровня | Профессия, Сертификат | 2 месяца |
| Как продавать на маркетплейсах | Курс, Популярно | 6 месяцев |
| Разработка игр на Unity | Курс | 6 месяцев |

### Dashboard

| Original | Español |
|---|---|
| Добрый день, Нина В! | ¡Buenas tardes, Nina V! |
| Продолжайте в том же духе, у вас отличный темп. | Sigue así, llevas un ritmo excelente. |
| Осталось 1 день до достижения СТРИК | Falta 1 día para lograr la racha |
| ПН · ВТ · СР · ЧТ · ПТ | Lun · Mar · Mié · Jue · Vie |
| Продолжить просмотр | Continuar viendo |
| Ваши профессии / Ваши курсы / Ваши достижения | Tus profesiones / Tus cursos / Tus logros |
| Первый день · Идеальное ДЗ · Урок в подарок | Primer día · Tarea perfecta · Clase de regalo |

### Detalle de curso

| Original | Español |
|---|---|
| Назад | Atrás |
| Адаптация под разные платформы | Adaptación a distintas plataformas |
| Ваш прогресс курса | Tu progreso del curso |
| 18 просмотрено · 32 осталось | 18 vistos · 32 restantes |
| 0/1 практическая работа | 0/1 trabajo práctico |
| Сертификат · Скачать | Certificado · Descargar |
| Видео | Videos |
| 1 О Курсе · 2 Первый дизайн-макет · 3–6 Специфика мобильных платформ | Sobre el curso · Primer mockup · Particularidades de plataformas móviles |
| 4.1 Введение · 4.2 Отличия от десктопа · 4.3 Гайдлайны платформ | Introducción · Diferencias con escritorio · Guías de plataforma |

---

## 7. Tokens exportables

### 7.1 CSS custom properties

```css
:root {
  /* Marca — azul eléctrico sólido */
  --blue-50:  #EBF1FF;
  --blue-100: #D6E3FF;
  --blue-200: #ADC7FF;
  --blue-300: #7AA5FF;
  --blue-400: #3D7BFF;
  --blue-500: #0055FF;
  --blue-600: #0047D6;
  --blue-700: #0039AD;
  --blue-800: #002B85;
  --blue-900: #001D5C;

  /* Neutros */
  --gray-0:   #FFFFFF;
  --gray-50:  #F5F7FA;
  --gray-100: #E9ECF1;
  --gray-200: #DDE2EA;
  --gray-300: #C4CBD6;
  --gray-400: #9AA3B2;
  --gray-500: #6B7385;
  --gray-700: #363D4A;
  --gray-900: #121722;

  /* Semánticos */
  --green-500:  #22C55E;
  --green-600:  #16A34A;
  --yellow-400: #FFC83D;
  --yellow-600: #D99A00;
  --red-500:    #EF4444;

  /* Alias */
  --color-bg-canvas: var(--gray-100);
  --color-bg-surface: var(--gray-0);
  --color-bg-surface-muted: var(--gray-50);
  --color-bg-brand: var(--blue-500);
  --color-text-primary: var(--gray-900);
  --color-text-secondary: var(--gray-500);
  --color-text-tertiary: var(--gray-400);
  --color-text-on-brand: var(--gray-0);
  --color-text-on-brand-muted: var(--blue-100);
  --color-text-link: var(--blue-600);
  --color-border: var(--gray-200);
  --color-success: var(--green-500);
  --color-warning: var(--yellow-600);
  --color-focus: var(--blue-400);

  /* Tipografía */
  --font-sans: "Inter", "Segoe UI", Roboto, Arial, sans-serif;

  /* Espaciado */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px;
  --space-12: 48px;

  /* Radios */
  --radius-sm: 6px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-2xl: 24px;
  --radius-pill: 999px;

  /* Sombras */
  --shadow-sm: 0 1px 2px rgba(18, 23, 34, 0.06);
  --shadow-md: 0 8px 24px rgba(18, 23, 34, 0.10);

  /* Layout */
  --sidebar-collapsed: 72px;
  --sidebar-expanded: 240px;
  --topbar-height: 80px;

  /* Motion */
  --duration-fast: 120ms;
  --duration-base: 200ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
}

@media (prefers-reduced-motion: reduce) {
  :root { --duration-fast: 0ms; --duration-base: 0ms; }
}
```

### 7.2 JSON (formato Design Tokens / Tokens Studio)

```json
{
  "color": {
    "blue": {
      "50":  { "$value": "#EBF1FF", "$type": "color" },
      "100": { "$value": "#D6E3FF", "$type": "color" },
      "200": { "$value": "#ADC7FF", "$type": "color" },
      "300": { "$value": "#7AA5FF", "$type": "color" },
      "400": { "$value": "#3D7BFF", "$type": "color" },
      "500": { "$value": "#0055FF", "$type": "color" },
      "600": { "$value": "#0047D6", "$type": "color" },
      "700": { "$value": "#0039AD", "$type": "color" },
      "800": { "$value": "#002B85", "$type": "color" },
      "900": { "$value": "#001D5C", "$type": "color" }
    },
    "gray": {
      "0":   { "$value": "#FFFFFF", "$type": "color" },
      "50":  { "$value": "#F5F7FA", "$type": "color" },
      "100": { "$value": "#E9ECF1", "$type": "color" },
      "200": { "$value": "#DDE2EA", "$type": "color" },
      "300": { "$value": "#C4CBD6", "$type": "color" },
      "400": { "$value": "#9AA3B2", "$type": "color" },
      "500": { "$value": "#6B7385", "$type": "color" },
      "700": { "$value": "#363D4A", "$type": "color" },
      "900": { "$value": "#121722", "$type": "color" }
    },
    "green":  { "500": { "$value": "#22C55E", "$type": "color" }, "600": { "$value": "#16A34A", "$type": "color" } },
    "yellow": { "400": { "$value": "#FFC83D", "$type": "color" }, "600": { "$value": "#D99A00", "$type": "color" } },
    "red":    { "500": { "$value": "#EF4444", "$type": "color" } }
  },
  "typography": {
    "display":     { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "64px", "lineHeight": "60px", "fontWeight": 800 } },
    "display-sm":  { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "36px", "lineHeight": "36px", "fontWeight": 700 } },
    "h1":          { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "28px", "lineHeight": "36px", "fontWeight": 700 } },
    "h2":          { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "20px", "lineHeight": "28px", "fontWeight": 700 } },
    "h3":          { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "18px", "lineHeight": "24px", "fontWeight": 700 } },
    "h4":          { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "16px", "lineHeight": "22px", "fontWeight": 600 } },
    "title-card":  { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "15px", "lineHeight": "20px", "fontWeight": 600 } },
    "body":        { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 400 } },
    "body-strong": { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "14px", "lineHeight": "20px", "fontWeight": 600 } },
    "body-sm":     { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "13px", "lineHeight": "18px", "fontWeight": 400 } },
    "caption":     { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "12px", "lineHeight": "16px", "fontWeight": 400 } },
    "micro":       { "$type": "typography", "$value": { "fontFamily": "Inter", "fontSize": "10px", "lineHeight": "12px", "fontWeight": 600 } }
  },
  "spacing": {
    "1": { "$value": "4px",  "$type": "dimension" },
    "2": { "$value": "8px",  "$type": "dimension" },
    "3": { "$value": "12px", "$type": "dimension" },
    "4": { "$value": "16px", "$type": "dimension" },
    "5": { "$value": "20px", "$type": "dimension" },
    "6": { "$value": "24px", "$type": "dimension" },
    "8": { "$value": "32px", "$type": "dimension" },
    "10": { "$value": "40px", "$type": "dimension" },
    "12": { "$value": "48px", "$type": "dimension" }
  },
  "radius": {
    "sm":   { "$value": "6px",   "$type": "dimension" },
    "md":   { "$value": "12px",  "$type": "dimension" },
    "lg":   { "$value": "16px",  "$type": "dimension" },
    "xl":   { "$value": "20px",  "$type": "dimension" },
    "2xl":  { "$value": "24px",  "$type": "dimension" },
    "pill": { "$value": "999px", "$type": "dimension" }
  },
  "shadow": {
    "sm": { "$type": "shadow", "$value": { "offsetX": "0px", "offsetY": "1px", "blur": "2px",  "spread": "0px", "color": "#1217220F" } },
    "md": { "$type": "shadow", "$value": { "offsetX": "0px", "offsetY": "8px", "blur": "24px", "spread": "0px", "color": "#1217221A" } }
  }
}
```

---

### Checklist de implementación

- [ ] Ningún `gradient` en el código (buscar `gradient` en todo el proyecto).
- [ ] Sidebar y PromoBanner usan `var(--blue-500)` plano.
- [ ] Nav item activo = fondo blanco + texto azul (no transparencias).
- [ ] Todos los IconButton tienen `aria-label`.
- [ ] ProgressBar con `role="progressbar"` y valores ARIA.
- [ ] Acordeón con `aria-expanded` y navegación por teclado.
- [ ] Focus visible con `--color-focus` en todos los elementos interactivos.
