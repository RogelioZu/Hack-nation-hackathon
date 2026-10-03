# Herramientas de los agentes Omnigent

La configuración de los 7 agentes vive en la raíz: `omnigent.yaml` (agentes, políticas y handoffs) e `initial_state.json` (Shared Research State inicial). La arquitectura, el esquema JSON y su relación con Supabase están en `/AGENTS.md` §7.

Esta carpeta contendrá:

- `tools/`: wrappers delgados en Python sobre `analysis/`, usados por los agentes. Escriben en Supabase con service_role y registran cada llamada en `agent_events`.
  - `search_evidence` (RAG en Supabase) y `search_openalex` → Literature Agent
  - `inspect_enut_variables` y `get_dataset_profile` → Data Steward
  - `save_hypothesis` → Hypothesis Agent
  - `save_proposals` → Experiment Planner
  - `run_experiment` (solo protocolos cerrados) → Experiment Runner
  - `read_run` y `record_decision` → Scientific Critic y Discovery Director
  - `log_event` → todos
- `policies.md`: qué puede y qué no puede hacer cada agente (sin SQL ni shell arbitrario sobre los datos; aprobación humana para ejecuciones y decisiones finales).

Antes de implementar, revisar las Decisiones abiertas de `/AGENTS.md`: varias afectan a estas herramientas.
