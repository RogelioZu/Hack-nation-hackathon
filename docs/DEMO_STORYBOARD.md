# Storyboard del demo (2 minutos)

Guion para grabar o presentar el demo de **tiemPO** sobre la pantalla de descubrimiento (`/`). La narración va **en inglés** (AGENTS.md §0); las indicaciones de escena, en español.

## Cómo se maneja la pantalla

- **REPLAY** (por defecto, `/`): muestra los artefactos commiteados. Funciona sin agentes y en Vercel.
  - `Start discovery` (o `Space`) revela las etapas con el reloj de abajo. La pantalla hace scroll sola y el inspector sigue a la etapa activa.
  - Las etapas que aún esperan agentes (hoy 5–9) se agrupan en una sola banda, **Next in the loop**: muestra qué preguntas abiertas recibe el siguiente agente, las direcciones que listó el motor (sin elegir) y cada etapa pendiente con su agente y ruta. Cuando llega el artefacto de una etapa, esa etapa sale de la banda y vuelve a ser tarjeta.
  - `→` / `←` avanzan o retroceden una etapa; la banda cuenta como un solo paso (pausan el reloj). `Home` reinicia (no hay botón: así la barra queda limpia). `Esc` muestra la cadena completa. Los atajos no se muestran en pantalla: cada botón los nombra en su tooltip.
  - El titular de la portada es la frase del hallazgo leída del `result.json` más reciente, con su chip y la línea de procedencia (`n`, commit del snapshot).
  - `/?stage=4` abre el replay detenido en la etapa 4 (útil para ensayar un tramo).
- **LIVE** (`/?mode=live`, sin botón en la interfaz; se abre por URL): solo en la máquina donde corre Omnigent. El servidor lee `reports/` cada 3 s y marca como **New** cada artefacto que llega.
- Antes de grabar, regenerar el snapshot si hay artefactos nuevos commiteados: `cd web && npm run snapshot` (solo incluye archivos versionados en git).

## Reloj del replay

`Play` es un recorrido automático corto, no la narración de 2 minutos. Con los artefactos de hoy dura **33 s**. Para narrar las escenas de abajo, avanza con `→` al ritmo de la voz (o abre una etapa con `/?stage=N`).

| Tiempo | Etapa que se revela | Artefacto |
|---|---|---|
| 0:00 | 1 · Research question | `initial_state.json` |
| 0:04 | 2 · First experiment | `EXP-001 spec` + `EXP-001 validation` |
| 0:08 | 3 · Evidence | `EXP-001 result` |
| 0:16 | 4 · Scientific critique | `CRIT-EXP-001-001` |
| 0:22 | Next in the loop (5–9 pendientes) | traspaso de la crítica + direcciones del motor |
| 0:30 | Cadena completa | — |
| 0:33 | Fin | — |

Las marcas se calculan a partir de las etapas registradas: cada etapa dura lo que dice `HOLD` en `web/app/_components/discovery/DiscoveryView.tsx` (pregunta 4 s, experimento 4 s, evidencia 8 s, crítica 6 s, etapas posteriores 3 s). La banda dura 8 s y la vista completa 3 s. Con las 9 etapas registradas, el reloj vuelve a 0:00, 0:04, 0:08, 0:16, 0:22, 0:25, 0:28, 0:31, 0:34 · 0:37 · 0:40. Si cambian aquí, cambian allá.

## Escenas

### 0:00–0:20 · El problema

- **En pantalla:** banner azul y etapa 1 (pregunta, población, hipótesis H1–H4 pre-registradas).
- **Voz:** "In Mexico City and the State of Mexico, a long commute costs more than travel time. The question is which part of a worker's own time moves with it: sleep, personal hygiene, conversation at home, or leisure."
- **Ojo:** no decir "costs" en sentido causal sobre los resultados; aquí se habla del problema, no del hallazgo.

### 0:20–0:40 · El enfoque: un laboratorio científico agéntico

- **En pantalla:** la etapa 1 sigue activa; señalar el chip `analytic_v1` y el inspector.
- **Voz:** "tiemPO is an agentic lab. Omnigent coordinates specialist agents, but no agent computes a number: every figure comes from a deterministic engine that runs each experiment twice on ENUT 2024 microdata. Every card you will see is read from a real artifact with an ID."

