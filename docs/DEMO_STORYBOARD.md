# Storyboard del demo (2 minutos)

Guion para grabar o presentar el demo de **tiemPO** sobre la pantalla de descubrimiento (`/`). La narración va **en inglés** (AGENTS.md §0) y las indicaciones de escena, en español.

## De dónde sale lo que se ve

```
artefactos del repo ──> research_state.json (índice: IDs, relaciones, hashes)
        │                      │ sigue referencias
        └──────────────> normalizeDiscoveryRun()  (web/lib/discovery/model.ts)
                               │
                       DiscoveryRunViewModel
                         ┌─────┴─────┐
                    REPLAY            LIVE
     web/data/discovery-run.json      ?mode=live, lee reports/ en local
     (generado en cada build)
```

- **REPLAY** (por defecto, `/`): lee `web/data/discovery-run.json`. El bundle lo genera `npm run snapshot`, y también el `prebuild` de `npm run build`, a partir de los artefactos **commiteados**. Es una vista derivada, no una fuente científica: guarda la ruta y el SHA-256 de cada fuente.
  - Funciona en Vercel sin Omnigent, sin Databricks y sin la laptop del equipo.
  - Si un artefacto requerido falta o está malformado, el build falla.
- **LIVE** (`/?mode=live`, sin botón; se abre por URL): solo en la máquina donde corren los agentes. El servidor lee `reports/` cada 3 s y normaliza con la misma función. En Vercel muestra el REPLAY con el aviso "Live needs the local lab server".
- Ningún componente tiene cifras, estados ni IDs escritos: todo sale del view model. `npm run test:discovery` lo comprueba (pruebas A–L).

## Cómo se maneja la pantalla

- Desde 2026-10-04 la portada es una **consola**: la pregunta aprobada aparece cargada en un compositor y `Run discovery` reproduce la sesión grabada agente por agente (indicador de trabajo + artefactos guardados → resultado de la etapa). La conclusión (H3 → INCONCLUSIVE y el resumen "Where the investigation stands now") solo aparece al final; los estados fijados por artefactos posteriores se ocultan hasta que su etapa aparece. `Space` pausa, `Esc` o `Skip to end` muestran todo, `/?view=full` abre el registro completo y `/?stage=N` abre la corrida pausada tras la etapa N. Dura unos 45 s. La pantalla hace scroll sola y el inspector sigue a la etapa activa.
- `→` / `←` avanzan o retroceden una etapa y pausan el reloj. `Home` reinicia. `Esc` muestra la cadena completa. Los atajos no se muestran en pantalla: cada botón los nombra en su tooltip.
- `/?stage=N` abre el replay detenido en la etapa N; por ejemplo, `/?stage=7` va directo al estado científico actualizado.
- Las etapas 4, 5 y 6 agrupan varios artefactos como secciones dentro de la misma tarjeta. Una sección sin artefacto se muestra como pendiente ("Not generated yet", "Awaiting human review" o "Experiment not executed"), con su agente y su ruta.
- Antes de grabar, si hay artefactos nuevos commiteados: `cd web && npm run snapshot` y commitear `web/data/discovery-run.json`.

## Reloj del replay

`Play` es un recorrido automático corto (55 s), no la narración de 2 minutos. Para narrar las escenas de abajo, avanza con `→` al ritmo de la voz.

| Tiempo | Etapa | Secciones (leídas del estado) |
|---|---|---|
| 0:00 | 1 · Research question | `initial_state` + `research_state`; H1–H4 con su estado actual |
| 0:04 | 2 · EXP-001 evidence | resultado, forest plot, `INCONCLUSIVE_RANKING` y los pares |
| 0:12 | 3 · Scientific critic | CRIT-EXP-001-001: evidencia, inferencia y preguntas sin probar |
| 0:18 | 4 · Hypotheses and experiment planning | Hypotheses (HYP-005/007/008) · Human review (REV-001) · Experiment planning (PROP-003/005/008/009) |
| 0:26 | 5 · Discovery decision | Director decision (DEC-001) · Engine capability · Decision history (DEC-001…005) · Human approval ✓ (REV-DEC-005-001) |
| 0:36 | 6 · EXP-002 | Formal test (pendientes por grupo + interacción) · Scientific critic (CRIT-EXP-002-002) |
| 0:44 | 7 · Updated scientific state | H3: `UNTESTED` → `INCONCLUSIVE` |
| 0:52 | Cadena completa | — |
| 0:55 | Fin | — |

Las duraciones viven en `HOLD` (`web/app/_components/discovery/DiscoveryView.tsx`). Si cambian aquí, cambian allá.

## Escenas (2:00)

### 0:00–0:15 · El problema
- **En pantalla:** titular (la actualización científica más reciente, leída del artefacto) y etapa 1.
- **Voz:** "In Mexico City and the State of Mexico, a long commute is time that has to come from somewhere. tiemPO asks which part of a worker's own time moves with it — and lets agents run the research, under human approval."

### 0:15–0:35 · Evidencia e incertidumbre (etapas 2 y 3)
- **Voz (frases aprobadas):** "Sleep had the strongest negative point estimate. The ranking across all four outcomes remained inconclusive."
- **Voz:** "The critic agent does not declare a winner: it separates observed evidence from inference and hands on the questions the data cannot settle yet, like sex differences — H3."
- **Prohibido:** "Commuting causes people to lose sleep" · "sleep is definitively the most sacrificed activity".

### 0:35–0:55 · Hipótesis y planeación de experimentos (etapa 4)
- **Voz:** "The hypothesis agent turns that gap into falsifiable hypotheses — to be tested, not findings — and a human approves them for planning. The planner proposes competing experiments: a formal test of the difference between women and men, and an exploratory women-only model that cannot establish a difference on its own."

### 0:55–1:20 · Decisión: Director, motor y aprobación humana (etapa 5)
- **Voz:** "The Director prefers the formal test, but the engine cannot run interactions yet, so it records that it is waiting for a capability instead of settling for the weaker test. The deterministic engine gains formal interaction testing, the Director reassesses — every decision kept — and a human approves the experiment, including what the human did not endorse."

### 1:20–1:45 · EXP-002 (etapa 6)
- **En pantalla:** las pendientes por grupo ("descriptive, not a test") y, aparte, la **prueba formal**: la diferencia de pendientes con su intervalo.
- **Voz:** "EXP-002 runs on the same deterministic engine. The female slope point estimate is more negative than the male one — but the formal test is the interaction, and its interval includes zero."
- **Prohibido:** "No sex difference" · "Men and women are the same" · "Women lose more sleep because of commuting".

### 1:45–2:00 · Estado científico actualizado (etapa 7)
- **En pantalla:** la tarjeta final: H3 · Sex Heterogeneity, `UNTESTED` → `INCONCLUSIVE`.
- **Voz:** "So the lab updates its state: H3 moves from untested to inconclusive. It ran the right experiment, got evidence that does not settle the question, and recorded exactly that — instead of inventing certainty. Every number on this screen comes from a reproducible artifact you can open."
- **Ojo:** el 10× del README es una meta, no una medición; no mencionarlo como resultado.
