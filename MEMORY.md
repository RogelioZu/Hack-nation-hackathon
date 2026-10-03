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
| Ingesta RAG (2 PDFs INEGI ENUT 2024) | ✅ 613 pasajes con embedding |
| Web (`/` y `/research/[id]`) leyendo Supabase real | ✅ Verificado con `next dev`; `npm run build` pasa |
| Pipeline ENUT (`analysis/enut/`) | ⏳ **Pendiente: lo entrega el usuario** |
| `run_experiment` y protocolos cerrados | ⏳ Depende del pipeline ENUT |
| Agentes Omnigent (`agents/`) | ⏳ No iniciado (no se ha hecho el preflight de acceso) |
| Papers de OpenAlex en el corpus | ⏳ No iniciado |
| Despliegue en Vercel | ⏳ No iniciado |
| Commit inicial en `main` | ✅ Hecho (no se ha hecho push a ningún remoto) |

## 2. Infraestructura

### Supabase
- Proyecto del hackathon: **`xnbruiprrxradfidoleu`** (us-east-1, Postgres 17). URL: `https://xnbruiprrxradfidoleu.supabase.co`.
- ⚠️ La cuenta tiene **otro** proyecto, "Finding out" (`fnveucrdccqwzovptxqa`), que **no es de este hackathon**. No tocarlo.
- El acceso se hace por el **MCP de Supabase**. Hubo que reautenticarlo con `/mcp` para que viera este proyecto. La **CLI `supabase` no tiene sesión iniciada**, así que `supabase db push` y `supabase link` no funcionan todavía.
- Migraciones aplicadas con `apply_migration` del MCP. Versiones remotas: `20261003210503_extensions`, `20261003210519_core`, `20261003210530_rag`, `20261003210538_rls`.
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

- Corpus en `analysis/rag/corpus.json`. Por ahora tiene el diseño conceptual de ENUT 2024 (564 pasajes) y el diseño muestral (49 pasajes). Los PDFs se guardan en `analysis/.cache/`, con nombre igual al `sha1(url)`.
- La primera ejecución descarga el modelo e5-small (~470 MB) a la caché de HuggingFace.
- `pypdf` muestra advertencias de "fontTools is required…". Son inofensivas: el texto se extrae bien.
- QA del 2026-10-03 (5 consultas):
  - ✅ Diseño muestral (UPM, estratos, factor de expansión).
  - ✅ Definición de convivencia (p. 67).
  - 🟡 Cuidados pasivos.
  - 🟡 "Traslado al trabajo": devuelve la semana de referencia, pero no la pregunta concreta.
  - ❌ Consulta en inglés "weekly time spent sleeping".
- **Debilidades conocidas:**
  1. El corpus está en español. Con consultas en inglés solo funciona la parte semántica, así que **el agente de evidencia debe consultar en español**.
  2. Las páginas del cuestionario anexo del diseño conceptual (pp. ~95–115) son tablas de formulario con texto repetido ("REGISTRE EL CÓDIGO…") que contaminan los resultados.
- **Mejora sugerida, aún no aplicada:** ingerir el cuestionario como fuente aparte (`kind = 'questionnaire'`) fragmentada por pregunta, y excluir o etiquetar esas páginas del diseño conceptual.
- Los `sources` demo del seed (`…0a1`, `…0a2`) no tienen pasajes. Solo existen para la web.

## 4. Dataset ENUT

- `MEX-INEGI.ESD3.04-ENUT-2019.xml`, en la raíz, es el **codebook DDI de ENUT 2019**: metadatos de 1300 variables y 8 tablas. **No son microdatos.** El usuario pidió **ignorarlo** porque entregará el pipeline completo. Se dejó **fuera del commit a propósito**.
- Hallazgo del codebook 2019, ya documentado en `AGENTS.md` §8:
  - `P5_4_*` es el traslado al trabajo; `P5_9_*` es el tiempo buscando trabajo.
  - `ENT` vale `09` para CDMX y `15` para Edomex.
  - `TMODULO_tradicional` tiene 71,404 casos a nivel nacional.
- CONTEXT.md asume ENUT **2024**. El año definitivo lo fija el pipeline del usuario.

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

## 6. Preferencias del usuario

- **Idioma:** documentación y conversación en español. UI web, demo y textos guardados en Supabase en inglés (ver `AGENTS.md` §0).
- **Commits:** mensaje breve en inglés y **sin créditos de coautoría** (ver `AGENTS.md`, "Para los commits").
- El usuario entrega el pipeline ENUT. No escribir transformaciones de datos por adelantado.

## 7. Próximos pasos

1. Recibir el pipeline ENUT → adaptarlo a protocolos cerrados → `run_experiment` escribe en `experiment_runs` con el contrato de resultados.
2. Preflight de Omnigent (administrado vs. código abierto) → YAML de los 4 roles en `agents/`.
3. Mejorar el corpus RAG: cuestionario por pregunta y papers de OpenAlex.
4. Decidir sobre `rls_auto_enable()` (ver §2).
5. Desplegar en Vercel con las variables de `web/.env.local`.
