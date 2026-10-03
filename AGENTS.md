# AGENTS.md — Commute & Time Lab (Hack Nation × Databricks · Agentic Scientific Discovery)

> **Nota para asistentes de IA (Claude, Codex, Cursor, Copilot, etc.):** este documento es la **fuente única de verdad** para la arquitectura de agentes, el flujo de datos, las reglas científicas y las convenciones del repo.

`CONTEXT.md` es la especificación original (larga); este archivo es su versión operativa. Si se contradicen, **gana este archivo**. Si alguno contradice el diccionario de datos ENUT, los microdatos o la documentación oficial, **ganan los datos**: corregir el supuesto aquí y registrarlo en el [Registro de decisiones](#registro-de-decisiones).

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

Construir un MVP web en el que **Omnigent orquesta en vivo agentes especialistas** para investigar una pregunta científica con microdatos reales de la **ENUT** (Encuesta Nacional sobre Uso del Tiempo, INEGI):

> Entre trabajadores residentes en Ciudad de México (CDMX) y Estado de México (Edomex), ¿cómo se relacionan **60 minutos semanales adicionales de traslado laboral** con el tiempo **semanal** dedicado a sueño, convivencia familiar/social, cuidados a integrantes del hogar, ocio y cuidado personal? ¿Difiere la asociación por sexo?

Ciclo obligatorio, con cada paso persistido en Supabase:

```
pregunta → evidencia (RAG, con citas) → hipótesis → ¿los datos permiten probarla? → ≥2 pruebas candidatas
        → elección registrada → ejecución reproducible (microdatos ENUT reales) → crítica
        → decisión actualizada que DEPENDE del resultado → siguiente prueba (vuelve al ciclo)
```

No ampliar a otras ciencias, mapas de rutas, recomendaciones de transporte, modelos causales, cuentas de usuario ni múltiples datasets.

## 2. Reglas científicas innegociables

- ENUT es **observacional y transversal**: decir "se asocia con", nunca "causa", "reduce" ni "provoca".
- El traslado se mide en la **semana de referencia** de la encuesta. Las unidades son **minutos semanales**. Nunca llamar "una hora diaria" a una hora semanal.
- La cobertura estatal (CDMX + Edomex) **no** es una muestra representativa de la Zona Metropolitana del Valle de México. No afirmarlo.
- **No inventar cifras, variables ni citas.** Las cifras salen solo de `run_experiment`. Las afirmaciones factuales salen solo de pasajes RAG con `source_id` / `passage_id` / URL, o de registros de OpenAlex con DOI.
- Las hipótesis generadas por agentes se **etiquetan** (`hypotheses.generated_by`).
- Reportar siempre `n` antes y después de exclusiones, porcentaje de faltantes, distribución del traslado, método de incertidumbre y qué elementos del diseño muestral se usaron (`FAC_PER`, `UPM_DIS`, `EST_DIS`). Si los intervalos no son plenamente consistentes con el diseño, etiquetar el resultado como **exploratorio** y explicar por qué.
- No forzar que las actividades sumen 24 h/día ni 168 h/semana (ENUT capta cuidados simultáneos o pasivos).
- Mantener separados **cuidados** (secciones 6.11–6.15) y **convivencia** (6.21), y separar **sueño** del resto del cuidado personal (6.1). Documentar si se incluye cuidado pasivo o simultáneo.
- **Reglas de decisión pre-registradas** en `projects.decision_rules` *antes* de ver resultados:
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
| RAG + host del experimento | Python 3.12 con **uv** → `analysis/` |
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
  rag/ingest.py            manifiesto → descarga → fragmentos con localizador → embeddings → upsert
  rag/search.py            search_evidence() → RPC hybrid_search
  rag/corpus.json          manifiesto del corpus (docs INEGI; agregar aquí papers de OpenAlex)
  enut/                    pipeline ENUT — LO PROPORCIONA EL USUARIO (pendiente)
agents/
  commute_lab/tools.py     10 tools que persisten en Supabase (create_project … record_decision)
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
| `passages` | Fragmentos RAG | `source_id`, `section`, `locator` (único por fuente, p. ej. `p. 12`), `content`, `embedding vector(384)`, `fts` (generada, configuración `'simple'`) |
| `hypotheses` | Afirmaciones a probar | `statement`, `generated_by`, `status` (proposed·testing·supported·not_supported·inconclusive·superseded), `supporting_passage_ids[]`, `opposing_passage_ids[]` |
| `experiment_proposals` | ≥2 pruebas candidatas | `label` (A/B), `title`, `protocol` (clave cerrada), `learning_value`, `feasibility`, `cost`, `selected`, `selection_rationale` |
| `experiment_runs` | Ejecuciones reproducibles | `proposal_id`, `protocol`, `dataset_hash`, `code_version`, `parameters`, `sample_sizes`, `results` (contrato abajo), `artifact_paths`, `status` (pending·running·succeeded·failed), `error` |
| `decisions` | Crítica → siguiente paso | `experiment_run_id`, `interpretation`, `uncertainty`, `limitations`, `rule_applied` (R1/R2/R3), `next_test`, `rationale`, `decided_by` |
| `agent_events` | Línea de tiempo / auditoría | `session_id`, `agent_name`, `event_type` (started·tool_call·handoff·output·decision·approval·error·note), `summary`, `input_refs`, `output_refs`, `occurred_at` |

**RLS:** activo en todas las tablas. `anon` y `authenticated` tienen solo SELECT. No hay políticas de escritura, así que solo `service_role` escribe (host Python, herramientas de Omnigent, Route Handlers protegidos de Next). **Nunca guardar filas individuales de microdatos.** Solo agregados y procedencia.

### Contrato de resultados (`experiment_runs.results`)

La web dibuja esta forma (ver `web/lib/types.ts`) y el pipeline ENUT debe emitirla. Los textos de `label`, `method`, `units` y `notes` van **en inglés**, porque se muestran en la web:

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
- Recuperación: `public.hybrid_search(query_text, query_embedding, match_count=5, full_text_weight=1, semantic_weight=1, rrf_k=50)`. Combina texto completo (`websearch_to_tsquery('simple')`) y coseno (HNSW) con Reciprocal Rank Fusion. Devuelve `passage_id, source_id, source_title, source_kind, url, doi, section, locator, content, score`.
- Punto de entrada en Python: `rag.search.search_evidence(query, k=5) -> list[EvidenceHit]`. El corpus actual está en español, así que **consultar en español**.
- Corpus deliberadamente pequeño: cuestionario ENUT, diccionario/descriptor, diseño conceptual y diseño muestral, más 10–20 papers pertinentes de OpenAlex (los encuentra `search_openalex` del Literature Agent). Guardar texto completo **solo si la licencia lo permite**. Si no, guardar título + resumen.
- El RAG fundamenta conceptos, literatura y decisiones de método. **Nunca produce cifras de resultados.**
- Control de calidad: revisar a mano 5 consultas de recuperación y 10 afirmaciones factuales del panel.

## 7. Arquitectura de agentes (Omnigent)

Arquitectura definida por el equipo en `omnigent.yaml` (commits `bda27fc` y `b9e6e74`).

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
| 3 | Data Steward (`data_steward`) | Si los datos permiten probarla | hipótesis líder | `variables`, `population` y `limitations` (reporte de calidad) | `search_evidence` | Va en el estado JSON; la herramienta de perfil ENUT llega con el pipeline |
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

- El Experiment Runner ejecuta **solo protocolos cerrados** (`weighted_means_by_group`, `wls_commute_by_sex`) vía `run_experiment(project_id, proposal_id, parameters)`. Esta función registra la versión de código (SHA de git), los parámetros, el hash del dataset y los resultados. **Ningún agente tiene SQL ni shell arbitrario sobre los datos.**
- `run_experiment` busca `analysis/enut/protocols.py` con `PROTOCOLS = {nombre: fn(parameters) -> {"results", "sample_sizes", "dataset_hash"}}`. Si no existe, guarda el run como `failed` con el motivo; **nunca inventa cifras**.
- Cada llamada a herramienta escribe una fila en `agent_events`. La política `commute_lab.policies.ask_before_run` devuelve **ASK** (aprobación humana) antes de `run_experiment` y de `record_decision`. Hay además un tope de 150 llamadas por sesión.
- Los textos que los agentes guardan (en el JSON y en Supabase) van **en inglés**, porque los muestra la web.
- La sesión se inicia desde Omnigent y se guarda `projects.omnigent_session_url`. Un botón "Start research" (Route Handler del servidor → API de Omnigent) se agrega **solo después** de que el ciclo funcione. Nunca llamar a Omnigent desde el navegador con credenciales.
- Preflight en la hora 0–1: confirmar acceso a Omnigent administrado y a un host que ejecute Python y llegue a Supabase. Si no, usar Omnigent de código abierto. Docs: [quickstart](https://developers.databricks.com/docs/omnigent/quickstart), [API programática](https://developers.databricks.com/docs/omnigent/programmatic), [spec YAML de agentes](https://github.com/omnigent-ai/omnigent/blob/main/docs/AGENT_YAML_SPEC.md).

## 8. Dataset (ENUT, INEGI)

**Estado: pendiente. El pipeline ENUT completo lo proporciona el usuario** y va en `analysis/enut/`. Hasta entonces, no escribir transformaciones a partir de supuestos.

Lo que el pipeline debe hacer, sin importar el año de la encuesta:
- Procesar el ZIP bruto localmente en Python. Solo los agregados salen de la máquina.
- Filtrar CDMX + Edomex tras comprobar los códigos geográficos (`ENT` en 2019, `CVE_ENT` en 2024; CDMX = `09`, Edomex = `15`).
- Comprobar en el descriptor los códigos de faltantes y saltos, las llaves y los filtros de ocupación **antes** de transformar.
- Conservar `FAC_PER`, `UPM_DIS` y `EST_DIS`.
- Exponerse como protocolos cerrados de `run_experiment` y emitir el [contrato de resultados](#contrato-de-resultados-experiment_runsresults).

⚠️ **Los nombres de variables cambian entre años.** En **ENUT 2019** (codebook DDI revisado), el traslado al trabajo es `P5_4_1..4` (lun–vie h/min, sáb–dom h/min). Las horas trabajadas son `P5_3_*`, el sueño `P6_1_1_*`, la convivencia `P6_21A_*`, la edad `EDAD_V` y el sexo `SEXO`. En 2019, `P5_9_*` es **tiempo buscando trabajo, NO traslado**. CONTEXT.md da `P5_9_*` como traslado para **2024**. Verificarlo contra el diccionario 2024 antes de usarlo.

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
uv run python -m rag.ingest                       # ingiere rag/corpus.json
uv run python -m rag.search "tiempo de traslado al trabajo" -k 5

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
| 4.5–6.5 | Pipeline ENUT del usuario → `run_experiment` → `experiment_runs` | **Resultado real persistido** |
| 6.5–8 | Omnigent: primera sesión real con los 7 agentes de `omnigent.yaml` (tools ya implementadas), ciclo completo | **Decisión dependiente del resultado guardada** |
| 8–9 | El panel muestra el ciclo completo; reejecutar para reproducibilidad; cronometrar manual vs asistido | Reproducción y medición honestas |
| 9–10 | Desplegar en Vercel, README, grabar demo de 2 minutos | Entrega completa |

**Regla de alcance:** si el ciclo científico (ejecución real + decisión dependiente) no funciona a la **hora 6**, se detiene todo el trabajo de UI. Todo el equipo pasa a Omnigent + experimento + decisión. La web puede ser una sola página.

Demo (2 min, en inglés): problema y pregunta (15 s) → agentes y fuentes (25 s) → dos pruebas y la elección (20 s) → ejecución y resultado real (35 s) → decisión actualizada y limitaciones (25 s).

## 12. Definición de terminado

1. Una URL pública explica la pregunta, la población, las fuentes y el estado de la investigación.
2. Una sesión de Omnigent muestra ≥3 roles efectivos, llamadas a herramientas y traspasos.
3. Se ven las dos pruebas propuestas, la elegida y por qué se eligió.
4. El código estadístico se reejecuta sobre ENUT y reproduce el resultado dentro de la tolerancia declarada.
5. Las cifras muestran unidades semanales, `n`, método, incertidumbre y enlaces de procedencia.
6. Se ve una decisión nueva derivada del resultado, con la regla aplicada y la siguiente prueba.
7. El repo contiene migraciones, configuraciones/políticas de agentes, instrucciones de ejecución, código, resultados y la medición de aceleración.

## 13. Convenciones para agentes que editen este repo

- Leer `MEMORY.md` al empezar y actualizarlo al terminar si cambió el estado (migraciones, ingestas, pendientes, trampas nuevas).
- Leer antes de escribir. Imitar el código existente. Cambios mínimos.
- Nunca editar una migración ya aplicada. Agregar un archivo nuevo con timestamp en `supabase/migrations/`.
- Después de editar `omnigent.yaml`, validarlo con `omnigent.spec.load` (ver §10). Si agregas una tool, implementarla en `agents/commute_lab/tools.py` y declararla con su JSON Schema.
- El contenido de seed/demo se marca (`is_demo`, prefijo `[DEMO]`) para que nunca se confunda con hallazgos.
- En `web/`, leer `web/AGENTS.md` (Next.js 16 trae cambios incompatibles) y la documentación incluida en `web/node_modules/next/dist/docs/`.
- Nunca commitear secretos, microdatos crudos ni `analysis/.cache/`.

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

## Decisiones abiertas

1. **Endpoint del modelo.** Verificar en el workspace de Databricks que `databricks-claude-sonnet-4-6` exista y que el perfil `DEFAULT` tenga acceso. Si no, cambiar `executor` en `omnigent.yaml`: el ancla `&executor` aplica a los 7 agentes.
2. **Herramienta de perfil ENUT para el Data Steward** (`inspect_enut_variables` / `get_dataset_profile`). Llega junto con el pipeline del usuario.
3. **Alcance de las políticas en sub-agentes.** Comprobar en la primera sesión real que el ASK también se dispara cuando un sub-agente (runner, critic) llama a la tool. Si no, mover esas llamadas al Director.

## Para los commits

Quiero que el commit explique de manera breve los cambios hechos, en ingles y no pongas creditos de co-autoria en ningun commit.
