# MEMORY.md — Estado y contexto que un agente debe conocer antes de tocar nada

Memoria compartida del proyecto. Complementa a `AGENTS.md`: allí están las reglas y los contratos; aquí está **el estado real**, **lo que ya se hizo y cómo**, y **las trampas encontradas**.

**Mantenerlo al día:** quien cambie el estado (aplicar una migración, ingerir fuentes, cerrar un pendiente) actualiza este archivo en el mismo commit. Las fechas son absolutas.

---

## 1. Estado actual (2026-10-03)

| Frente | Estado |
|---|---|
| `AGENTS.md` (contexto, contratos, roadmap) | ✅ Hecho |
| Migraciones Supabase (extensiones, tablas, RAG, RLS) | ✅ Aplicadas en remoto |
| Seed demo | ✅ Cargado en remoto |
| Ingesta RAG (3 PDFs INEGI ENUT 2024) | ✅ 535 pasajes limpios con embedding: cuestionario por pregunta (88), diseño conceptual (402), diseño muestral (45). FTS en español |
| Web (`/` y `/research/[id]`) leyendo Supabase real | ✅ Verificado con `next dev`; `npm run build` pasa |
| Pipeline ENUT → `analytic_v1` | ✅ Construido y validado fuera del repo (fases 1 → 2A → 2B). **`APPROVED_FOR_EXPERIMENTS`**. ENUT 2024, n = 2,563. Documentación en `docs/` y `metadata/analytic_v1_manifest.json` (commit `805b7c2`) |
| Motor de experimentos (`src/experiments/`) | ✅ Determinista, `ExperimentSpec` → `ExperimentResult`, solo `weighted_linear_regression` con CR1 por UPM. Tests en `tests/` |
| EXP-001 | ✅ `EXPERIMENT_COMPLETED`, `REQUIRES_HUMAN_REVIEW`, `INCONCLUSIVE_RANKING`. Resultados en `reports/experiments/EXP-001/` (ver §4) |
| Motor de experimentos: empaquetado | ✅ Clon limpio verificado el 2026-10-03: `pip install -r requirements-experiments.txt`, validador PASS, EXP-001 con 0 diferencias numéricas, sin datos crudos ni `staging_v1` (§5). Pendiente: borrar `audit/` y `metadata/provenance.json`; validar `omnigent.yaml` en un entorno con Omnigent |
| Tool `run_experiment` (`agents/commute_lab/tools.py`) | 🟡 **Desfasada**: sigue esperando `analysis/enut/protocols.py` (`weighted_means_by_group`, `wls_commute_by_sex`), que ya no se va a escribir. Hay que reescribirla para que reciba un `ExperimentSpec` y llame al motor. `save_proposals` valida contra la misma lista vieja y `describe_dataset` busca `data/processed/analytic_v1.*` en vez de `docs/` + `metadata/` |
| Capa agéntica de descubrimiento | ⏳ **Fase actual.** Scientific Critic, Hypothesis Agent, Experiment Planner, Discovery Director y orquestación Omnigent sobre la evidencia de EXP-001 (ver `AGENTS.md` §7.5). Nada implementado aún |
| Agentes Omnigent | 🟡 `omnigent.yaml` reescrito con el formato real y **validado con `omnigent.spec.load`** (Omnigent 0.16). Las 11 tools de `agents/commute_lab/` están implementadas; 10 se probaron contra Supabase. Los prompts y `initial_state.json` todavía describen la pregunta y el estado viejos (60 min semanales, protocolos cerrados). Desde `84207bb` usan Omnigent de código abierto con harness `codex`, `gpt-5.4-mini` y `OPENAI_API_KEY` (hay que revalidar el spec con `omnigent.spec.load`). **Falta la primera sesión real** |
| Papers de OpenAlex | 🟡 `search_openalex` funciona y registra cada paper en `sources` (`kind = 'paper'`, solo metadatos y resumen, sin pasajes) |
| Despliegue en Vercel | ✅ https://commute-time-lab.vercel.app (producción, pública) |
| Repo | ✅ Historia local fusionada con `origin/main` (GitHub `RogelioZu/Hack-nation-hackathon`) |

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
- **Smoke test de las tools**: se probaron las 10 contra Supabase con un proyecto temporal `[SMOKE TEST]`, borrado al final (la cascada limpia todo; los `sources` de OpenAlex se borraron a mano). `run_experiment` hoy siempre termina en `failed` con el motivo "Analytic dataset data/processed/analytic_v1.parquet is not available yet", que es lo esperado.