### 0:40–1:00 · EXP-001 y la evidencia real

- **En pantalla:** etapa 2 (`EXP-001`: identical on re-run, dataset hash unchanged, requires human review) y a 0:48 la etapa 3 con el forest plot.
- **Voz (frases aprobadas, no cambiarlas):**
  - "Sleep had the strongest negative point estimate."
  - "Five additional weekday commuting hours were associated with about 49 fewer weekday sleep minutes in the adjusted model."
  - "The ranking across all four outcomes remained inconclusive."
- **Prohibido:** "Commuting causes people to lose 49 minutes of sleep." · "Sleep is definitively the activity most sacrificed."
- Las tres frases salen del artefacto: si `result.json` cambiara, la pantalla cambia y este guion se revisa.

### 1:00–1:25 · El científico de IA responde a la incertidumbre

- **En pantalla:** etapa 4 (`CRIT-EXP-001-001`, veredicto `UNCERTAIN`), luego 5, 6 y 7 (o la banda **Next in the loop** si aún no existen).
- **Voz (lo que ya existe):** "Instead of declaring a winner, the critic agent flags what the evidence cannot settle: it is observational, the ranking is uncertain, the variance is an approximation, and sex and household differences, H3 and H4, are untested."
- **Voz (depende de artefactos futuros):**
  - Si existen hipótesis: "From that critique, the hypothesis agent proposes {código H5…}: {statement del artefacto}." Leer el texto de la tarjeta, no parafrasearlo con más fuerza.
  - Si existen candidatos: "The planner proposes {N} competing experiments; {A} fits the current engine contract, {B} would need a contract revision."
  - Si existe la selección: "The Director chooses {label} for expected learning, not for the chance of a significant result: {rationale del artefacto}."
  - **Si todavía no existen:** "These stages are waiting for the agents. The critique already hands them four untested questions; the interface shows the rest as pending instead of inventing them."

### 1:25–1:45 · Nuevo experimento → decisión actualizada

- **En pantalla:** etapa 8 (nuevo `EXP-NNN`, su forest plot y su crítica) y etapa 9 (decisión con regla R1/R2/R3 y siguiente prueba).
- **Voz (plantilla):** "The selected spec runs through the same deterministic engine as {EXP-NNN}. {Primera frase de la tarjeta de evidencia.} The critic reviews it, and the Director records an updated decision under rule {Rx}: {next_test del artefacto}."
- **Si todavía no existen:** "When the run is approved, its result and the updated decision land here automatically, with the same provenance."
- No llenar cifras ni conclusiones de EXP-002 hasta que exista su `result.json`.

### 1:45–2:00 · Por qué acelera el descubrimiento

- **En pantalla:** cadena completa (`Esc` o el reloj a 1:45); inspector mostrando la ruta y el SHA-256 del último artefacto.
- **Voz:** "The loop goes from a question to a critique-driven next experiment without anyone retyping a number, and every step is auditable: the file, its hash, the agent and the model that produced it. That is how agents can speed up science without overstating it."
- **Ojo:** el 10× del README es una meta, no una medición. No mencionarlo como resultado.

## Pendientes que dependen de los agentes

| Etapa | Qué falta | Quién lo produce | Dónde aparece |
|---|---|---|---|
| 5 · New hypotheses | hipótesis H5+ motivadas por la crítica | `hypothesis_agent` · `save_hypothesis` | `reports/discovery/<session>/hypotheses/` |
| 6 · Candidate experiments | ≥2 candidatos con factibilidad y verificación en seco | `experiment_planner` · `save_proposals` | `reports/discovery/<session>/candidates/` |
| 7 · Selected experiment | elección y justificación del Director | `discovery_director` · `select_candidate` | `reports/discovery/<session>/decisions/` |
| 8 · New evidence | `EXP-NNN` ejecutado y su crítica | `experiment_runner` · `run_experiment` + `scientific_critic` | `experiments/EXP-NNN/`, `reports/experiments/EXP-NNN/`, `…/critiques/` |
| 9 · Updated decision | decisión con regla y siguiente prueba | `discovery_director` · `record_decision` | `reports/discovery/<session>/decisions/` |
