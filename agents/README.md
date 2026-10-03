# Herramientas de los agentes Omnigent

El spec de los 7 agentes está en la raíz, en `omnigent.yaml`: el Discovery Director es el agente raíz y los 6 especialistas son sub-agentes. El estado inicial está en `initial_state.json`. La arquitectura, el esquema JSON y su relación con Supabase están en `/AGENTS.md` §7.

El paquete `commute_lab/` (no se llama `agents` para no chocar con el SDK `openai-agents`) contiene:

- `tools.py`: 10 function tools. Escriben en Supabase con service_role, registran cada paso en `agent_events` y devuelven JSON.

  | Tool | Quién la usa |
  |---|---|
  | `create_project`, `set_project_status`, `log_event` | Discovery Director |
  | `search_evidence`, `search_openalex` | Literature Agent (y Data Steward: `search_evidence`) |
  | `save_hypothesis` | Hypothesis Agent |
  | `save_proposals` | Experiment Planner (exige ≥2 propuestas y protocolos cerrados) |
  | `run_experiment`, `read_run` | Experiment Runner |
  | `read_run`, `record_decision` | Scientific Critic (exige una regla R1–R3 y un run real del proyecto) |

- `policies.py`: `ask_before_run` pide aprobación humana (ASK) antes de `run_experiment` y `record_decision`.

Las tools importan `db` y `rag` desde `analysis/`. Por eso Omnigent se ejecuta desde la raíz con `PYTHONPATH=agents:analysis` (ver `/AGENTS.md` §10).