### Motor de experimentos: empaquetado (resuelto el 2026-10-03)
- **Verificado desde un clon limpio** (`core.autocrlf=true`, sin `data/raw/` ni `data/interim/`, venv nuevo con solo `pip install -r requirements-experiments.txt`): 16 tests OK, `validate_experiment_engine.py` PASS, `run_experiment.py` reproduce EXP-001 con **0 diferencias en 1,801 valores numéricos**, y el SHA256 del parquet no cambia.
- `requirements-experiments.txt` es autocontenido: numpy, pandas, pyarrow, pydantic, scipy (motor) + statsmodels, patsy (tests), con las versiones del runtime de EXP-001. Requiere Python ≥ 3.11; el Python por defecto de esta máquina es 3.7, así que usar `py -3.12`.
- **Ruta larga en Windows:** instalar statsmodels en un venv con ruta profunda falla con `OSError [Errno 2]` (límite de 260 caracteres por sus archivos de test anidados). Usar una ruta de venv corta o habilitar rutas largas.
- `validate_experiment_engine.py` ya **no** lee datos crudos ni `staging_v1`, y no cuenta los tests del pipeline. Comprueba: hash aprobado (parquet = manifiesto = aprobación) y consistencia con el manifiesto (vía `load_approved`), JSON Schema = modelos Pydantic, registro de métodos = esquema, tests del motor, EXP-001 dos veces idéntico, igualdad exacta con el `result.json` commiteado (salvo `code_sha256`, `code_fingerprints`, `protocol_fingerprints` y `runtime`), bytes de `result.json` = `result_sha256` de `validation.json`, y entradas sin cambios. Escribe `engine_validation.json`.
- **Finales de línea (`.gitattributes`):** LF forzado en `*.py`, `*.md`, `*.json`, `*.yaml`, `*.yml` y `*.txt`; parquet y PDF binarios. Dos excepciones con `-text` (bytes exactos): `metadata/analytic_v1_manifest.json` y `reports/experiments/EXP-001/result.json`. Ambos se generaron con CRLF, y la procedencia registra el hash de esos bytes (`manifest_sha256` f800513b…, `result_sha256` 5e4084a3…), pero git los había guardado con LF (f23add97…, 3113a9ee…). Un clon limpio no coincidía con la procedencia de EXP-001. Las cifras nunca cambiaron.
- **Al commitear:** git no detecta solo que esos dos archivos cambiaron, porque su fecha de modificación no cambió. Agregarlos explícitamente: `git add .gitattributes metadata/analytic_v1_manifest.json reports/experiments/EXP-001/result.json`. El diff muestra ~8,000 líneas por archivo, pero solo cambian los finales de línea.
- `scripts/run_experiment.py` ahora escribe siempre LF (`newline="
"`), así que sus salidas y `result_sha256` son iguales en cualquier sistema. Antes, en Windows escribía CRLF.
- **Procedencia de entorno:** el runner hashea su código, `requirements-experiments.txt`, `docs/EXPERIMENT_ENGINE.md` y los docs de protocolo (`AGENTS.md`, `docs/*`). Cualquier edición de esos archivos cambia `code_sha256` y `protocol_fingerprints` en una reejecución, sin tocar cifras. El validador lo reporta en `exp001_environment_provenance_changed`.
- **Correr los tests directamente:** `PYTHONPATH=. python -m unittest discover -s tests` (`tests/` no es paquete; con `-t .` falla). `src/experiments/report.py` no depende de `tests/`: la dependencia es solo tests → producción.
- **Pendiente (requiere permiso del usuario):** borrar `audit/` (idéntica byte por byte a `reports/audit/`; ningún doc ni JSON la cita) y `metadata/provenance.json` (0 bytes, sin consumidores): `git rm -r audit metadata/provenance.json`.
- El mensaje del commit `04df096` perdió letras (`ngine_validation`, `equirements`…) por secuencias de escape. Es cosmético y está en `origin`: no reescribir la historia.

