# Agentes Omnigent (siguiente fase)

Los roles, herramientas y salidas estructuradas están definidos en `/AGENTS.md` §7. Esta carpeta contendrá:

- `coordinator.yaml`, `evidence.yaml`, `method.yaml`, `critic.yaml` (YAML de agentes Omnigent)
- `policies.md`: qué puede y qué no puede hacer cada agente (sin SQL ni shell arbitrario sobre los datos; aprobación humana para ejecuciones y decisiones finales)
- `tools/`: wrappers delgados en Python sobre `analysis/` (`search_evidence`, `run_experiment`, `record_decision`, `log_event`, ...)
