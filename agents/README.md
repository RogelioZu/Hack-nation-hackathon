# Herramientas de los agentes Omnigent

El spec de los 7 agentes está en la raíz, en `omnigent.yaml`: el Discovery Director es el agente raíz y los 6 especialistas son sub-agentes. El estado inicial está en `initial_state.json`. La arquitectura, el esquema JSON y su relación con Supabase están en `/AGENTS.md` §7.

El paquete `commute_lab/` (no se llama `agents` para no chocar con el SDK `openai-agents`) contiene:

- `tools.py`: 15 function tools. Escriben en Supabase con service_role, registran cada paso en `agent_events` y devuelven JSON. Las cifras solo salen del motor (`src/experiments/`), que corre por subproceso en `.venv-experiments` (o `EXPERIMENT_PYTHON`).

  | Tool | Quién la usa |
  |---|---|
  | `create_project`, `set_project_status`, `log_event`, `register_experiment`, `select_candidate`, `record_decision` | Discovery Director |
  | `read_experiment_result` | Director, Scientific Critic, Experiment Runner |
  | `save_critique` | Scientific Critic (veredicto VALID · UNCERTAIN · REQUIRES_REVISION · REQUIRES_HUMAN_REVIEW) |
  | `search_evidence`, `search_openalex`, `search_web` (Bright Data, opcional) | Literature Agent (y Data Steward: `search_evidence`) |
  | `save_hypothesis` | Hypothesis Agent (código estable H5+, evidencia / inferencia / hipótesis nueva) |
  | `describe_dataset` | Data Steward y Experiment Planner |
  | `save_proposals` | Experiment Planner (≥2 candidatos; los factibles con `ExperimentSpec` verificado en seco) |
  | `run_experiment` | Experiment Runner (solo la propuesta elegida; asigna `EXP-NNN`) |

  Los objetos completos (críticas, hipótesis, candidatos, decisiones) se guardan también en `reports/discovery/<project_id>/`.

- `policies.py`: `ask_before_run` pide aprobación humana (ASK) antes de `run_experiment` y `record_decision`.

Cada sub-agente declara sus propias tools en `omnigent.yaml` (anclas YAML): Omnigent 0.16 no resuelve `inherit` en sub-agentes inline.

Las tools importan `db` y `rag` desde `analysis/`. Por eso Omnigent se ejecuta desde la raíz con `PYTHONPATH=agents:analysis` (ver `/AGENTS.md` §10).
