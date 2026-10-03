# AGENTS.md — Commute & Time Lab (Hack Nation × Databricks · Agentic Scientific Discovery)

> **Nota para asistentes de IA (Claude, Codex, Cursor, Copilot, etc.):** este documento es la **fuente única de verdad** para la arquitectura de agentes, el flujo de datos, las reglas científicas y las convenciones del repo.

`CONTEXT.md` es la especificación original (larga); este archivo es su versión operativa. Si se contradicen, **gana este archivo**. Para el significado de variables, población y métodos estadísticos, **ganan los documentos de `docs/`** (`DATA_CONTRACT.md`, `SCIENTIFIC_PROTOCOL.md`, `EXPERIMENT_PROTOCOL.md`, `EXPERIMENT_ENGINE.md`). Si alguno contradice el diccionario de datos ENUT, los microdatos o la documentación oficial, **ganan los datos**: corregir el supuesto aquí y registrarlo en el [Registro de decisiones](#registro-de-decisiones).

**Presupuesto: 10 horas en total.**

> 📌 **Antes de tocar nada, lee [`MEMORY.md`](MEMORY.md).** Tiene el estado real del proyecto (qué está aplicado en Supabase, qué está pendiente), las decisiones ya tomadas y las trampas técnicas encontradas. Si cambias el estado, actualízalo en el mismo commit.

## 0. Idioma

| Qué | Idioma |
|---|---|
| Documentación (`*.md`, registro de decisiones, políticas de agentes) | **Español** |
| Conversación con el equipo en sesiones de agentes (Claude Code, Codex, etc.) | **Español** |
| Interfaz de la app web (`web/`: textos, etiquetas, mensajes) y demo | **Inglés** |
| `README.md` público, prompts de sistema de los agentes en `omnigent.yaml` y textos que los agentes guardan en Supabase | **Inglés** |
| Código: identificadores, nombres de tablas/columnas, campos del JSON de estado, protocolos | Inglés |

---

## 1. Misión

Construir un MVP web en el que **Omnigent orquesta en vivo agentes especialistas** para investigar una pregunta científica con microdatos reales de la **ENUT 2024** (Encuesta Nacional sobre Uso del Tiempo, INEGI). Nombre del proyecto en los prompts: **Time Poverty Lab**.

> Entre trabajadores de 18 a 65 años que residen en Ciudad de México (CDMX) y Estado de México (Edomex), ¿qué dimensión del tiempo personal muestra la asociación negativa más fuerte con **5 horas adicionales de traslado laboral entre semana** (`commute_5h`: 1 unidad = 300 minutos más de lunes a viernes)? ¿Difiere la asociación por sexo o por la presencia de menores en el hogar?

Las cuatro dimensiones canónicas son sueño, higiene personal exclusiva, conversación exclusiva con integrantes del hogar y ocio (definiciones en [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md)). Los cuidados a integrantes del hogar **ya no** son un resultado del dataset aprobado.

**Fase actual (desde 2026-10-03): capa agéntica de descubrimiento.** La capa de datos (`analytic_v1`) y el motor determinista de experimentos (`src/experiments/`) ya existen y están validados. EXP-001 ya se ejecutó. Ahora toca construir el ciclo en el que la evidencia de un experimento **cambia** la siguiente decisión científica:

```
pregunta → evidencia (RAG, con citas) → hipótesis → pruebas candidatas (≥2) → Experiment Planner
        → orquestación Omnigent → ExperimentSpec → ExperimentRunner (determinista) → ExperimentResult
        → Scientific Critic → estado científico actualizado → siguiente experimento (vuelve al ciclo)
```

- **No** se programa una secuencia fija EXP-001 → EXP-002 → EXP-003. EXP-002 no está elegido: lo decide el sistema a partir de la evidencia (ver §7.5).
- El motor produce evidencia; los agentes LLM la interpretan y deciden qué investigar. **Ningún agente calcula ni inventa cifras.**

No ampliar a otras ciencias, mapas de rutas, recomendaciones de transporte, modelos causales, cuentas de usuario ni múltiples datasets. No pulir la UI antes de que funcione el ciclo.

## 2. Reglas científicas innegociables

- ENUT es **observacional y transversal**: decir "se asocia con", nunca "causa", "reduce", "sacrifica" ni "provoca". Toda conclusión es una asociación observacional.
- **Unidades:** todos los tiempos son **minutos totales de lunes a viernes** en la semana de referencia, no promedios diarios ni minutos semanales de 7 días. `commute_5h` = `commute_weekday_min / 300`. Nunca llamar "una hora diaria" a 300 minutos de la semana laboral.
- La cobertura estatal (CDMX + Edomex) **no** es una muestra representativa de la Zona Metropolitana del Valle de México. No afirmarlo.
- **No inventar cifras, variables ni citas.** Las cifras salen solo del motor determinista (`src/experiments/`, §7.4). Las afirmaciones factuales salen solo de pasajes RAG con `source_id` / `passage_id` / URL, o de registros de OpenAlex con DOI.
- **Variables canónicas:** su significado está en [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md). No redefinirlas, no crear variables derivadas sin documentar y no cambiar la población analítica en silencio.
- **Nunca modificar `analytic_v1.parquet`** ni volver a correr la limpieza de datos, salvo que una validación científica explícita falle. Una versión nueva es un archivo nuevo (`analytic_v2…`).
- **No ocultar la incertidumbre ni subir la fuerza de la evidencia.** Si la evidencia es inconclusa, se reporta como inconclusa. Si el crítico la juzga insuficiente, la siguiente acción correcta puede ser un experimento de validación, no una conclusión más fuerte.
- **Varianza aproximada:** el motor usa FAC_PER con errores agrupados por UPM (CR1). **No** es una reconstrucción completa de la varianza de encuesta compleja de ENUT (sin centrado por estrato, FPC ni réplicas). Toda salida debe conservar esa limitación. No llamarlo `svyglm` ni "varianza ajustada por diseño".
- **No elegir un experimento porque se espera que salga significativo.** Se elige el que maximiza el aprendizaje científico esperado.
- Las hipótesis generadas por agentes se **etiquetan** (`hypotheses.generated_by`) y separan tres cosas: evidencia existente, inferencia e hipótesis nueva.
- Reportar siempre `n` antes y después de exclusiones, faltantes, método de incertidumbre y qué elementos del diseño muestral se usaron (`weight` = FAC_PER, `cluster` = UPM_DIS, `stratum` = EST_DIS).
- No forzar que las actividades sumen 24 h/día (ENUT capta actividades simultáneas). No eliminar, recortar ni winsorizar valores extremos.
- **Reglas de decisión pre-registradas** en `projects.decision_rules` *antes* de ver resultados. Son guías del crítico y del Director, no una secuencia fija; las ramas completas están en [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md) ("Branching Rules"):
  - **R1**: hay diferencia por sexo suficientemente sustentada y los subgrupos tienen tamaño adecuado → probar composición del hogar / presencia de menores.
  - **R2**: no aparece diferencia por sexo → sensibilidad a traslados largos / relación no lineal.
  - **R3**: la calidad o el tamaño de muestra impiden concluir → revisar variables, cohorte y medición.
- No declarar aceleraciones (p. ej. "10×") sin medirlas. El 10× del `README.md` es una **meta**, no un resultado. Cronometrar una línea base manual con el mismo corpus y dataset.

## 3. Requisitos del track y evaluación

Hack-Nation 7th Global AI Hackathon, Challenge 03. Omnigent es **obligatorio** (administrado por Databricks o de código abierto). Debe coordinar el flujo real, los traspasos, el uso de herramientas y el cambio de plan tras el resultado. Ponderación: orquestación Omnigent 30 % · potencial científico 25 % · aceleración y aprendizaje 20 % · rigor 15 % · creatividad y responsabilidad 10 %.

Entregables: repositorio, configuraciones y políticas de agentes, código y resultados del experimento, evidencia citada, mejora medida, siguiente experimento y un **demo de 2 minutos**.

## 4. Stack y estructura

| Área | Elección |
|---|---|
| Orquestación | Omnigent 0.16 con `omnigent.yaml` (7 agentes) + estado inicial `initial_state.json` |
| Herramientas de agentes | Python, paquete `commute_lab` en `agents/commute_lab/` (tools + policies) |
| Backend / estado persistente | Supabase Postgres + **pgvector**, RLS, migraciones SQL versionadas → `supabase/` |
| RAG | Python 3.12 con **uv** → `analysis/` |
| Motor de experimentos | Python ≥ 3.11, pandas + pyarrow + numpy + scipy + pydantic (tests: statsmodels) → `src/experiments/` |
| Web | Next.js 16 App Router + TypeScript + Tailwind 4 → `web/` (despliegue en Vercel) |
| Embeddings | `intfloat/multilingual-e5-small`, 384 dimensiones, CPU |
| LLM de los agentes | Harness `claude-sdk` con `databricks-claude-sonnet-4-6`, auth `databricks` y perfil `DEFAULT` (verificar el endpoint, ver [Decisiones abiertas](#decisiones-abiertas)) |
| Web desplegada | Vercel, proyecto `commute-time-lab` → https://commute-time-lab.vercel.app |

```
AGENTS.md / CLAUDE.md      este archivo (CLAUDE.md lo importa junto con MEMORY.md)
MEMORY.md                  estado actual, decisiones y trampas; leer antes de tocar nada
CONTEXT.md                 especificación original (larga)
README.md                  presentación pública del proyecto (inglés)
omnigent.yaml              spec Omnigent: Discovery Director (raíz) + 6 sub-agentes, tools y políticas
initial_state.json         Shared Research State vacío con el que arranca la sesión
.env.example               SOLO nombres de variables; copiar a .env (raíz) y web/.env.local
supabase/
  config.toml
  migrations/              *_extensions, *_core, *_rag, *_rls  (nunca editar una ya aplicada; crear archivo nuevo)
  seed.sql                 estado DEMO de relleno (is_demo = true, run 'pending', sin resultados)
analysis/
  pyproject.toml           proyecto uv (torch CPU)
  db.py                    cliente Supabase con service_role (lee el .env de la raíz)
  rag/embed.py             embeddings e5 con prefijos "passage: " / "query: "
  rag/ingest.py            manifiesto → descarga → limpieza → fragmentos (sección + localizador) → embeddings → upsert
  rag/search.py            search_evidence() → RPC hybrid_search (expande términos inglés → español)
  rag/corpus.json          manifiesto del corpus: cuestionario, diseño conceptual y diseño muestral ENUT 2024
  rag/eval.py              QA de recuperación (hit@1, hit@5, MRR, ruido) sobre rag/eval_queries.json
  enut/README.md           nota histórica; el pipeline ENUT se construyó fuera de este repo (ver §8)
data/
  raw/                     ZIP bruto de INEGI (ignorado por git)
  processed/               analytic_v1.parquet (dataset canónico; ⚠️ aún NO está en el repo, ver MEMORY.md §1)
                           y staging_v1.parquet (staging histórico de la fase 2A; el motor no lo lee)
metadata/
  analytic_v1_manifest.json          procedencia, linaje por columna, hashes, faltantes, validaciones
  experiment_contract.schema.json    JSON Schema de ExperimentSpec y ExperimentResult
docs/
  DATA_CONTRACT.md         definiciones canónicas de variables y población (FUENTE DE VERDAD de las variables)
  SCIENTIFIC_PROTOCOL.md   decisiones científicas aprobadas por fase (2A, 2B)
  EXPERIMENT_PROTOCOL.md   ciclo de descubrimiento, hipótesis H1–H4, ramas, crítico, aprobación humana
  EXPERIMENT_ENGINE.md     contrato del motor: método, varianza CR1, ranking, sensibilidad, reproducción
src/experiments/           motor determinista (sin LLM): run_experiment(ExperimentSpec) -> ExperimentResult
  schemas.py               modelos Pydantic estrictos (rechazan campos, variables y métodos desconocidos)
  runner.py                carga y verifica analytic_v1, filtra población, ajusta, ranking, sensibilidad, procedencia
  methods/                 registro cerrado de métodos: solo weighted_linear_regression
  models.py                ExperimentError y utilidades
experiments/EXP-001/       spec.json (+ copia de result.json)
reports/experiments/EXP-001/  result.json, summary.md (en español), validation.json
tests/                     test_experiment_schemas.py, test_experiment_runner.py, test_exp001.py
agents/
  commute_lab/tools.py     11 tools que persisten en Supabase (create_project … record_decision)
  commute_lab/policies.py  ask_before_run: pide aprobación humana para run_experiment y record_decision
web/
  lib/supabase.ts          cliente de solo lectura (clave publishable, solo servidor)
  lib/data.ts              getProjects(), getResearch(id)
  lib/types.ts             tipos de filas + contrato de resultados
  app/page.tsx             portada + lista de casos de investigación
  app/research/[id]/       panel del ciclo completo (consulta cada 5 s)
  AGENTS.md                aviso autogenerado de Next.js 16: leer node_modules/next/dist/docs antes de escribir código Next
```

## 5. Modelo de datos (Supabase, esquema `public`)

Todas las PK son `uuid`. Las tablas hijas se borran en cascada con `projects`. Los agentes intercambian **IDs**, no prosa.

| Tabla | Propósito | Campos clave |
|---|---|---|
| `projects` | Un caso de investigación | `question`, `cohort_definition`, `decision_rules jsonb [{id,if,then}]`, `status` (draft·evidence·planning·running·critique·decided·archived), `omnigent_session_url`, `is_demo` |
| `sources` | Documentos citables | `kind` (official_doc·questionnaire·data_dictionary·sampling_design·paper·report·internal), `title`, `url` (única), `doi`, `publisher`, `year`, `license` |
| `passages` | Fragmentos RAG | `source_id`, `section` (ruta de marcadores del PDF o `Sección V… › Pregunta 5.9`), `locator` (único por fuente, p. ej. `p. 12` o `p. 12 · 5.9`), `content`, `embedding vector(384)`, `fts` (generada, configuración `public.es_unaccent`: español + unaccent) |
| `hypotheses` | Afirmaciones a probar | `statement`, `generated_by`, `status` (proposed·testing·supported·not_supported·inconclusive·superseded), `supporting_passage_ids[]`, `opposing_passage_ids[]` |
| `experiment_proposals` | ≥2 pruebas candidatas | `label` (A/B), `title`, `protocol` (clave cerrada), `learning_value`, `feasibility`, `cost`, `selected`, `selection_rationale` |
| `experiment_runs` | Ejecuciones reproducibles | `proposal_id`, `protocol`, `dataset_hash`, `code_version`, `parameters`, `sample_sizes`, `results` (contrato abajo), `artifact_paths`, `status` (pending·running·succeeded·failed), `error` |
| `decisions` | Crítica → siguiente paso | `experiment_run_id`, `interpretation`, `uncertainty`, `limitations`, `rule_applied` (R1/R2/R3), `next_test`, `rationale`, `decided_by` |
| `agent_events` | Línea de tiempo / auditoría | `session_id`, `agent_name`, `event_type` (started·tool_call·handoff·output·decision·approval·error·note), `summary`, `input_refs`, `output_refs`, `occurred_at` |

**RLS:** activo en todas las tablas. `anon` y `authenticated` tienen solo SELECT. No hay políticas de escritura, así que solo `service_role` escribe (host Python, herramientas de Omnigent, Route Handlers protegidos de Next). **Nunca guardar filas individuales de microdatos en Supabase.** Solo agregados y procedencia.

### Contrato de resultados (`experiment_runs.results`)

> ⚠️ **Desfasado respecto al motor.** El resultado canónico ahora es `ExperimentResult` (`src/experiments/schemas.py`, `metadata/experiment_contract.schema.json`). Tiene estimaciones por modelo (`adjusted`, `unadjusted`, sensibilidad), intervalos puntuales y Bonferroni, `ranking`, diagnósticos, limitaciones y procedencia. **Pendiente:** decidir cómo se guarda en Supabase (el `ExperimentResult` completo en `results`, o un resumen + `artifact_paths` hacia `reports/experiments/<id>/`) y adaptar `web/lib/types.ts`. Hasta entonces, la forma de abajo es la que dibuja la web.

La web dibuja esta forma (ver `web/lib/types.ts`). Los textos de `label`, `method`, `units` y `notes` van **en inglés**, porque se muestran en la web:

```json
{
  "label": "exploratory",
  "method": "WLS: activity_min ~ commute_hours * sex + age + work_hours + state, weights FAC_PER",
  "units": "Weekly minutes associated with +60 weekly commute minutes",
  "uncertainty_method": "Cluster-robust SE by UPM_DIS; strata EST_DIS not incorporated",
  "estimates": [
    {"activity": "sleep", "sex": "women", "estimate": -0.0, "ci_low": -0.0, "ci_high": 0.0, "n": 0}
  ],
  "notes": ["n before/after exclusions …", "missing share …"]
}
```

`sample_sizes` es un mapa plano `{etiqueta: n}`, por ejemplo `{"cohort_before_exclusions": …, "women": …, "men": …}`. Los números de arriba son de relleno. Nunca copiarlos.

## 6. Contrato RAG

- Modelo: `intfloat/multilingual-e5-small`, normalizado. Se ingiere como `"passage: …"` y se consulta como `"query: …"`. **Usar el mismo modelo en ingesta y consulta.** Cambiarlo obliga a re-embeber todo y a cambiar `vector(384)`.
- Recuperación: `public.hybrid_search(query_text, query_embedding, match_count=5, full_text_weight=1, semantic_weight=1, rrf_k=50)`. Combina texto completo y coseno (HNSW) con Reciprocal Rank Fusion. El texto completo usa la configuración `public.es_unaccent` (stemming español + sin acentos), acepta coincidencias **parciales** (OR) y ordena primero por cuántos términos distintos de la consulta contiene el pasaje y luego por `ts_rank_cd`. Devuelve `passage_id, source_id, source_title, source_kind, url, doi, section, locator, content, score`.
- Punto de entrada en Python: `rag.search.search_evidence(query, k=5) -> list[EvidenceHit]`. El corpus está en español, así que **consultar en español**. Los términos de dominio en inglés (commute, sleep, care, weights…) se expanden a su equivalente en español (`GLOSSARY` en `rag/search.py`), pero es un respaldo, no un sustituto.
- Corpus deliberadamente pequeño: cuestionario ENUT 2024 (un pasaje por pregunta numerada), diseño conceptual (sin portada, índice, anexo del cuestionario ni referencias) y diseño muestral, más 10–20 papers pertinentes de OpenAlex (los encuentra `search_openalex` del Literature Agent). Guardar texto completo **solo si la licencia lo permite**. Si no, guardar título + resumen.
- Limpieza en la ingesta: se quitan encabezados/pies repetidos, números de página, instrucciones al entrevistador ("REGISTRE…", "CIRCULE…") y guías de puntos (`Sí ....... 1` → `Sí = 1`). Las reglas de salto ("PASE A", "FILTRO") **se conservan**: explican faltantes estructurales.
- El RAG fundamenta conceptos, literatura y decisiones de método. **Nunca produce cifras de resultados.**
- Control de calidad: `uv run python -m rag.eval` (15 consultas fijas, 5 en inglés; criterio por texto esperado, no por id) antes y después de cualquier cambio de ingesta o búsqueda. Además, revisar a mano 10 afirmaciones factuales del panel.

## 7. Arquitectura de agentes (Omnigent)

Arquitectura definida por el equipo en `omnigent.yaml` (commits `bda27fc` y `b9e6e74`).

> **Estado (2026-10-03):** §7.1–7.3 describen lo que está implementado en `omnigent.yaml` y `agents/commute_lab/`, que todavía es anterior al motor de experimentos. §7.4 y §7.5 describen el **objetivo de la fase actual**. Donde chocan, gana el objetivo: hay que adaptar el código y los prompts.

### 7.1 Restricción central: el Shared Research State

Los agentes **NO** se comunican por chat de texto libre. Se comunican **exclusivamente** recibiendo, modificando y devolviendo **un único objeto JSON**: el *Shared Research State*. El prompt de sistema de cada especialista obliga a que su salida sea estrictamente ese objeto JSON, sin markdown ni texto conversacional. Omnigent no tiene una política `enforce_json_output`; la regla vive en los prompts.

Esquema actual (`initial_state.json`):

```json
{
  "project_id": "String (uuid en Supabase; lo llena el Director con create_project)",
  "research_question": "String",
  "population": "Object",
  "hypotheses": [
    { "id": "String", "claim": "String", "status": "untested | tested" }
  ],
  "evidence": ["Array of evidence cards"],
  "variables": "Object mapping concepts to data columns",
  "experiments": [
    { "id": "String", "hypothesis_id": "String", "method": "String", "status": "String" }
  ],
  "results": ["Array of metrics and artifacts"],
  "limitations": ["Array of strings"],
  "next_decision": { "experiment": "String", "reason": "String" }
}
```

### 7.2 Los 7 agentes

Omnigent gestiona el enrutamiento. Cada agente es dueño de **una decisión científica**:

| # | Agente (`name`) | Decisión científica | Entrada | Salida en el estado | Herramientas (`commute_lab.tools`) | Persistencia en Supabase |
|---|---|---|---|---|---|---|
| 1 | Literature Agent (`literature_agent`) | Qué evidencia previa existe | `research_question` | `evidence[]` (tarjetas + citas) | `search_evidence` (RAG INEGI), `search_openalex` | `sources` (los papers de OpenAlex se registran como `paper`), `passages` |
| 2 | Hypothesis Agent (`hypothesis_agent`) | Qué explicación falsable probar | `evidence` | `hypotheses[]` ordenadas | `save_hypothesis` | `hypotheses` |
| 3 | Data Steward (`data_steward`) | Si los datos permiten probarla | hipótesis líder | `variables`, `population` y `limitations` (reporte de calidad) | `describe_dataset`, `search_evidence` | Va en el estado JSON; los nombres de columna salen del contrato del dataset analítico |
| 4 | Experiment Planner (`experiment_planner`) | Qué prueba maximiza el aprendizaje | hipótesis + datos | `experiments[]` (status `planned`) | `save_proposals` (exige ≥2 y protocolos cerrados) | `experiment_proposals`, una `selected` con `selection_rationale` |
| 5 | Experiment Runner (`experiment_runner`) | Ejecutar la prueba de forma reproducible | especificación del experimento | `results[]`; experimento `completed`/`failed` | `run_experiment` (requiere aprobación), `read_run` | `experiment_runs` |
| 6 | Scientific Critic (`scientific_critic`) | Si la interpretación es confiable | `results` | `limitations[]` + regla aplicada | `read_run`, `record_decision` (requiere aprobación) | `decisions`, estado de `hypotheses` |
| 7 | Discovery Director (raíz del spec) | Qué investigar después | estado completo | `project_id`, `next_decision` | `create_project`, `set_project_status`, `log_event` + los 6 sub-agentes | `projects`, `agent_events` |

Todas las tools escriben una fila en `agent_events`, que la web muestra como línea de tiempo.

**Orquestación en `omnigent.yaml`.** El Discovery Director es el agente raíz. Los otros 6 son sub-agentes (`type: agent`) que el Director invoca en orden; cada uno hereda (`inherit`) solo sus tools. Después del crítico, el Director puede repetir **una vez** planner → runner → critic si `next_decision` propone una prueba factible (máximo 2 experimentos por sesión):

```
Director → literature_agent → hypothesis_agent → data_steward → experiment_planner
        → experiment_runner → scientific_critic → Director (next_decision)
        └─(si aplica, una vez)→ experiment_planner → experiment_runner → scientific_critic → Director
```

### 7.3 Cómo se conecta el estado JSON con Supabase

El **JSON es el contrato de mensajes** entre agentes durante la sesión. **Supabase es el registro persistente** que lee la web y que sirve de auditoría. Cada agente persiste su sección mediante herramientas Python (service_role) y registra una fila en `agent_events`; el JSON viaja con los IDs resultantes.

| Campo del estado | Tabla / columna | Nota |
|---|---|---|
| `research_question` | `projects.question` | Fijada al crear el proyecto |
| `population` | `projects.cohort_definition` | El Data Steward la confirma contra el diccionario |
| `evidence[]` | `sources` + `passages` | Cada tarjeta debe llevar `source_id`, `passage_id` (o DOI), `url`, `locator` y la cita textual |
| `hypotheses[]` | `hypotheses` | `claim` → `statement`; `untested` → `proposed`; `tested` → `supported`·`not_supported`·`inconclusive` |
| `variables` | `experiment_runs.parameters.variables` | El runner los pasa como parámetros del protocolo |
| `experiments[]` | `experiment_proposals` + `experiment_runs` | El planner propone ≥2; el runner crea el run de la elegida |
| `results[]` | `experiment_runs.results` | Debe cumplir el [contrato de resultados](#contrato-de-resultados-experiment_runsresults) |
| `limitations[]` | `decisions.limitations` | También el reporte de calidad del Data Steward |
| `next_decision` | `decisions.next_test` / `rationale` / `rule_applied` | Debe citar el `experiment_run_id` real y la regla R1–R3 aplicada |

**Extensiones aplicadas al esquema JSON** (aditivas):
- `project_id` en `initial_state.json`.
- Las reglas R1–R3 se guardan en `projects.decision_rules` al llamar a `create_project`.
- `experiments[]` lleva además `protocol`, `learning_value`, `feasibility`, `cost`, `selected` y `selection_rationale`.
- `evidence[]` lleva `claim`, `stance`, `source_id`, `passage_id` o `doi`, `url`, `locator` y `quote`.
- `next_decision` lleva además `rule_applied` y `run_id`.

Los prompts de `omnigent.yaml` definen estas formas.

### 7.4 Reglas de los agentes

**El motor determinista es el único camino computacional aprobado** para experimentos sobre `analytic_v1`:

```
ExperimentSpec  →  src.experiments.runner.run_experiment(spec)  →  ExperimentResult
```

- Los agentes piden experimentos **construyendo un `ExperimentSpec` válido** (ejemplo: `experiments/EXP-001/spec.json`). No calculan coeficientes con el LLM, no inventan estadísticas, no modifican `analytic_v1`, no saltan la validación del esquema y no crean variables derivadas sin documentar. **Ningún agente tiene SQL ni shell arbitrario sobre los datos.**
- El esquema es estricto y rechaza lo desconocido. Lo que acepta **hoy** (`src/experiments/schemas.py`):

  | Campo | Valores permitidos |
  |---|---|
  | `dataset_version` | `analytic_v1` |
  | `population` | `source = approved_analytic_v1`; `states` ⊆ {`09`, `15`}; `age_min`/`age_max` dentro de 18–65; `sexes` ⊆ {`male`, `female`}; `expected_n` opcional |
  | `exposure` | `commute_5h` |
  | `outcomes` | los 4 canónicos: `sleep_weekday_min`, `personal_hygiene_weekday_min`, `household_conversation_weekday_min`, `leisure_weekday_min` |
  | `covariates` | `work_weekday_min`, `age`, `sex`, `state` |
  | `method` | `weighted_linear_regression` (registro cerrado en `methods/__init__.py`) |
  | `hypothesis_ids` | `H1`, `H2` |
  | `sensitivity_analyses` | `exclude_zero_weekday_work` |
  | `uncertainty` / `confidence_level` | `psu_cluster_CR1_t` / `0.95` |

- **Consecuencia para la planeación:** con el contrato actual sí se puede estimar el mismo modelo **por separado en subpoblaciones** (por sexo, estado o rango de edad) cambiando `population`. **No** se pueden pedir interacciones (Commute × Sex), términos no lineales, splines, categorías de traslado, modelos de dos partes, `has_child_u15`/`has_minor_u18` como covariables ni las hipótesis H3/H4. Para eso hay que **revisar el contrato** (esquema + método + tests + `docs/EXPERIMENT_ENGINE.md`) y pasar por aprobación humana. El Planner debe declarar esa factibilidad en cada candidato; un candidato que exija revisión del contrato no se ejecuta sin ella.
- El motor verifica el SHA256 del parquet antes y después, corre cada spec dos veces y exige resultados idénticos. Escribe `result.json`, `summary.md`, `spec.json` y `validation.json` en `reports/experiments/<id>/`. Los fallos lanzan `ExperimentError` con código y mensaje; nunca devuelve un resultado exitoso parcial.
- `ExperimentResult.review_status` siempre es `REQUIRES_HUMAN_REVIEW`. `EXPERIMENT_COMPLETED` es un estado técnico, no una aprobación científica.
- **Brecha actual:** la tool `run_experiment` de `agents/commute_lab/tools.py` todavía espera protocolos cerrados en `analysis/enut/protocols.py` (`weighted_means_by_group`, `wls_commute_by_sex`), que **nunca se implementaron y quedan reemplazados por el motor**. Hay que reescribir la tool para que reciba un `ExperimentSpec`, llame a `src.experiments.runner.run_experiment` y persista el resultado y su procedencia en `experiment_runs`. Lo mismo `save_proposals`, que valida contra esa lista vieja.
- `describe_dataset` lee archivos hermanos `data/processed/analytic_v1.*`. El contrato y el manifiesto ahora están en `docs/DATA_CONTRACT.md` y `metadata/analytic_v1_manifest.json`: hay que apuntarla ahí. **Nunca devuelve filas.**
- Cada llamada a herramienta escribe una fila en `agent_events`. La política `commute_lab.policies.ask_before_run` devuelve **ASK** (aprobación humana) antes de `run_experiment` y de `record_decision`. Hay además un tope de 150 llamadas por sesión.
- Los textos que los agentes guardan (en el JSON y en Supabase) van **en inglés**, porque los muestra la web.
- La sesión se inicia desde Omnigent y se guarda `projects.omnigent_session_url`. Un botón "Start research" (Route Handler del servidor → API de Omnigent) se agrega **solo después** de que el ciclo funcione. Nunca llamar a Omnigent desde el navegador con credenciales.
- Preflight en la hora 0–1: confirmar acceso a Omnigent administrado y a un host que ejecute Python y llegue a Supabase. Si no, usar Omnigent de código abierto. Docs: [quickstart](https://developers.databricks.com/docs/omnigent/quickstart), [API programática](https://developers.databricks.com/docs/omnigent/programmatic), [spec YAML de agentes](https://github.com/omnigent-ai/omnigent/blob/main/docs/AGENT_YAML_SPEC.md).

### 7.5 Objetivo de la fase actual: la capa agéntica de descubrimiento

**Punto de partida:** `reports/experiments/EXP-001/result.json` (evidencia real). No elegir EXP-002 a mano.

**Roles mínimos** (se apoyan en los 7 agentes de §7.2; los nombres de salida son el objetivo):

| Rol | Entrada | Responsabilidad | Salida estructurada |
|---|---|---|---|
| Scientific Critic | `ExperimentResult` | Evaluar fuerza de la evidencia, incertidumbre, diagnósticos, limitaciones, interpretaciones no sustentadas y preguntas abiertas. Veredicto de `docs/EXPERIMENT_PROTOCOL.md`: `VALID` · `UNCERTAIN` · `REQUIRES_REVISION` · `REQUIRES_HUMAN_REVIEW` | `ScientificCritique` |
| Hypothesis Agent | estado + evidencia + crítica | Hipótesis falsables motivadas por la evidencia, separando evidencia existente, inferencia e hipótesis nueva | hipótesis con ID estable |
| Experiment Planner | hipótesis + crítica + variables y métodos soportados (§7.4) | **≥2 candidatos** cuando sea factible, cada uno con: pregunta, hipótesis que prueba, ganancia de información esperada, variables requeridas, factibilidad (¿cabe en el contrato actual?), limitaciones y por qué el resultado podría cambiar la interpretación | candidatos con ID estable |
| Discovery Director | estado completo | Elegir qué investigar después por aprendizaje esperado, no por probabilidad de significancia. Decisión registrada, explicable y trazable a evidencia | `decisions[]`, `next_action`, nuevo `ExperimentSpec` |
| Omnigent | — | Coordinar los roles y sus traspasos | sesión con traspasos visibles |

**Shared Research State objetivo** (sustituye a `initial_state.json` cuando se implemente; IDs estables para hipótesis, experimentos, críticas, candidatos y decisiones):

`research_question`, `dataset_version`, `population`, `evidence`, `hypotheses`, `experiments`, `experiment_results`, `scientific_critiques`, `limitations`, `candidate_experiments`, `decisions`, `next_action` (+ `project_id` para Supabase).

**Condición de éxito** (es el objetivo principal):

```
EXP-001 → el crítico evalúa el resultado real → hipótesis justificadas → candidatos en competencia
  → Omnigent elige uno y explica por qué → ExperimentSpec válido → ExperimentRunner determinista
  → nuevo ExperimentResult → el crítico lo evalúa → la siguiente decisión cambia según el resultado
```

**Qué dice EXP-001** (detalle en `reports/experiments/EXP-001/summary.md`; n = 2,563; coeficientes ajustados por +300 min de traslado entre semana, en minutos de lunes a viernes):

| Outcome | Coef. ajustado | IC 95 % puntual |
|---|---:|---|
| `sleep_weekday_min` | −48.711 | [−63.481, −33.940] |
| `leisure_weekday_min` | −20.396 | [−43.436, 2.644] |
| `household_conversation_weekday_min` | −3.816 | [−10.344, 2.712] |
| `personal_hygiene_weekday_min` | +3.094 | [−0.760, 6.948] |

- Estado: `EXPERIMENT_COMPLETED` · revisión `REQUIRES_HUMAN_REVIEW` · ranking **`INCONCLUSIVE_RANKING`**: solo 2 de 6 diferencias pareadas (sueño − conversación y sueño − higiene) excluyen el cero con Bonferroni. Sueño − ocio no se resuelve.
- La sensibilidad `exclude_zero_weekday_work` (34 excluidos, n = 2,529) no cambia direcciones ni orden.
- **Redacción aceptable:** "Longer weekday commuting showed the strongest negative point association with sleep in EXP-001, but uncertainty prevented a definitive ranking across all four time-use outcomes."
- **Redacción prohibida:** "commuting definitely sacrifices sleep the most" o cualquier variante causal o de ranking definitivo.
- **Direcciones abiertas que dejó EXP-001** (candidatas, **no** EXP-002 predeterminado): ¿la relación es no lineal? ¿difiere por sexo? El sistema debe evaluarlas junto con cualquier otro candidato justificado (p. ej. un experimento de validación) y elegir el de mayor aprendizaje esperado. Ambas requieren revisión del contrato si se piden como interacción o no linealidad; la estimación separada por sexo cabe en el contrato actual (§7.4).

## 8. Dataset (ENUT, INEGI)

**Estado: `analytic_v1` = `APPROVED_FOR_EXPERIMENTS`** (aprobación humana de la fase 3, 2026-10-03). El pipeline se construyó y validó fuera de este repo por fases (1 auditoría → 2A staging → 2B dataset canónico → 3 motor de experimentos). **No reconstruir el pipeline, no reinterpretar el dataset crudo de ENUT y no volver a limpiar datos.**

| Qué | Dónde |
|---|---|
| Dataset canónico (una fila por persona) | `data/processed/analytic_v1.parquet`, SHA256 `973f2c010940da06048eb12ade53fa271525d82f68d3a157ad78e429d687dd94` |
| Definiciones de variables y población | [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md) (**fuente de verdad**; no redefinir) |
| Procedencia, linaje, faltantes, validaciones | `metadata/analytic_v1_manifest.json` |
| Decisiones científicas por fase | [`docs/SCIENTIFIC_PROTOCOL.md`](docs/SCIENTIFIC_PROTOCOL.md) |

**Población analítica primaria:** 2,563 trabajadores de 18 a 65 años en CDMX (`09`) o Edomex (`15`) (suma de FAC_PER ≈ 12.74 millones). `active_worker = P5_1 = 1 o P5_2 ∈ 1–6`. Se excluyen los ausentes en la semana de referencia (`P5_2 = 7`) y quedan fuera de la población los de `P5_2 = 8`. Se exige traslado resuelto. No hay filtros de caso completo ni de valores extremos; los ceros se marcan, no se eliminan.

**Variables canónicas** (ENUT 2024, tabla TMODULO salvo indicación; tiempos = minutos totales de lunes a viernes):

| Rol | Variables |
|---|---|
| Exposición | `commute_5h` = `commute_weekday_min` / 300 (P5_9_1/P5_9_2). El trabajo solo virtual (P5_7 = 2, que se salta la 5.9) es un **cero estructural marcado** (`commute_structural_zero`) |
| Outcomes primarios | `sleep_weekday_min` (P6_1_1, incluye siestas) · `personal_hygiene_weekday_min` (P6_1_3, higiene/arreglo exclusivo, **no** todo el autocuidado) · `household_conversation_weekday_min` (P6_21A_1, conversación exclusiva con integrantes del hogar, **no** todo el tiempo familiar) · `leisure_weekday_min` (suma de 11 componentes de P6_18–P6_22; ver contrato) |
| Control de tiempo de trabajo | `work_weekday_min` (ramas de P5_8 según modalidad) |
| Otras | `age`, `sex` (1 hombre, 2 mujer), `state`, `work_modality`, `has_child_u15`, `has_minor_u18`, `household_size` (de TSDEM), `person_id`, `household_id` |
| Diseño muestral | `weight` (FAC_PER), `stratum` (EST_DIS), `cluster` (UPM_DIS) |

- Faltantes en la población primaria: 0 en exposición, outcomes, controles y diseño; `work_modality` 957 (no preguntada); `has_child_u15` y `has_minor_u18` 3 cada una.
- Solo `work_weekday_min`, `age`, `sex` y `state` están aprobadas como controles. Las demás variables canónicas no son controles automáticos.
- `staging_v1.parquet` es un artefacto histórico de la fase 2A (todas las personas de TMODULO, columnas crudas como texto). El motor **no** lo lee.
- El ZIP bruto (`data/raw/`) sigue fuera de git. En Supabase y en la web solo hay agregados.

⚠️ **Los nombres de variables cambian entre años.** En **ENUT 2019**, `P5_4_*` era el traslado y `P5_9_*` la búsqueda de trabajo. En **ENUT 2024** (la que usa `analytic_v1`), la **pregunta 5.9 / columnas `P5_9_1`–`P5_9_2`** es el traslado al trabajo, ya verificado por el pipeline.

## 9. Seguridad y secretos

- `.env` (raíz, lo usa Python) y `web/.env.local` están en `.gitignore`. `.env.example` solo tiene nombres.
- `SUPABASE_SERVICE_ROLE_KEY` vive solo en `analysis/`, en las herramientas de agentes y en Route Handlers del servidor. **Nunca** en una variable `NEXT_PUBLIC_*` ni en código del navegador.
- La web lee con `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, que RLS limita a SELECT.
- Las credenciales de Databricks/Omnigent van en variables de entorno, nunca en `omnigent.yaml`.
- Ejecutar `get_advisors(security)` después de cada cambio DDL.

## 10. Comandos

```bash
# Supabase (project ref: xnbruiprrxradfidoleu)
supabase login && supabase link --project-ref xnbruiprrxradfidoleu
supabase db push                                  # aplica supabase/migrations
psql "$SUPABASE_DB_URL" -f supabase/seed.sql      # seed demo (remoto)
supabase gen types typescript --linked > web/lib/database.types.ts

# Python (desde analysis/)
uv sync
uv run python -m rag.ingest                       # ingiere rag/corpus.json (--dry-run: solo fragmenta y cuenta)
uv run python -m rag.search "tiempo de traslado al trabajo" -k 5
uv run python -m rag.eval                         # QA de recuperación: hit@1, hit@5, MRR, ruido

# Motor de experimentos (desde la raíz; requiere data/processed/analytic_v1.parquet y
# metadata/analytic_v1_experiment_approval.json, que aún faltan en el repo: ver MEMORY.md §1)
python -m unittest discover -s tests -t .         # tests de esquema, runner y EXP-001
python scripts/validate_experiment_engine.py      # ⚠️ script aún no está en el repo
python scripts/run_experiment.py experiments/EXP-001/spec.json   # ⚠️ ídem; escribe reports/experiments/EXP-001/

# Omnigent (desde la raíz; las tools necesitan agents/ y analysis/ en el path)
uv tool install "omnigent[databricks]"            # o: pip install "omnigent[databricks]"
PYTHONPATH=agents:analysis omnigent run omnigent.yaml -p "$(cat initial_state.json)"
# Validar el spec sin credenciales de modelo:
PYTHONPATH=agents:analysis python -c "from pathlib import Path; from omnigent.spec import load; print(load(Path('omnigent.yaml')).name)"

# Web (desde web/)
npm run dev                                       # http://localhost:3000/research/00000000-0000-0000-0000-000000000001
npx next typegen && npx tsc --noEmit && npm run lint && npm run build
```

## 11. Roadmap de 10 horas

| Horas | Trabajo | Condición de salida |
|---|---|---|
| 0–1 | AGENTS.md, esqueleto del repo, vincular Supabase, preflight de Omnigent | Acceso real a BD + orquestador ✅/❌ |
| 1–3 | Migraciones, RLS, seed, ingesta + búsqueda RAG | `hybrid_search` devuelve pasajes con cita |
| 3–4.5 | Panel Next.js lee la BD (`/research/[id]`) | La web muestra estado real de la BD |
| 4.5–6.5 | ✅ Pipeline ENUT → `analytic_v1` aprobado → motor determinista → EXP-001 ejecutado (2026-10-03). ⏳ Falta conectar el motor a la tool `run_experiment` → `experiment_runs` | **Resultado real persistido** |
| 6.5–8 | **Fase actual.** Capa agéntica (§7.5): crítico sobre EXP-001 → hipótesis → candidatos → elección → nuevo `ExperimentSpec` → motor → crítica → decisión. Primera sesión real de Omnigent | **Decisión dependiente del resultado guardada** |
| 8–9 | El panel muestra el ciclo completo; reejecutar para reproducibilidad; cronometrar manual vs asistido | Reproducción y medición honestas |
| 9–10 | Desplegar en Vercel, README, grabar demo de 2 minutos | Entrega completa |

**Regla de alcance:** si el ciclo científico (ejecución real + decisión dependiente) no funciona a la **hora 6**, se detiene todo el trabajo de UI. Todo el equipo pasa a Omnigent + experimento + decisión. La web puede ser una sola página.

Demo (2 min, en inglés): problema y pregunta (15 s) → agentes y fuentes (25 s) → dos pruebas y la elección (20 s) → ejecución y resultado real (35 s) → decisión actualizada y limitaciones (25 s).

## 12. Definición de terminado

1. Una URL pública explica la pregunta, la población, las fuentes y el estado de la investigación.
2. Una sesión de Omnigent muestra ≥3 roles efectivos, llamadas a herramientas y traspasos.
3. Se ven las dos pruebas propuestas, la elegida y por qué se eligió.
4. El código estadístico se reejecuta sobre ENUT y reproduce el resultado dentro de la tolerancia declarada.
5. Las cifras muestran unidades (minutos de lunes a viernes por +300 min de traslado), `n`, método, incertidumbre (y su limitación de diseño) y enlaces de procedencia.
6. Se ve una decisión nueva derivada del resultado, con la regla aplicada y la siguiente prueba.
7. El repo contiene migraciones, configuraciones/políticas de agentes, instrucciones de ejecución, código, resultados y la medición de aceleración.

## 13. Convenciones para agentes que editen este repo

- Leer `MEMORY.md` al empezar y actualizarlo al terminar si cambió el estado (migraciones, ingestas, pendientes, trampas nuevas).
- Leer antes de escribir. Imitar el código existente. Cambios mínimos.
- Nunca editar una migración ya aplicada. Agregar un archivo nuevo con timestamp en `supabase/migrations/`.
- Después de editar `omnigent.yaml`, validarlo con `omnigent.spec.load` (ver §10). Si agregas una tool, implementarla en `agents/commute_lab/tools.py` y declararla con su JSON Schema.
- El contenido de seed/demo se marca (`is_demo`, prefijo `[DEMO]`) para que nunca se confunda con hallazgos.
- En `web/`, leer `web/AGENTS.md` (Next.js 16 trae cambios incompatibles) y la documentación incluida en `web/node_modules/next/dist/docs/`.
- Nunca commitear secretos, microdatos crudos (ZIP, `data/raw/`) ni `analysis/.cache/`. El dataset analítico de `data/processed/` sí se commitea.
- No tocar `data/processed/analytic_v1.parquet`, `metadata/analytic_v1_manifest.json`, `docs/DATA_CONTRACT.md` ni `docs/SCIENTIFIC_PROTOCOL.md` sin aprobación humana. Ampliar el motor (método, rol de variable, sensibilidad, hipótesis) exige revisar a la vez `schemas.py`, `metadata/experiment_contract.schema.json`, `docs/EXPERIMENT_ENGINE.md` y los tests.
- Cada experimento nuevo vive en `experiments/EXP-NNN/spec.json` y sus salidas en `reports/experiments/EXP-NNN/`. Nunca editar a mano un `result.json`.

## Registro de decisiones

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-03 | Proyecto Supabase `xnbruiprrxradfidoleu`; esquema = CONTEXT §7, más `decision_rules`, `generated_by`, `rule_applied`, `limitations` e `is_demo` | El pre-registro y el etiquetado se necesitan para la nota de rigor |
| 2026-10-03 | El índice de texto usa la configuración `'simple'` | El corpus mezcla español e inglés |
| 2026-10-03 | Embeddings calculados en Python (e5-small, CPU), no en la BD | Un solo modelo para ingesta y consulta; las herramientas de los agentes son Python |
| 2026-10-03 | Web de solo lectura (clave publishable + RLS) que consulta cada 5 s | Sin secretos en el navegador; tiempo real es opcional |
| 2026-10-03 | Documentación y sesiones en español; UI web, demo, README y prompts en inglés | Preferencia del equipo |
| 2026-10-03 | Año y pipeline ENUT: **pendiente del usuario** | El usuario entregará el pipeline completo |
| 2026-10-03 | Se adopta la arquitectura de **7 agentes + Shared Research State** de `omnigent.yaml`. Reemplaza los 4 roles iniciales (coordinador → Discovery Director; evidencia → Literature Agent; método/datos → Hypothesis Agent + Data Steward + Experiment Planner; crítico → Scientific Critic) | Decisión del equipo; da más traspasos visibles (orquestación = 30 %) |
| 2026-10-03 | El JSON de estado es el contrato entre agentes; Supabase es la persistencia que lee la web | Ambos diseños se complementan: uno para la sesión, otro para auditoría y panel |
| 2026-10-03 | `omnigent.yaml` reescrito con el formato real de Omnigent 0.16: Director raíz + 6 sub-agentes `type: agent`, 10 tools `type: function` y políticas `type: function`. Validado con `omnigent.spec.load` | El formato anterior (`agents:` lista, `role`, `system_prompt`, `handoffs`, `policies` como lista) no era válido: el loader lo rechazaba por no tener `prompt` |
| 2026-10-03 | `execute_python_sandbox` → `run_experiment` con protocolos cerrados | Reproducibilidad y regla de no ejecutar código arbitrario |
| 2026-10-03 | Aprobación humana (ASK) para `run_experiment` y `record_decision` | Requisito del track |
| 2026-10-03 | Ciclo de regreso: el Director puede repetir planner → runner → critic una vez | La decisión debe cambiar la siguiente prueba |
| 2026-10-03 | Modelo `databricks/dbrx-instruct` → `databricks-claude-sonnet-4-6` (harness `claude-sdk`) | El id anterior no tenía el formato de Omnigent; se usa el de los ejemplos oficiales |
| 2026-10-03 | Paquete de tools llamado `commute_lab`, no `agents` | `agents` es el nombre de import del SDK `openai-agents` que usa Omnigent |
| 2026-10-03 | `variables` se guarda en `experiment_runs.parameters.variables` | Evita una migración nueva |
| 2026-10-03 | El índice de texto pasa de `'simple'` a `public.es_unaccent` (español + unaccent) y `hybrid_search` acepta coincidencias parciales ordenadas por nº de términos (migración `20261003221539_rag_spanish_fts`). Reemplaza la decisión del índice `'simple'` | Todos los pasajes están en español (los papers de OpenAlex no tienen pasajes). Con `'simple'` + `websearch_to_tsquery` (AND) casi ninguna consulta natural tenía coincidencias de texto y la búsqueda quedaba solo semántica |
| 2026-10-03 | El cuestionario ENUT 2024 se ingiere como fuente propia (`kind = 'questionnaire'`, un pasaje por pregunta, pp. 3–25 del PDF de INEGI) y se excluye el anexo B del diseño conceptual (pp. 91–115) | Las páginas de formulario contaminaban los resultados y no permitían citar una pregunta concreta |
| 2026-10-03 | Las consultas en inglés se expanden con un glosario fijo inglés → español; no hay traductor ni reranker | Determinista y auditable; el eval mide si basta |
| 2026-10-03 | La salida del pipeline es `data/processed/analytic_v1.parquet` + contrato + metadata, versionados en git. `run_experiment` lo hashea (`sha256`) y se lo pasa al protocolo; el Data Steward lo lee con la tool nueva `describe_dataset`. Relaja la regla "solo los agregados salen de la máquina": el ZIP bruto sigue fuera de git y Supabase sigue sin filas individuales | Decisión del equipo: un dataset analítico único que Omnigent y el ExperimentRunner consumen directamente. Deriva de microdatos públicos de INEGI, cuya licencia permite redistribuir citando la fuente |
| 2026-10-03 | Año de la encuesta: **ENUT 2024**. Pregunta reformulada: exposición `commute_5h` (+300 min de lunes a viernes), 4 outcomes canónicos (sueño, higiene personal exclusiva, conversación exclusiva en el hogar, ocio), población de 18–65 años. Unidades: minutos totales de lunes a viernes. Los cuidados salen de los outcomes. Reemplaza la pregunta de "60 minutos semanales" | Contrato `analytic_v1` aprobado (fase 2B) en `docs/DATA_CONTRACT.md` |
| 2026-10-03 | El motor determinista `src/experiments/` (`ExperimentSpec` → `ExperimentResult`, solo `weighted_linear_regression`, CR1 por UPM) es el único camino computacional. Reemplaza los protocolos `weighted_means_by_group` y `wls_commute_by_sex` de `analysis/enut/protocols.py`, que nunca se implementaron | Contrato estricto y reproducible ya validado (fase 3) |
| 2026-10-03 | EXP-001 completado: sueño tiene la asociación puntual más negativa, pero el ranking es `INCONCLUSIVE_RANKING`. Queda como `REQUIRES_HUMAN_REVIEW` | Resultado del motor; ver `reports/experiments/EXP-001/` |
| 2026-10-03 | No hay secuencia fija de experimentos: EXP-002 lo elige el sistema (crítico → hipótesis → ≥2 candidatos → Director) según el aprendizaje esperado. No linealidad y diferencia por sexo son candidatos, no decisiones | Requisito del track: la evidencia debe cambiar la siguiente decisión |
| 2026-10-03 | El Shared Research State se amplía (§7.5) con `dataset_version`, `experiment_results`, `scientific_critiques`, `candidate_experiments`, `decisions` y `next_action`, todos con IDs estables | Trazabilidad de cada decisión a la evidencia |

## Decisiones abiertas

1. **Endpoint del modelo.** Verificar en el workspace de Databricks que `databricks-claude-sonnet-4-6` exista y que el perfil `DEFAULT` tenga acceso. Si no, cambiar `executor` en `omnigent.yaml`: el ancla `&executor` aplica a los 7 agentes.
2. **Archivos que faltan en el repo.** El motor y los tests necesitan `data/processed/analytic_v1.parquet`, `metadata/analytic_v1_experiment_approval.json`, `src/experiments/report.py`, `scripts/run_experiment.py`, `scripts/validate_experiment_engine.py` y `requirements-experiments.txt`. Los documentos citan además `metadata/mappings/` y `reports/audit/`. Hay que traerlos del entorno donde se construyó el pipeline, sin regenerarlos, y comprobar que el SHA256 del parquet coincide con el manifiesto.
3. **Alcance de las políticas en sub-agentes.** Comprobar en la primera sesión real que el ASK también se dispara cuando un sub-agente (runner, critic) llama a la tool. Si no, mover esas llamadas al Director.
4. **`ExperimentResult` en Supabase.** Decidir si `experiment_runs.results` guarda el resultado completo o un resumen + `artifact_paths`, y cómo se guardan `ScientificCritique` y los candidatos (¿`decisions` y `experiment_proposals` bastan, o hace falta una migración?).
5. **Revisión humana de EXP-001.** Su `review_status` es `REQUIRES_HUMAN_REVIEW`. Definir si el ciclo agéntico puede usarlo como evidencia antes de esa revisión (marcado como provisional) o si la revisión es un paso del ciclo.
6. **Ampliación del contrato.** Si el sistema elige un experimento que necesita interacciones, no linealidad o H3/H4, hay que revisar el contrato del motor con aprobación humana (§7.4).

## Para los commits

Quiero que el commit explique de manera breve los cambios hechos, en ingles y no pongas creditos de co-autoria en ningun commit.
