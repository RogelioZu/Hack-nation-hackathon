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
| Pipeline ENUT (`analysis/enut/`) | ⏳ **Pendiente: lo entrega el usuario.** Salida acordada: `data/processed/analytic_v1.parquet` + contrato + metadata (`analytic_v1.*`), versionados en git |
| `run_experiment` y protocolos cerrados | 🟡 `run_experiment` ya apunta al parquet (guarda su `sha256` como `dataset_hash`) y `describe_dataset` lee contrato y metadata. Faltan el dataset y `analysis/enut/protocols.py`, que se escribe contra el contrato |
| Agentes Omnigent | 🟡 `omnigent.yaml` reescrito con el formato real y **validado con `omnigent.spec.load`** (Omnigent 0.16). Las 11 tools de `agents/commute_lab/` están implementadas; 10 se probaron contra Supabase y `describe_dataset` con un dataset ficticio fuera del repo. **Falta la primera sesión real**: requiere el perfil de Databricks y el endpoint del modelo |
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

## 4. Dataset ENUT

- `MEX-INEGI.ESD3.04-ENUT-2019.xml` era el **codebook DDI de ENUT 2019**: metadatos de 1300 variables y 8 tablas. **No son microdatos.** El usuario pidió **ignorarlo** porque entregará el pipeline completo. Nunca se commiteó, y el 2026-10-03 ya no estaba en la carpeta del repo.
- Hallazgo del codebook 2019, ya documentado en `AGENTS.md` §8:
  - `P5_4_*` es el traslado al trabajo; `P5_9_*` es el tiempo buscando trabajo.
  - `ENT` vale `09` para CDMX y `15` para Edomex.
  - `TMODULO_tradicional` tiene 71,404 casos a nivel nacional.
- CONTEXT.md asume ENUT **2024**. El año definitivo lo fija el pipeline del usuario.
- Hallazgos del **cuestionario ENUT 2024** (ingerido en el RAG el 2026-10-03; ver `AGENTS.md` §8):
  - 5.9 = tiempo de traslado al trabajo (ida y vuelta, lun–vie y sáb–dom, h:min). 5.8 = tiempo de trabajo. 5.12 = búsqueda de trabajo, incluidos sus traslados.
  - 5.7 = modalidad: 1 solo presencial, 2 solo virtual, 3 mixta. **FILTRO 5.9: con 5.7 = 2 se salta la 5.9**, así que el traslado de quien trabaja solo a distancia es faltante estructural.
  - 6.1 = cuidado personal "sin hacer otra actividad": 1 dormir (incluye siesta), 2 comer, 3 aseo. 6.21 = convivencia familiar, social y participación ciudadana.
  - El nombre de la columna (`P5_9_*`) aún no se ha visto en un diccionario 2024.

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

### Vercel
- Cuenta Hobby. El proyecto `commute-time-lab` está en el scope `roger-1592` (`team_37NrEuZAkgRsRYTKpMCwC5j9`).
  - El MCP de Vercel da **403 si se pasa `teamId`**. Funciona sin `teamId` (usa el scope por defecto).
- Despliegue por API con archivos inline (no hay conexión con Git ni CLI de Vercel). Se suben solo los fuentes de `web/`, **sin `package-lock.json`** (240 KB), así que Vercel resuelve versiones desde `package.json`. Para redeployar: `create_deployment` con los archivos, o conectar el repo de GitHub.
- Variables en el proyecto (production, preview y development): `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
- `https://commute-time-lab.vercel.app` es público. Los alias por deployment y `…-roger-1592.vercel.app` piden login de Vercel (SSO protection por defecto).

## 6. Preferencias del usuario

- **Idioma:** documentación y conversación en español. UI web, demo y textos guardados en Supabase en inglés (ver `AGENTS.md` §0).
- **Commits:** mensaje breve en inglés y **sin créditos de coautoría** (ver `AGENTS.md`, "Para los commits").
- El usuario entrega el pipeline ENUT. No escribir transformaciones de datos por adelantado.
- La salida del pipeline es `data/processed/analytic_v1.parquet` con su contrato y metadata, **versionados en git** para que Omnigent y el ExperimentRunner los consuman directamente (decisión del 2026-10-03). El ZIP bruto (`data/raw/`) sigue fuera de git y Supabase sigue sin filas individuales. Los requisitos del contrato están en `analysis/enut/README.md`.

## 7. Próximos pasos

1. Recibir `data/processed/analytic_v1.parquet` + contrato + metadata. Revisar que el contrato cubra `analysis/enut/README.md` y escribir contra él `analysis/enut/protocols.py` con `PROTOCOLS = {nombre: fn(dataset_path, parameters) -> {"results", "sample_sizes"}}`. El entorno de Omnigent necesitará las dependencias que usen los protocolos (p. ej. pandas/pyarrow).
2. Configurar el perfil de Databricks y verificar el endpoint del modelo → primera sesión real: `PYTHONPATH=agents:analysis omnigent run omnigent.yaml -p "$(cat initial_state.json)"`.
3. En esa sesión, comprobar que el ASK salta cuando un sub-agente llama a `run_experiment` o `record_decision` ([Decisiones abiertas](AGENTS.md#decisiones-abiertas)).
4. RAG: si el eval o el uso real lo piden, agregar reranker multilingüe o filtro por `source_kind` (ver §3).
5. Decidir sobre `rls_auto_enable()` (ver §2).
6. Redeployar la web cuando cambie `web/`, o conectar el repo de GitHub a Vercel.