### Vercel
- Cuenta Hobby. El proyecto `commute-time-lab` está en el scope `roger-1592` (`team_37NrEuZAkgRsRYTKpMCwC5j9`).
  - El MCP de Vercel da **403 si se pasa `teamId`**. Funciona sin `teamId` (usa el scope por defecto).
- Despliegue por API con archivos inline (no hay conexión con Git ni CLI de Vercel). Se suben solo los fuentes de `web/`, **sin `package-lock.json`** (240 KB), así que Vercel resuelve versiones desde `package.json`. Para redeployar: `create_deployment` con los archivos, o conectar el repo de GitHub.
- Variables en el proyecto (production, preview y development): `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- `https://commute-time-lab.vercel.app` es público. Los alias por deployment y `…-roger-1592.vercel.app` piden login de Vercel (SSO protection por defecto).

## 6. Preferencias del usuario

- **Idioma:** documentación y conversación en español. UI web, demo y textos guardados en Supabase en inglés (ver `AGENTS.md` §0).
- **Commits:** mensaje breve en inglés y **sin créditos de coautoría** (ver `AGENTS.md`, "Para los commits").
- **El pipeline de datos está cerrado.** No reconstruirlo, no reinterpretar los datos crudos, no modificar `analytic_v1.parquet` y no volver a limpiar datos salvo que una validación científica explícita falle.
- `analytic_v1` y sus metadatos están **versionados en git** para que Omnigent y el motor los consuman directamente. El ZIP bruto (`data/raw/`) sigue fuera de git y Supabase sigue sin filas individuales.
- Prioridad: **el ciclo de descubrimiento antes que la UI**. No programar EXP-001 → EXP-002 → EXP-003 fijo; la evidencia debe poder cambiar la siguiente decisión.

## 7. Próximos pasos

1. Borrar `audit/` y `metadata/provenance.json` (§5) y validar `omnigent.yaml` con `omnigent.spec.load` donde Omnigent esté instalado (es independiente del motor).
2. **Conectar el motor a las tools:** reescribir `run_experiment` en `agents/commute_lab/tools.py` para que valide un `ExperimentSpec` y llame a `src.experiments.runner.run_experiment`. Actualizar `save_proposals` y `describe_dataset` (que exponga `docs/DATA_CONTRACT.md`, el manifiesto y los valores que acepta el esquema). Quitar las referencias a `analysis/enut/protocols.py`. El entorno de Omnigent necesita pandas, pyarrow, numpy, scipy y pydantic.
3. **Capa agéntica** (`AGENTS.md` §7.5): estructuras `ScientificCritique`, hipótesis y candidatos con IDs estables, el Shared Research State ampliado y los prompts de crítico, Hypothesis Agent, Planner y Director. Arrancar desde `reports/experiments/EXP-001/result.json`.
4. Actualizar `omnigent.yaml` e `initial_state.json` a la pregunta, unidades y outcomes de `analytic_v1`, y validar con `omnigent.spec.load`.
5. Decidir cómo se guarda `ExperimentResult` en Supabase y adaptar `web/lib/types.ts` ([Decisiones abiertas](AGENTS.md#decisiones-abiertas) 4).
6. Cargar `OPENAI_API_KEY` (`set -a; source .env; set +a`) y verificar que `gpt-5.4-mini` esté habilitado → primera sesión real: `PYTHONPATH=agents:analysis omnigent run omnigent.yaml -p "$(cat initial_state.json)"`. Comprobar que el ASK salta cuando un sub-agente llama a `run_experiment` o `record_decision`.
7. RAG: si el eval o el uso real lo piden, agregar reranker multilingüe o filtro por `source_kind` (ver §3).
8. Decidir sobre `rls_auto_enable()` (ver §2).
9. Redeployar la web cuando cambie `web/`, o conectar el repo de GitHub a Vercel.
