# MEMORY.md — Estado y contexto que un agente debe conocer antes de tocar nada

Memoria compartida del proyecto. Complementa a `AGENTS.md`: allí están las reglas y los contratos; aquí está **el estado real**, **lo que ya se hizo y cómo**, y **las trampas encontradas**.

**Mantenerlo al día:** quien cambie el estado (aplicar una migración, ingerir fuentes, cerrar un pendiente) actualiza este archivo en el mismo commit. Las fechas son absolutas.

---

## 1. Estado actual (2026-10-04)

| Frente | Estado |
|---|---|
| `AGENTS.md` (contexto, contratos, roadmap) | ✅ Hecho |
| Migraciones Supabase (extensiones, tablas, RAG, RLS) | ✅ Aplicadas en remoto |
| Seed demo | ✅ Cargado en remoto |
| Ingesta RAG (3 PDFs INEGI ENUT 2024) | ✅ 535 pasajes limpios con embedding: cuestionario por pregunta (88), diseño conceptual (402), diseño muestral (45). FTS en español |
| Web: espina de descubrimiento (`/`) | ✅ 2026-10-04 (noche), rama `feat/researcher-ux`: rediseño para **investigadores** (lectura a su ritmo). Navegación: botón fijo "Start investigation" en la cabecera del home; "Home" en la cabecera durante y después de la corrida y "Back to home" al final (también el enlace Discovery del sidebar, vía el evento `tiempo:home`); `?start=1` arranca la corrida (lo usan los botones de la guía); se quitó "guided" de los textos y los íconos de "How the lab works". La Reading guide (`app/guide/`) se reescribió: qué es tiemPO, controles, los 7 pasos, cómo leer una tarjeta, glosario de estados, números y evidencia; la página (servidor) lee el bundle y pasa solo etapas, estados y experimentos a `Guide.tsx` (cliente). Se borró `SpineGuide.tsx`. Explicaciones para lectores externos: `ExperimentView.plain` (título, qué hizo, por qué corrió, qué encontró; derivado del spec, la decisión, la revisión y el resultado) y `CritiqueView.plain`; tarjetas EXP en el hero y botones "EXP-00N · what was it?" durante la corrida (el hallazgo se oculta con `isRevealed` hasta su etapa); recuadros "In plain words" en experimentos y críticas; la crítica muestra veredicto + razón + preguntas abiertas y pliega el resto ("Show the critic's full review"); el inspector abre con "What this is" y pliega los detalles técnicos. Iteración anterior (brief "Storytelling, Provenance & Interactive Agent Discovery"): hero con misión, insignias de procedencia, "How the lab works", la pregunta y los 7 agentes (Literature Agent y Data Steward marcados "Implemented, not in this session": no hay artefactos suyos y no se inventan); en cada turno se listan `Stage.checks` (validaciones reales de las tools) y las puertas humanas (REVIEW) se abren y cierran; controles Previous/Play/Next (← Space →); `HandoffPanel` muestra `ArtifactRef.handoff` (extracto real del JSON, rutas locales saneadas, ~61 KB más en el bundle); al final `Overview` + `KeyResults` (forest plot, interacción y limitaciones). La prueba C ahora busca `DATABRICKS_`/`databricks.com` en vez de cualquier mención. Antes, la portada pasó a ser una **consola**: compositor con la pregunta aprobada → `Run discovery` → turnos de agente (`AgentWorking`: agente, acción y artefactos guardados) → etapa revelada; la conclusión y el resumen `Overview.tsx` ("Where the investigation stands now") llegan al final. Etiqueta "Replaying the recorded session" visible. `isRevealed` en el contexto oculta estados fijados por artefactos posteriores (H1–H3 en la pregunta, "Ran as" y auditorías en propuestas). `?view=full` muestra todo (la prueba R lo usa); LIVE abre completo. Antes, en la misma rama, la portada abría con "Where the investigation stands" (`Overview.tsx`): estado de H1–H4 con el artefacto que lo fijó, experimentos con resultado y revisión, y preguntas abiertas de la última crítica. La cabecera es una barra de secciones con scroll spy; el replay pasa a botón secundario "Walkthrough" (mismos atajos). Cada código de estado lleva una etiqueta en lenguaje llano y su significado (glosario `STATUS_TEXT` en `model.ts`, campos `label`/`meaning` de `StatusView`); el código exacto sigue visible salvo cuando es la misma palabra. Cada etapa muestra la pregunta que responde (`Stage.purpose`, `shortTitle`). Pruebas A–L + R pasan. 2026-10-04 (tarde): **integrada con la cadena real hasta EXP-002**. Adaptador `normalizeDiscoveryRun` (`web/lib/discovery/model.ts`) con `research_state.json` como índice → `DiscoveryRunViewModel` → **7 etapas** agrupadas a pedido del usuario: (1) pregunta; (2) evidencia de EXP-001; (3) crítico; (4) hipótesis + REV-001 + propuestas; (5) decisión: DEC-001 + capacidad del motor + historial DEC-001…005 + aprobación REV-DEC-005-001; (6) EXP-002 con la interacción como prueba formal + su crítica; (7) H3 `UNTESTED → INCONCLUSIVE`. Las etapas agrupadas guardan sus piezas en `stage.parts`. REPLAY lee `web/data/discovery-run.json` (normalizado, generado en `prebuild`); `npm run test:discovery` pasa las pruebas A–L. Antes, ese mismo día: tras `/impeccable critique` (22/40, `.impeccable/critique/`), el titular es el hallazgo leído de `result.json`, las etapas pendientes forman la banda **Next in the loop**, el aviso de ranking nombra los 6 pares, H1/H2 muestran la evaluación del motor, el inspector enlaza a GitHub en el commit del snapshot y da el comando de reproducción, y se corrigió la accesibilidad (región viva, foco, skip link, contraste). "Audit trail" salió del sidebar (`/audit` sigue por URL). Escala de lectura subida para proyección (body 16/24, body-sm 15/22, caption 13/18, párrafos de apoyo 17/28; ver `DESIGN.md`). 2026-10-03: Nombre en la web: **tiemPO** (wordmark Inter 900); polish "menos saturado": banner blanco, controles en texto, etiquetas de tipo como muestra de color. Sistema Education2025. Lee artefactos del repo: REPLAY (snapshot `web/data/discovery-snapshot.json`, solo archivos versionados) y LIVE (`/?mode=live`, solo local). Etapas 1–4 reales; 5–9 se muestran como pendientes hasta que los agentes escriban sus artefactos. Probado con un fixture sintético fuera del repo. `npm run build` pasa |
| Web: auditoría Supabase (`/audit`, `/research/[id]`) | ✅ Restilizada; misma lógica |
| Pipeline ENUT → `analytic_v1` | ✅ Construido y validado fuera del repo (fases 1 → 2A → 2B). **`APPROVED_FOR_EXPERIMENTS`**. ENUT 2024, n = 2,563. Documentación en `docs/` y `metadata/analytic_v1_manifest.json` (commit `805b7c2`) |
| Motor de experimentos (`src/experiments/`) | ✅ Determinista, `ExperimentSpec` → `ExperimentResult`, solo `weighted_linear_regression` con CR1 por UPM. Tests en `tests/` |
| EXP-001 | ✅ `EXPERIMENT_COMPLETED`, `REQUIRES_HUMAN_REVIEW`, `INCONCLUSIVE_RANKING`. Resultados en `reports/experiments/EXP-001/` (ver §4) |
| EXP-002 | ✅ `EXPERIMENT_COMPLETED`, `REQUIRES_HUMAN_REVIEW`. Interacción traslado × sexo para sueño (PROP-003, elegida en DEC-005 y aprobada en REV-DEC-005-001). Interacción −17.715 [−47.532, 12.101], `INCONCLUSIVE_INTERVAL_INCLUDES_ZERO`; ranking `NOT_APPLICABLE_SINGLE_OUTCOME`. CRIT-EXP-002-002: **H3 `UNTESTED` → `INCONCLUSIVE`**. Resultados en `reports/experiments/EXP-002/` |
| Motor de experimentos: empaquetado | ✅ Clon limpio verificado el 2026-10-03: `pip install -r requirements-experiments.txt`, validador PASS, EXP-001 con 0 diferencias numéricas, sin datos crudos ni `staging_v1` (§5). Ese clon era Windows; en Linux pasa desde el 2026-10-03 con tolerancia relativa 1e-9 en floats (§5). Pendiente: borrar `audit/` y `metadata/provenance.json`; validar `omnigent.yaml` en un entorno con Omnigent |
| Tools (`agents/commute_lab/tools.py`) | ✅ Reescritas el 2026-10-03: 15 tools conectadas al motor real (`run_experiment` → `scripts/run_experiment.py` en `.venv-experiments`; `save_proposals` verifica specs en seco con `scripts/check_experiment_spec.py`). Smoke test completo contra Supabase sin LLM (ver §5) |
| Capa agéntica de descubrimiento | ✅ Implementada en `omnigent.yaml` + `initial_state.json`: EXP-001 → crítico → literatura → hipótesis → Data Steward → ≥2 candidatos → el Director elige → runner → crítico → decisión actualizada (`AGENTS.md` §7.2). ⏳ Falta la primera sesión real con LLM |
| Agentes Omnigent | 🟡 Executor: `openai-agents` + `databricks-gpt-oss-120b` (Databricks Free Edition) vía el provider `databricks-serving`. Specs validados **sin stubs** (`omnigent.yaml`: 15 tools; `agents/scientific_critic.yaml`: 2). ✅ **Primera corrida real**: el Scientific Critic criticó EXP-001 → `reports/discovery/local/critiques/CRIT-EXP-001-001.json` (§5, "Omnigent en Windows"). Falta instalar `supabase` en el entorno de Omnigent para las tools que persisten. Bright Data (`search_web`) sin credenciales todavía |
| Shared Research State | ✅ Rama `feat/research-state` (2026-10-03): `agents/commute_lab/research_state.py` + `scripts/build_research_state.py` reconstruyen el estado desde `reports/experiments/` y `reports/discovery/local/` (sin BD, sin cifras copiadas: punteros JSON). Snapshot generado en `reports/discovery/local/research_state.json`. Contrato de IDs y referencias para hipótesis, candidatos y decisiones en `docs/RESEARCH_STATE.md`; escribir artefactos con `save_artifact` (nunca sobrescribe). Tests: `PYTHONPATH=agents python -m unittest discover -s agents/tests` |
| Discovery Director | ✅ Rama `feat/discovery-director` (2026-10-03): `agents/discovery_director.yaml` + `commute_lab/director_tools.py` (5 tools, solo librería estándar, sin ExperimentRunner). Recalcula la ejecutabilidad de cada `PROP-*` con la auditoría en vivo del motor (`planner_tools.capability_audit`) y distingue la mejor propuesta científica de la mejor ejecutable hoy. **Corrida real** (Linux, Databricks `gpt-oss-120b`): `DEC-001` = `WAITING_FOR_ENGINE_CAPABILITY`, preferida PROP-003, ejecutable hoy PROP-005, falta `interaction_terms`. Al extender el motor se vuelve a correr y crea `DEC-002` (nunca sobrescribe). La ejecutabilidad combina la auditoría del schema con `metadata/experiment_engine_capabilities.json` (export del motor): con las interacciones de moderador binario (PR #3), PROP-003, PROP-008 (`has_child_u15` entra como moderador, no como covariable) y PROP-009 ya son ejecutables. ✅ **RUN B** (rama `feat/director-rerun`): `DEC-002` = `READY_TO_EXECUTE`, misma preferencia PROP-003, ahora ejecutable; `next_action` del estado = `run_experiment` con aprobación humana previa. Una primera corrida de RUN B se descartó sin commitear porque decía "strongest observed negative association" y que el test aclararía el ranking: el validador ahora rechaza `RANKING_OVERCLAIM`, "resolve/clarify the ranking", "will resolve/establish" y un `READY_TO_EXECUTE` sin aprobación humana en `next_action` |
| Papers de OpenAlex | 🟡 `search_openalex` funciona y registra cada paper en `sources` (`kind = 'paper'`, solo metadatos y resumen, sin pasajes) |
| Despliegue en Vercel | ✅ https://commute-time-lab.vercel.app (producción, pública). Redeployado el 2026-10-04 desde GitHub `main` @ `948229a` (correcciones de la validación E2E; antes `22ce188`); `test:discovery` pasa contra la URL de producción |
| Validación E2E (2026-10-04) | ✅ En Linux sobre `main` @ `47f27c2`: motor 35/35, agentes 49/49, validador del motor PASS, EXP-002 reproducido en memoria (0 diferencias fuera de 1e-9), 28 hashes de `research_state.json` OK, REPLAY sin red (namespace aislado) OK, autoplay 55 s. **Prueba real Omnigent → Databricks**: Scientific Critic sobre EXP-002 en un `git clone` de scratch (no en el repo), 4 llamadas `chat/completions` 200, el validador rechazó el primer `save_scientific_critique` y el agente lo corrigió. Correcciones de UI en el árbol de trabajo (sin commit ni deploy): scroll del autoplay en etapas altas, razonamiento de DEC-002…005 visible, cambio DEC-002→003 rotulado como cambio de auditoría (hashes del motor iguales), crítica más reciente gana en `updates`, LIVE exige `initial_state.json` + `reports/experiments` + `reports/discovery` (en Vercel `/?mode=live` mostraba un run vacío). Hallazgo científico abierto: HYP-005/007/008 dicen "contradicted if the interval includes zero", contra REV-DEC-005-001 y el motor (INCONCLUSIVE); el validador de hipótesis lo acepta |
| Repo | ✅ `feat/ui` fusionada en `main` (2026-10-04, fast-forward). En Linux, verificado: 35 tests del motor y 49 de agentes OK; `validate_experiment_engine.py` PASS (EXP-001 con diferencias relativas ≤ 3.4e-11, dentro de la tolerancia 1e-9 de un sistema distinto); `research_state.json` vigente; web build y `test:discovery` OK |

## 2. Infraestructura

### Repositorio y trabajo en equipo
- Remoto: `origin` = `https://github.com/RogelioZu/Hack-nation-hackathon.git`, rama `main`.
- El 2026-10-03, `origin/main` tenía 4 commits del equipo: `README.md`, `AGENTS.md` (arquitectura de agentes), `omnigent.yaml` e `initial_state.json`. Nuestra historia local era **independiente**: no compartían ningún commit. Se fusionaron con `git pull --allow-unrelated-histories`.
- Solo `AGENTS.md` tuvo conflicto. Se resolvió con un único `AGENTS.md` en español que integra la arquitectura de 7 agentes y el Shared Research State (§7). Las diferencias entre ambos diseños quedaron como **Decisiones abiertas** al final de `AGENTS.md`.
- `omnigent.yaml` e `initial_state.json` **no se modificaron** en el merge. Cambiarlos requiere acordar antes las decisiones abiertas con el equipo.

### Supabase
- Proyecto del hackathon: **`xnbruiprrxradfidoleu`** (us-east-1, Postgres 17). URL: `https://xnbruiprrxradfidoleu.supabase.co`.
- ⚠️ La cuenta tiene **otro** proyecto, "Finding out" (`fnveucrdccqwzovptxqa`), que **no es de este hackathon**. No tocarlo.
- El acceso se hace por el **MCP de Supabase**. Hubo que reautenticarlo con `/mcp` para que viera este proyecto. La **CLI `supabase` no tiene sesión iniciada**, así que `supabase db push` y `supabase link` no funcionan todavía.
- Migraciones aplicadas con `apply_migration` del MCP. Versiones remotas: `20261003210503_extensions`, `20261003210519_core`, `20261003210530_rag`, `20261003210538_rls`, `20261003221539_rag_spanish_fts`.
  - **Los archivos locales se renombraron para coincidir con esas versiones.** Si aplicas otra migración por MCP, consulta `list_migrations` y renombra el archivo local a la versión que devuelva. Si no, un `db push` futuro intentará reaplicarla.
- El seed se cargó con `execute_sql` del MCP, no con `db reset`.
- **Advisor de seguridad:** no reporta nada sobre nuestras tablas. Sí avisa sobre `public.rls_auto_enable()`, una función `SECURITY DEFINER` que **ya existía en el proyecto** y que se puede llamar sin sesión vía `/rest/v1/rpc/rls_auto_enable`. No se tocó; **el usuario debe decidir** si se le quita `EXECUTE` a `anon` y `authenticated`.
- RLS verificado por REST con la clave publishable: `select` funciona y `insert` falla con `42501 new row violates row-level security policy`.

### Claves y archivos `.env` (ignorados por git)
- `web/.env.local` contiene `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (la clave publishable es `sb_publishable_…`, pública).
- `.env` en la raíz lo gestiona el usuario y contiene `SUPABASE_SERVICE_ROLE_KEY`. **Nunca imprimir su valor.** Para revisarlo, mostrar solo los nombres (`cut -d= -f1 .env`).
- El MCP **no** expone la clave `service_role`. Hay que pedírsela al usuario.

### IDs fijos del seed demo
- Proyecto: `00000000-0000-0000-0000-000000000001`, accesible en `/research/00000000-0000-0000-0000-000000000001`.
- Fuentes demo: `…0a1`, `…0a2`. Hipótesis: `…0b1`. Propuestas A/B: `…0c1`, `…0c2` (B está seleccionada). Run pendiente: `…0d1`.
- Todo el seed tiene `is_demo = true` o el prefijo `[DEMO]`. Cuando exista el ciclo real, crear un proyecto nuevo o limpiar estas filas; nunca mezclar resultados reales con ellas.

## 3. RAG: estado y calidad

- Corpus en `analysis/rag/corpus.json` (3 fuentes INEGI ENUT 2024). Los PDFs se guardan en `analysis/.cache/`, con nombre igual al `sha1(url)`.
  - **Cuestionario** (`kind = 'questionnaire'`, PDF propio de INEGI `enut_2024_cuestionario.pdf`): solo pp. 3–25. Las pp. 26–73 repiten las secciones IV–VII para la 2.ª–4.ª persona y la p. 1 es texto legal. Un pasaje por pregunta numerada; `section` = `Sección V. … › Pregunta 5.9`, `locator` = `p. 12 · 5.9`.
  - **Diseño conceptual**: se excluyen portada y créditos (1–3), índice (5–6), separador (71), anexo B = cuestionario duplicado (91–115) y referencias (125–127). `section` sale de los marcadores del PDF (`6. … › 6.3 Uso del tiempo › 6.3.3 …`), cortando la página donde empieza cada encabezado.
  - **Diseño muestral**: se excluyen portada, índice y referencias (1–3, 5–6, 24).
- Limpieza (`analysis/rag/ingest.py`): NFKC (arregla las letras matemáticas del diseño muestral), unión de palabras cortadas con guion, encabezados/pies repetidos, números de página, instrucciones al entrevistador y guías de puntos (`Sí ....... 1` → `Sí = 1`). Se descartan fragmentos de < 60 caracteres (< 40 en el cuestionario), que eran encabezados sueltos. Se conservan "PASE A" y "FILTRO".
- `uv run python -m rag.ingest --dry-run` fragmenta y cuenta sin embeddings ni escrituras.
- La primera ejecución descarga el modelo e5-small (~470 MB) a la caché de HuggingFace. Las advertencias de `pypdf` sobre "fontTools" son inofensivas.
- **QA medido con `uv run python -m rag.eval`** (15 consultas fijas en `rag/eval_queries.json`, 5 en inglés; acierto = el pasaje contiene el texto esperado, sin acentos, y es del `kind` esperado). Mismo archivo antes y después, el 2026-10-03:

  | Métrica (k = 5) | Antes | Después |
  |---|---|---|
  | hit@1 | 0.60 | 0.80 |
  | hit@5 | 0.80 | 0.93 |
  | MRR | 0.69 | 0.86 |
  | Pasajes del top 5 con ruido de formulario | 31 % | 0 % |

  - El único ✗ ("tiempo de traslado al trabajo") es en parte un artefacto del criterio: los 4 primeros resultados son la definición de la variable de traslado (diseño conceptual p. 49), pero el texto esperado era la redacción del cuestionario ("trasladarse de ida y vuelta"). La pregunta 5.9 sí sale primera si la consulta menciona "pregunta" o "cuestionario".
  - "cuidado pasivo integrantes del hogar" bajó del 1.º al 3.º lugar: ahora ganan filas del anexo A que dicen "cuidados pasivos" (plural, no cuenta para el criterio). La definición (p. 58) sigue en el top 5.
  - Con 15 consultas, cambios pequeños de limpieza mueven hit@1 ±0.07. No sobreinterpretar décimas.
- **Debilidades que quedan:**
  1. La extracción de `pypdf` desordena las columnas del cuestionario: una pregunta puede arrastrar líneas de la vecina (p. ej. la 5.9 incluye el FILTRO 5.8). Por eso las etiquetas temáticas en mayúsculas no se usan como `section`.
  2. Sin IDF en Postgres: términos muy frecuentes ("tiempo", "trabajo") pesan tanto como los raros. RRF con la parte semántica lo compensa en parte.
  3. Las consultas en inglés dependen del glosario fijo de `rag/search.py`. Un término que no esté ahí solo cuenta con la parte semántica.
- **Mejoras posibles, aún no aplicadas:** reranker multilingüe (cross-encoder, ~470 MB más, ~1 s por consulta en CPU), filtro por `source_kind` en `hybrid_search` y en la tool, y diccionario de variables de microdatos 2024 (catálogo RNM de INEGI) como fuente `data_dictionary`.
- Los `sources` demo del seed (`…0a1`, `…0a2`) no tienen pasajes. Solo existen para la web.

## 4. Dataset ENUT y EXP-001

### Dataset `analytic_v1` (llegó en el commit `805b7c2`, 2026-10-03)
- **Año: ENUT 2024.** Fases del pipeline (todas con aprobación humana): 1 auditoría → 2A staging semántico (`staging_v1.parquet`, todas las personas de TMODULO) → 2B dataset canónico (`analytic_v1.parquet`) → 3 motor de experimentos y autorización de EXP-001.
- Una fila por persona; n = 2,563 (18–65 años, CDMX/Edomex, trabajadores activos con traslado resuelto). SHA256 `973f2c010940da06048eb12ade53fa271525d82f68d3a157ad78e429d687dd94`.
- El manifiesto (`metadata/analytic_v1_manifest.json`) dice `experiment_readiness = EXPERIMENT_READY` y `final_human_approval = pending`. **Eso es del momento de la fase 2B.** La aprobación posterior (fase 3, `APPROVED_FOR_EXPERIMENTS`) vive en `metadata/analytic_v1_experiment_approval.json`. No "corregir" el manifiesto: se preserva tal cual.
- Definiciones: `docs/DATA_CONTRACT.md` (la primera tabla es la vigente; las secciones "Historical Phase 1 / Phase 2A" de abajo son históricas y el runner las ignora a propósito).
- `staging_v1.parquet` y los CSV crudos (`data/raw/enut_2024/`) solo existen en local (`data/interim/` y `data/raw/` están ignorados por git). El motor no los lee; solo `scripts/validate_experiment_engine.py` los necesita para comparar hashes, así que **ese script no corre en un clon limpio**. `engine_validation.json` reporta 41 tests porque suma los 25 tests del pipeline, que no están en el repo; aquí hay 16.
- `analysis/enut/` ya no recibirá el pipeline: se construyó en otro entorno.
- Hallazgos previos que el pipeline confirmó: en ENUT 2024, P5_9 es el traslado; con P5_7 = 2 (solo virtual) se salta la 5.9 y el pipeline lo codifica como **cero estructural marcado**. En ENUT 2019, P5_9 era la búsqueda de trabajo (el codebook 2019 se descartó y nunca se commiteó).

### EXP-001 (resultado real)
- Pregunta: ¿qué dimensión del tiempo personal muestra la asociación negativa más fuerte con +5 h de traslado entre semana? Spec: `experiments/EXP-001/spec.json` (H1, H2; 4 outcomes; controles trabajo, edad, sexo, estado; sensibilidad `exclude_zero_weekday_work`; versiones ajustada y sin ajustar = 16 modelos).
- Coeficientes ajustados (min de lunes a viernes por +300 min de traslado): sueño **−48.711** [−63.48, −33.94]; ocio **−20.396** [−43.44, 2.64]; conversación en el hogar **−3.816** [−10.34, 2.71]; higiene **+3.094** [−0.76, 6.95].
- **`INCONCLUSIVE_RANKING`**: con Bonferroni, solo sueño − conversación y sueño − higiene excluyen el cero; sueño − ocio no. H1: evidencia compatible (sueño). H2: evidencia de al menos una diferencia, sin orden completo. H3/H4 no se evaluaron.
- Sensibilidad: excluir 34 personas con `work_weekday_min = 0` no cambia direcciones ni orden.
- Diagnósticos: 351 UPM, 19 estratos, R² ponderado ≤ 0.07, sin predicciones negativas, 168 puntos con leverage > 2p/n (se conservan).
- Alternativas que dejó EXP-001, **sin elegir**: no linealidad del traslado y diferencia por sexo.
- Frase correcta para la demo: "Longer weekday commuting showed the strongest negative point association with sleep in EXP-001, but uncertainty prevented a definitive ranking across all four time-use outcomes." **Nunca** "commuting definitely sacrifices sleep the most".
- Limitación que hay que conservar siempre: CR1 por UPM es una aproximación, no la varianza completa de encuesta compleja de ENUT.
- `experiments/EXP-001/result.json` y `reports/experiments/EXP-001/result.json` son idénticos.

## 5. Trampas técnicas encontradas

- **Next.js 16**:
  - `PageProps<'/research/[id]'>` necesita los tipos de ruta generados. Correr `npx next typegen` antes de `tsc --noEmit`; si no, aparece `TS2344`.
  - `params` es una `Promise`.
  - Las páginas llaman `await connection()` (en `lib/data.ts`) para renderizarse en cada request y no prerenderizarse con datos viejos.
  - `next dev` regenera `web/AGENTS.md`. No borrarlo.
- **`server-only`**: el paquete está instalado y lo importan `lib/supabase.ts` y `lib/data.ts`.
- **Python**: está fijado a **3.12** (`analysis/.python-version`) aunque el sistema tiene 3.14, para asegurar wheels de torch. Torch se instala desde el índice **CPU** (configurado en `pyproject.toml`).
- **Shell zsh**: una variable con espacios usada como comando (`P="psql -h …"; $P …`) **no** se separa en palabras y falla con exit 127. Usar `bash -c '…'` o funciones.
- **Probar migraciones localmente sin `supabase start`**:
  - La imagen `pgvector/pgvector:pg17` ya está descargada.
  - Crear antes el schema `extensions` y los roles `anon`, `authenticated` y `service_role` (este último con `bypassrls`), y poner `search_path = public, extensions`.
  - Así se validaron las 4 migraciones y el seed antes de aplicarlos en remoto.

- **Omnigent**:
  - La versión original de `omnigent.yaml` (commits del equipo) **no era un spec válido**: el loader la rechazaba por no tener `prompt`. Usaba campos inventados (`agents:` como lista, `role`, `system_prompt`, `handoffs`, `policies` como lista) y el comando `omnigent run --config … --state …`, que no existe. Se reescribió el 2026-10-03.
  - Para validar sin credenciales de modelo: `from omnigent.spec import load; load(Path("omnigent.yaml"))`. Si `is_omnigent_yaml()` devuelve False, `diagnose_yaml_rejection()` explica el motivo.
  - Los `callable` y `handler` se importan **al cargar** el spec. Si el módulo no se puede importar, el loader **no falla**: deja `callable=None` en silencio. Verificar siempre que cada `FunctionTool.callable` no sea `None` (ver la comprobación en el historial del 2026-10-03).
  - Las function tools reciben los argumentos del LLM como kwargs, y el resultado se convierte con `str()`. Por eso las tools devuelven JSON (`json.dumps`).
  - No llamar `agents` a un paquete propio: es el import del SDK `openai-agents`, que Omnigent instala.
  - Para el validador se usó un venv temporal con `omnigent[databricks]` 0.16.0 y Python 3.12, fuera del repo.
- **Smoke test de las tools** (2026-10-03, sin LLM): proyecto temporal `[SMOKE TEST]` → `register_experiment(EXP-001)` (idempotente) → `save_critique` → `save_hypothesis` → `save_proposals` (rechaza un spec `RANK_DEFICIENT`) → `select_candidate` (rechaza un candidato que exige revisar el contrato) → `run_experiment` (rechaza lo no seleccionado; corrió un spec real con id desechable `EXP-900`) → `record_decision`. Todo se borró al final (proyecto, `reports/discovery/<id>/`, `EXP-900`). Para repetirlo sin gastar `EXP-002`, parchear `tools._next_experiment_id`.
- **`inherit` no funciona en sub-agentes inline** (Omnigent 0.16): `_agent_tool_to_sub_spec` solo traduce `AgentTool` y `FunctionTool` anidados y descarta `InheritedTool`. Con `tools: {x: inherit}` el sub-agente queda sin tools, y `omnigent.spec.load` no avisa. Comprobar con `load(...).sub_agents[i].local_tools`.
- **Dos Pythons**: Omnigent está instalado con `uv tool` en Python 3.14 (trae supabase, httpx, sentence-transformers, pandas, pydantic) y ahí se importan las tools. El motor corre aparte en `.venv-experiments` (Python 3.12, `uv python install 3.12`; no había 3.12 en el sistema) para usar las versiones fijadas. `analysis/.venv` no existe en esta máquina.
- **`.env` no tiene `SUPABASE_DB_URL`** (vacía): no se pueden aplicar migraciones por `psql`. La CLI `supabase` tampoco tiene sesión.
- Restringir la población a un sexo con `sex` como covariable da `RANK_DEFICIENT` (lo mismo con `state`).

### Motor de experimentos: empaquetado (resuelto el 2026-10-03)
- **Verificado desde un clon limpio** (`core.autocrlf=true`, sin `data/raw/` ni `data/interim/`, venv nuevo con solo `pip install -r requirements-experiments.txt`): 16 tests OK, `validate_experiment_engine.py` PASS, `run_experiment.py` reproduce EXP-001 con **0 diferencias en 1,801 valores numéricos**, y el SHA256 del parquet no cambia.
- `requirements-experiments.txt` es autocontenido: numpy, pandas, pyarrow, pydantic, scipy (motor) + statsmodels, patsy (tests), con las versiones del runtime de EXP-001. Requiere Python ≥ 3.11; el Python por defecto de esta máquina es 3.7, así que usar `py -3.12`.
- **Ruta larga en Windows:** instalar statsmodels en un venv con ruta profunda falla con `OSError [Errno 2]` (límite de 260 caracteres por sus archivos de test anidados). Usar una ruta de venv corta o habilitar rutas largas.
- `validate_experiment_engine.py` ya **no** lee datos crudos ni `staging_v1`, y no cuenta los tests del pipeline. Comprueba: hash aprobado (parquet = manifiesto = aprobación) y consistencia con el manifiesto (vía `load_approved`), JSON Schema = modelos Pydantic, registro de métodos = esquema, tests del motor, EXP-001 dos veces idéntico, igualdad con el `result.json` commiteado (floats con tolerancia relativa `FLOAT_REL_TOL = 1e-9`; enteros, IDs, estados, hashes y claves exactos; salvo `code_sha256`, `code_fingerprints`, `protocol_fingerprints` y `runtime`), bytes de `result.json` = `result_sha256` de `validation.json`, y entradas sin cambios. Escribe `engine_validation.json`.
- **Finales de línea (`.gitattributes`):** LF forzado en `*.py`, `*.md`, `*.json`, `*.yaml`, `*.yml` y `*.txt`; parquet y PDF binarios. Dos excepciones con `-text` (bytes exactos): `metadata/analytic_v1_manifest.json` y `reports/experiments/EXP-001/result.json`. Ambos se generaron con CRLF, y la procedencia registra el hash de esos bytes (`manifest_sha256` f800513b…, `result_sha256` 5e4084a3…), pero git los había guardado con LF (f23add97…, 3113a9ee…). Un clon limpio no coincidía con la procedencia de EXP-001. Las cifras nunca cambiaron.
  - ⚠️ El commit `2d00fda` puso `-text` pero **no** volvió a agregar los bytes CRLF: git siguió guardando LF y en cualquier clon nuevo el validador daba `RESULT_BYTES_DRIFT` y `read_experiment_artifact` del crítico rechazaba EXP-001. Solo funcionaba en la máquina donde los archivos seguían con CRLF. Corregido el 2026-10-03 convirtiendo LF → CRLF (los hashes coinciden exactamente con f800513b… y 5e4084a3…). Comprobar con `git ls-files --eol`: debe decir `i/crlf`.
- **Reproducción entre plataformas:** reejecutar EXP-001 en Linux da 821 de 1,127 floats no idénticos bit a bit frente al resultado generado en Windows, con diferencia relativa máxima 3.4 × 10⁻¹¹ (BLAS/libm). Por eso el validador compara floats con tolerancia relativa 1e-9 y reporta `exp001_floats_not_bit_identical` y `exp001_max_float_relative_difference`. `run_experiment.py` sigue exigiendo igualdad exacta entre sus dos corridas en la misma máquina.
- **Al commitear:** git no detecta solo que esos dos archivos cambiaron, porque su fecha de modificación no cambió. Agregarlos explícitamente: `git add .gitattributes metadata/analytic_v1_manifest.json reports/experiments/EXP-001/result.json`. El diff muestra ~8,000 líneas por archivo, pero solo cambian los finales de línea.
- `scripts/run_experiment.py` ahora escribe siempre LF (`newline="
"`), así que sus salidas y `result_sha256` son iguales en cualquier sistema. Antes, en Windows escribía CRLF.
- **Procedencia de entorno:** el runner hashea su código, `requirements-experiments.txt`, `docs/EXPERIMENT_ENGINE.md` y los docs de protocolo (`AGENTS.md`, `docs/*`). Cualquier edición de esos archivos cambia `code_sha256` y `protocol_fingerprints` en una reejecución, sin tocar cifras. El validador lo reporta en `exp001_environment_provenance_changed`.
- **Correr los tests directamente:** `PYTHONPATH=. python -m unittest discover -s tests` (`tests/` no es paquete; con `-t .` falla). `src/experiments/report.py` no depende de `tests/`: la dependencia es solo tests → producción.
- **Pendiente (requiere permiso del usuario):** borrar `audit/` (idéntica byte por byte a `reports/audit/`; ningún doc ni JSON la cita) y `metadata/provenance.json` (0 bytes, sin consumidores): `git rm -r audit metadata/provenance.json`.
- El mensaje del commit `04df096` perdió letras (`ngine_validation`, `equirements`…) por secuencias de escape. Es cosmético y está en `origin`: no reescribir la historia.

### Omnigent en Windows (verificado el 2026-10-03 en la máquina del usuario)
- **Instalación:** uv 0.12.23 con winget (`astral-sh.uv`) y `uv tool install --python 3.12 "omnigent[databricks]"` (0.16.0). Sin el extra falla con "databricks-sdk is required". Binarios en `~/.local/bin`, que ya está en el PATH. Databricks CLI v1.19.0 (winget `Databricks.DatabricksCLI`), perfil `DEFAULT` → `https://dbc-1548c90f-c9ac.cloud.databricks.com` (OAuth con `databricks auth login`).
- **Modelos del workspace gratuito** (`databricks serving-endpoints list`):
  - chat: `databricks-gpt-oss-120b`, `-gpt-oss-20b`, `-meta-llama-3-3-70b-instruct`, `-meta-llama-3-1-8b-instruct`, `-llama-4-maverick`, `-qwen3-next-80b-a3b-instruct`, `-qwen35-122b-a10b`, `-deepseek-v4-flash-0731`, `-gemma-3-12b`;
  - embeddings: `-bge-large-en`, `-gte-large-en`, `-qwen3-embedding-0-6b`.
  - **No hay Claude ni GPT-5.x.**
- **Trampa de la ruta por defecto:** con `auth: {type: databricks, profile: DEFAULT}`, el harness `openai-agents` llama a `/ai-gateway/openai/v1`, que responde **403 "'databricks-…' is no longer available. Use Unity Catalog model services."**. El listado `/api/2.1/unity-catalog/model-services` está vacío en Free Edition. Los mismos endpoints sí funcionan en `/serving-endpoints/chat/completions`, con tool calling (probado en 6 modelos).
- **Solución:** un provider en `C:\Users\emili\.omnigent\config.yaml` (respaldo previo en `config.yaml.bak-20261003`), sin `default: true`:

  ```yaml
  providers:
    databricks-serving:
      kind: gateway
      openai:
        base_url: https://dbc-1548c90f-c9ac.cloud.databricks.com/serving-endpoints
        api_key_ref: env:DATABRICKS_TOKEN
        wire_api: chat
  ```

  En `omnigent.yaml`: `auth: {type: provider, name: databricks-serving}`.
  - `wire_api: chat` fuerza Chat Completions también en los sub-agentes, que **no heredan** `use_responses` del ancla `&executor`.
  - Definir `HARNESS_OPENAI_AGENTS_GATEWAY_BASE_URL` como variable de entorno **no** sirve: Omnigent limpia el entorno del harness.
- **Linux (verificado el 2026-10-03):** `~/.omnigent/config.yaml` con el mismo provider `databricks-serving`, `DATABRICKS_TOKEN` (PAT) en `.env` y `set -a; source .env; set +a; PYTHONPATH=agents omnigent run agents/discovery_director.yaml -p "…"`. En Linux no hacen falta `PYTHONUTF8` ni `omnigent server --background`: `run` levanta el servidor local solo (queda corriendo en `127.0.0.1:6767`).
- **Token:** `DATABRICKS_TOKEN` tiene que estar en el entorno del servidor y del `run`.
  - El token OAuth de `databricks auth token` caduca en ~1 h; para sesiones largas, usar un PAT.
  - `auth_command` (renovación automática) no sirve en Windows: Omnigent lo ejecuta con `sh -c`, y `sh` no está en el PATH (solo existe en `C:\Program Files\Git\usr\bin`).
- **Bug 1 (Omnigent 0.16 en Windows):** `omnigent run` sin servidor previo truena con `httpx.ConnectTimeout` en `_wait_for_server`. Esa función solo tolera `ConnectError`, y en Windows conectar a un puerto que aún no escucha tarda ~2 s. Arrancar antes `omnigent server --background` y usar `run … --server http://127.0.0.1:6767`.
- **Bug 2:** el túnel del host se cae en bucle con `'charmap' codec can't encode character '\u2713'`. Definir `PYTHONUTF8=1` en el servidor y en el `run`.
- **Las function tools se importan en el proceso del servidor** (`LocalToolInfo.runtime = SERVER`): `PYTHONPATH` debe estar en el entorno al arrancar `omnigent server`, no solo en el `run`.
- **Dependencias de las tools (auditoría del 2026-10-03, resuelta):**
  - El entorno de Omnigent **sí** tiene `python-dotenv`, `httpx`, `pydantic` y `yaml`. **No** tiene `supabase`, `sentence-transformers`, `torch` ni `pypdf`.
  - **Trampa:** desde la raíz del repo, la carpeta `supabase/` (migraciones) se importa como paquete de espacio de nombres. `find_spec("supabase")` da un falso positivo y aparece "cannot import name 'Client'". Revisar dependencias desde otro directorio.
  - **Causa real** del "function-type tool has no resolved callable": `analysis/db.py` importaba `supabase` al cargar, y `tools.py` importa `db`. Ahora `supabase` se importa dentro de `client()`. El spec completo (15 tools) y el del crítico cargan **sin stubs** y sin importar `supabase`, torch, sentence-transformers ni pypdf.
  - `supabase` sigue siendo necesaria **al ejecutar** las tools que persisten en Supabase. Instalarla en el entorno de Omnigent antes de correr el ciclo completo: `uv tool install --python 3.12 "omnigent[databricks]" --with supabase --force`.
  - torch y sentence-transformers solo los usa `search_evidence` (import diferido). pypdf solo lo usa `rag/ingest.py`, que no es una tool.
- **Crítico aislado:** `agents/scientific_critic.yaml` tiene solo dos tools de librería estándar (`commute_lab/critic_tools.py`):
  - `read_experiment_artifact` lee `reports/experiments/<id>/` y verifica `result.json` contra `validation.json`.
  - `save_scientific_critique` valida el contrato y rechaza: frases causales en la evidencia, cifras decimales ausentes en la vista del artefacto y referencias a otros `EXP-*`. Escribe `reports/discovery/local/critiques/CRIT-<id>-NNN.json` y nunca sobrescribe.
  - La vista compacta del resultado vive en `commute_lab/experiment_views.py`, que comparten `tools.py` y el crítico.
- **Primera corrida real (2026-10-03):** `CRIT-EXP-001-001`, con `databricks-gpt-oss-120b` en 32 s.
  - Estado `UNCERTAIN`. Reconoce sueño como la estimación puntual más negativa, `INCONCLUSIVE_RANKING`, diseño observacional sin lenguaje causal, CR1 ≠ varianza completa de ENUT y H3/H4 sin evaluar. No menciona EXP-002.
  - Las 21 cifras con decimales coinciden con el artefacto (verificación independiente).
  - Detalle de redacción: una INFERENCE dice "strongest negative association" sin "point estimate". La misma crítica aclara en `unsupported_claims` que no hay ranking definitivo.
- **Motor en Windows:** `.venv-experiments` creado con `uv venv -p 3.12` + `requirements-experiments.txt`; el validador da PASS. `tools.py` ahora usa por defecto `.venv-experiments/Scripts/python.exe` en Windows (y `bin/python` en el resto); `EXPERIMENT_PYTHON` sigue teniendo prioridad.
- **Bootstrap anterior con `OPENAI_API_KEY`:** la llave es válida, pero su organización **no tiene créditos** ("You have no credits remaining"). El harness `codex` descarta `OPENAI_API_KEY` y necesita la CLI `codex`, que no está instalada (la app de escritorio de Codex no la expone).

- **Hypothesis Agent (2026-10-04):** `agents/hypothesis_agent.yaml` con tres tools de librería estándar (`commute_lab/hypothesis_tools.py`):
  - `read_hypothesis_context`: entrega el resultado de EXP-001, la crítica, las 22 variables aprobadas, H1–H4 y el contrato del motor, leído del JSON Schema.
  - `validate_hypothesis`: validación en seco, sin guardar.
  - `save_hypothesis`: asigna `HYP-NNN` secuencial (contando también `superseded/`), no sobrescribe y permite máximo 4 hipótesis activas por crítica.
  - Los artefactos van en `reports/discovery/local/hypotheses/` (misma convención que las críticas), con estado `UNTESTED` y `REQUIRES_HUMAN_REVIEW`.
- **El validador rechaza:**
  - lenguaje causal (incluido "effect");
  - "strongest negative association" (se debe decir "point estimate");
  - afirmaciones vagas o sin comparación;
  - criterios de apoyo y refutación sin incertidumbre (se exige un intervalo que excluya o incluya el cero);
  - variables o nombres `snake_case` fuera del contrato;
  - variables que el experimento no estimó, presentadas como evidencia observada;
  - cifras, decimales o enteros, que no estén en las fuentes;
  - `known_executable: true` para interacciones, formas no lineales, variables fuera del schema o diferencias entre grupos;
  - otros `EXP-*`, frases que eligen la siguiente prueba y duplicados (Jaccard ≥ 0.6);
  - **hipótesis que no son nuevas**: deben agregar un subgrupo, una comparación entre grupos, una variable aprobada no usada o una forma funcional distinta.
- **Corridas reales** con `databricks-gpt-oss-120b`:
  - Primera corrida: HYP-001 a 003. Segunda: HYP-004 a 006.
  - Las dos pasaron el validador de ese momento, pero la revisión encontró huecos: criterios basados solo en estimaciones puntuales, "effect", `known_executable: true` en una diferencia entre grupos, y re-pruebas de coeficientes que EXP-001 ya estimó.
  - Después de cada revisión se endureció el validador y se archivaron esas hipótesis sin cambios en `hypotheses/superseded/` (con `README.md`). Sus IDs no se reutilizan. HYP-005, de la segunda corrida, sí era válida y sigue activa.
  - Tercera corrida: HYP-007 y 008.
  - **Activas:** HYP-005 (sueño, mujeres vs. hombres), HYP-007 (sueño, con vs. sin `has_child_u15`) y HYP-008 (ocio, por sexo). Las tres con `known_executable: null`. Esperan revisión humana; no van al Experiment Planner.
- **Trampa de escritura:** al parchear Python con heredocs, `\b` dentro de strings no-raw se escribió como el carácter de retroceso (0x08). Las regex no fallan; simplemente nunca coinciden. Parchear desde archivos `.py` y revisar que el archivo no tenga caracteres de control.
- ✅ **Bytes de EXP-001 en git (resuelto el 2026-10-04):** `main` (commit `2bd1fbf`) restauró los bytes CRLF certificados de `reports/experiments/EXP-001/result.json` (`5e4084a3…`) y `metadata/analytic_v1_manifest.json` (`f800513b…`). `feat/hypothesis-agent` los recibió al fusionar `main` (merge por fast-forward a `555ea10`). El crítico, el validador y las tools leen EXP-001 con bytes exactos.
  - Las hipótesis y propuestas generadas antes del arreglo guardaron el hash LF observado (`3113a9ee…`) como `sha256`. `hypotheses/PROVENANCE_NOTE.md` y `candidates/PROVENANCE_NOTE.md` aclaran cuál es el hash canónico; esos artefactos no se reescriben porque REV-001 certifica los bytes de las hipótesis.
  - Desde entonces, `hypothesis_tools` y `planner_tools` guardan `observed_sha256` y `certified_sha256` por separado (`_experiment_provenance`).

- **Revisión humana REV-001 (2026-10-04):** `reports/discovery/local/reviews/REV-001.json`. Aprueba HYP-005, HYP-007 y HYP-008 para la planificación, con 5 restricciones: las direcciones son hipótesis; la heterogeneidad exige inferir sobre la diferencia entre grupos; los subgrupos separados no bastan; el análisis es observacional; sin lenguaje causal. Es una transcripción literal del mensaje del usuario, marcada como tal y con los hashes de las hipótesis. El Planner rechaza cualquier hipótesis que haya cambiado después de la revisión.
- **Experiment Planner:** `agents/experiment_planner.yaml` con tres tools de librería estándar (`commute_lab/planner_tools.py`):
  - `read_planning_context`: entrega la revisión, las hipótesis aprobadas, la crítica, EXP-001, las variables y la **auditoría de capacidades**. La auditoría se deriva en cada llamada del JSON Schema y del registro de métodos: interacciones, comparación formal entre grupos, no linealidad y filtro por `has_child_u15` → **no soportados**; filtros por sexo, estado y edad → sí.
  - `validate_proposal` (en seco) y `save_proposal`, que escribe `reports/discovery/local/candidates/PROP-NNN.json` (el tipo `candidates` del Shared Research State; antes era `proposals/`, que el estado ignoraba) con `selected=false`, `experiment_id=null` y `REQUIRES_HUMAN_REVIEW`.
- **El validador de propuestas exige:**
  - que la factibilidad coincida con la auditoría;
  - que `FORMAL_HETEROGENEITY_TEST` liste `interaction_terms` o `formal_between_group_comparison`;
  - que `EXPLORATORY_SUBGROUP` declare que no establece heterogeneidad y no se compare contra el estimado global;
  - que la interacción incluya el término principal del moderador, declarando `covariates_outside_schema` si el moderador no está en el schema;
  - que "incluye el cero" sea inconcluso;
  - que en una hipótesis bidireccional el apoyo acepte ambos sentidos y la refutación sea por equivalencia, con un margen fijado por humanos;
  - que no repita EXP-001;
  - sin sobreafirmaciones ("definitive", "prove"), sin lenguaje causal ("main effect" sí está permitido), sin elegir ni asignar EXP-*, sin cifras inventadas y sin duplicados (mismas hipótesis y mismo outcome).
- **Corridas reales:** cinco, con `databricks-gpt-oss-120b`. PROP-001, 002, 004, 006 y 007 se archivaron en `candidates/superseded/` (con `README.md`); el validador de cada momento no había detectado sus fallas.
  - En la primera corrida el agente afirmó haber guardado PROP-003 sin llamar a `save_proposal`. **Siempre verificar en disco, nunca el resumen del agente.**
  - En la cuarta, el CLI de Omnigent terminó con "Turn did not complete within 120s" (subscribe-after-post race).
- **Activas:**
  - PROP-003: HYP-005, interacción traslado × sexo para sueño.
  - PROP-008: HYP-007, interacción × `has_child_u15`, que también requiere esa covariable fuera del schema.
  - PROP-009: HYP-008, interacción × sexo para ocio, bidireccional.
  - Las tres anteriores son `REQUIRES_ENGINE_EXTENSION`.
  - PROP-005: HYP-005, modelo exploratorio solo de mujeres, `EXECUTABLE_NOW`, declarado insuficiente para establecer heterogeneidad.
  - Esperan revisión humana. No se eligió ninguna ni se asignó EXP-002.

- **Extensión del motor: interacción con moderador binario (rama `feat/interaction-engine`, 2026-10-04):**
  - Campo opcional `interaction` en `ExperimentSpec`; resultados en `ExperimentResult.interactions`; capacidades en `metadata/experiment_engine_capabilities.json`, que el validador compara con `src/experiments/capabilities.py`.
  - Usa la misma WLS + CR1 que EXP-001. La pendiente del grupo de comparación sale de la covarianza completa. El moderador entra una sola vez, aunque también esté en las covariables. Los faltantes del moderador se excluyen y se cuentan, nunca se rellenan.
  - Validación: 29 tests del motor (13 sintéticos nuevos, sin resultados reales); validador PASS; EXP-001 sin diferencias no ambientales, ni siquiera de 1 bit; `analytic_v1` y el `result.json` de EXP-001 conservan sus hashes.
  - El auditor del Planner (sin cambios) detecta `interaction_terms = True` por el campo `interaction`. `formal_between_group_comparison` sigue en `False` en su auditoría, porque busca otros nombres de campo.
  - PROP-003, PROP-008 y PROP-009 traducidas a `ExperimentSpec` validan contra el esquema; no se ejecutaron. No hay EXP-002.

### Web: espina de descubrimiento (2026-10-03)
- `web/lib/discovery/collect.mjs` es JS plano (lo usan el servidor y `scripts/snapshot-discovery.mjs`); `model.ts` es puro y se puede probar con `node --input-type=module -e 'await import("./lib/discovery/model.ts")'` desde `web/`.
- Los lectores toleran los dos formatos de crítica (`critic_tools.py` local y `tools.py` con Supabase) y nombres alternativos en hipótesis/candidatos/decisiones. Un campo ausente se muestra como "Not stated in the artifact", nunca se rellena.
- Vínculos sin Supabase: candidato → experimento comparando el spec (sin `experiment_id`); selección → candidato por `proposal_id`; crítica → experimento por `experiment_id`. Una decisión actualizada solo cita `experiment_run_id` (UUID de Supabase), así que no se enlaza a un `EXP-NNN`.
- LIVE usa `DISCOVERY_REPO_ROOT` si está definida (por defecto, el padre de `web/`). Así se probó con un fixture sintético en el scratchpad.
- **Next 16 no permite dos `next dev` en el mismo directorio.** Para un segundo servidor: `npm run build && npx next start -p 3100`.
- Desde el merge de `main` (2026-10-04, commit `2bd1fbf`), `reports/experiments/EXP-001/result.json` conserva sus bytes CRLF certificados (`5e4084a3…`), así que el hash que muestra el inspector coincide con `validation.json` y con `research_state.json`.
- **Adaptador (2026-10-04, tarde):**
  - `snapshot-discovery.mjs` importa `model.ts` directamente: Node 24 quita los tipos, así que no hay paso de compilación. Usa `--no-warnings` para silenciar el aviso `MODULE_TYPELESS_PACKAGE_JSON`.
  - Opciones: `--root` y `--out`, que usa la prueba B con una copia temporal. Sale con 1 si `research_state.json` apunta a un archivo que falta o si un artefacto requerido está malformado.
  - `research_state.json` lista los specs en `reports/experiments/<id>/spec.json`, pero el collector lee la copia de `experiments/<id>/`. El chequeo acepta cualquiera de las dos.
  - El cambio de capacidad del motor **no tiene artefacto propio**: se deriva comparando `provenance.engine_capability_audit.supported` entre decisiones consecutivas.
    - DEC-001→002: `interaction_terms`.
    - DEC-002→003: `formal_between_group_comparison`.
    - **No hay review humano de esos cambios**, y la UI lo dice.
  - El estado de H1–H4 sale de la crítica (`hypothesis_assessments`), si no del motor (listas `supported/inconclusive_hypotheses`), y si no de `initial_state`. Las tarjetas HYP muestran el estado con el que se escribieron y la evaluación posterior aparte.
  - `StatusTag` muestra el código exacto. El tono lo pone `statusOf()` en el adaptador, así que los componentes no tienen literales de estado; la prueba A lo verifica.
  - Capturas headless de la página completa: escritorio unos 13.500 px y móvil unos 26.000 px de alto.
- **2026-10-04:**
  - Los chips de experimento ya no se repiten: `EXP-001 spec`, `EXP-001 result` y `EXP-001 validation`.
  - `compactResult` (`collect.mjs`) conserva `candidate_next_experiments` (pregunta + factibilidad), que la banda muestra como "Listed by the engine, not selected".
  - El bundle guarda en `commit` **el último commit que tocó los artefactos**, no HEAD (`git log -1 -- initial_state.json metadata experiments reports/experiments reports/discovery`). Así el bundle no cambia entre commits que no tocan ciencia, `npm run build` no ensucia el árbol y el enlace "GitHub at <commit>" apunta a un commit que contiene exactamente esos archivos. Si los artefactos son nuevos, hay que hacer push antes de desplegar para que el enlace no dé 404.
  - El reloj del replay se calcula con `HOLD` y `timeline()` en `DiscoveryView.tsx`, ya no con `CUES` fijos. La banda es un solo paso.
  - Las capturas headless con `chromium-browser --headless=new --screenshot` salen en blanco si la página hace scroll sola (`/?stage=N`). Usar una ventana alta (p. ej. `--window-size=1440,4300`) para que no necesite scroll.
  - El commit `ed888f1` incluyó por error la inyección de `live.js` (Impeccable live) en `web/app/layout.tsx`. Ya se quitó del árbol de trabajo.
- La cuenta de Gemini (`GEMINI_API_KEY`) tiene cuota 0 para `gemini-3-pro-image` y no hay `OPENAI_API_KEY`: no hay generación de imágenes. El build de diseño fue code-first aunque `.impeccable/config.json` guarda `comp`.
- **Trampas de la validación E2E (2026-10-04):**
  - `pkill -f "<patrón>"` también mata la shell que lo ejecuta si el patrón aparece en su propia línea de comandos (exit 144). Matar por PID (`ss -ltnp | grep :PUERTO`).
  - Para probar un agente sin tocar artefactos canónicos: `git clone` local en scratch y `PYTHONPATH=<clon>/agents` (las tools derivan `ROOT` de la ruta del módulo). Una copia con `git archive` sin `data/` ni historial hace que `read_experiment_artifact` rechace la procedencia (correcto, pero inútil para la prueba). Detener antes cualquier `omnigent server` previo: importa las tools con el `PYTHONPATH` con el que arrancó.
  - `omnigent run … -p "…" < /dev/null` corre un turno y termina; el transcript está en `GET http://127.0.0.1:6767/v1/sessions/<id>/items` y las llamadas HTTP en `~/.omnigent/logs/runner/`.
  - En esta máquina Linux, `~/.omnigent/config.yaml` (provider `databricks-serving`) se creó el 2026-10-04; `DATABRICKS_TOKEN` (PAT) está en `.env`.
  - **Vercel empaqueta las rutas literales que lee el servidor**: con `existsSync(path.join(root, "initial_state.json"))` el trazado de archivos metió en la función los artefactos commiteados, y `/?mode=live` en producción se rotulaba "reports/ on this machine". Por eso `load.ts` desactiva LIVE si existe `process.env.VERCEL`. Probar en local con `VERCEL=1 npx next start`.

### Vercel
- Cuenta Hobby. El proyecto `commute-time-lab` está en el scope `roger-1592` (`team_37NrEuZAkgRsRYTKpMCwC5j9`).
  - El MCP de Vercel da **403 si se pasa `teamId`**. Funciona sin `teamId` (usa el scope por defecto).
- **Desde el 2026-10-04 se despliega desde GitHub**, sin subir archivos: `create_deployment` del MCP con `gitSource: {type: "github", org: "RogelioZu", repo: "Hack-nation-hackathon", ref: "main"}`, `projectSettings: {rootDirectory: "web", framework: "nextjs"}`, `target: "production"` y `skipAutoDetectionConfirmation: "1"`. Tarda unos 40 s. El `prebuild` regenera el bundle o conserva el commiteado; el contenido es el mismo.
- Antes: despliegue por API con archivos inline (no hay CLI de Vercel). Se suben solo los fuentes de `web/`, **sin `package-lock.json`** (240 KB), así que Vercel resuelve versiones desde `package.json`. Para redeployar: `create_deployment` con los archivos, o conectar el repo de GitHub.
- Variables en el proyecto (production, preview y development): `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- `https://commute-time-lab.vercel.app` es público. Los alias por deployment y `…-roger-1592.vercel.app` piden login de Vercel (SSO protection por defecto).

## 6. Preferencias del usuario

- **Idioma:** documentación y conversación en español. UI web, demo y textos guardados en Supabase en inglés (ver `AGENTS.md` §0).
- **Commits:** mensaje breve en inglés y **sin créditos de coautoría** (ver `AGENTS.md`, "Para los commits").
- **El pipeline de datos está cerrado.** No reconstruirlo, no reinterpretar los datos crudos, no modificar `analytic_v1.parquet` y no volver a limpiar datos salvo que una validación científica explícita falle.
- `analytic_v1` y sus metadatos están **versionados en git** para que Omnigent y el motor los consuman directamente. El ZIP bruto (`data/raw/`) sigue fuera de git y Supabase sigue sin filas individuales.
- Prioridad: **el ciclo de descubrimiento antes que la UI**. No programar EXP-001 → EXP-002 → EXP-003 fijo; la evidencia debe poder cambiar la siguiente decisión.

## 7. Próximos pasos

1. **Siguiente paso del ciclo:**
   - EXP-002 ya se ejecutó y CRIT-EXP-002-002 dejó H3 en `INCONCLUSIVE`.
   - Según `research_state.json` (`next_action`), lo siguiente es el `hypothesis_agent` con CRIT-EXP-002-002 como entrada.
   - Siguen pendientes de revisión humana EXP-001 y EXP-002.
   - No elegir EXP-003 a mano.
   - Para el ciclo completo: `--with supabase`, un PAT en `DATABRICKS_TOKEN` y la receta de §5.
   - Después de cada artefacto nuevo: `python scripts/build_research_state.py && (cd web && npm run snapshot)`.
2. Probar `search_web` con `BRIGHTDATA_API_TOKEN` + `BRIGHTDATA_SERP_ZONE` reales.
3. Panel web: ✅ la espina (`/`) ya muestra críticas, hipótesis, candidatos, selección, nueva evidencia y decisión desde los JSON de `reports/discovery/`. Cada vez que se commiteen artefactos nuevos: `cd web && npm run snapshot` (o `npm run build`, que lo corre en `prebuild`) y commitear `web/data/discovery-run.json`; si no, el REPLAY de Vercel no los muestra. Verificar con `npm run test:discovery`.
4. Borrar `audit/` y `metadata/provenance.json` (§5).
5. Confirmar con el equipo si el track exige Omnigent administrado por Databricks; hoy el executor usa Databricks Free Edition desde Omnigent de código abierto.
6. RAG: si el eval o el uso real lo piden, agregar reranker multilingüe o filtro por `source_kind` (ver §3).
7. Decidir sobre `rls_auto_enable()` (ver §2).
8. Redeployar la web cuando cambie `web/` (receta en §5, "Vercel"). La versión publicada es `main` @ `948229a` (deploy `dpl_9o8aEaf49e7JiYrYcZ4DSkuN3Q2C`).
