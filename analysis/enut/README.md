# Pipeline ENUT (pendiente)

El pipeline ENUT completo lo proporciona el usuario. Mientras tanto, no escribir transformaciones basadas en supuestos.

Cuando llegue, debe:
- leer el ZIP bruto localmente (`data/`, en `.gitignore`). Las filas individuales nunca salen de esta máquina.
- exponer protocolos cerrados para `run_experiment` (p. ej. `weighted_means_by_group`, `wls_commute_by_sex`).
- escribir una fila en `experiment_runs` por ejecución, con `dataset_hash`, `code_version`, `parameters`, `sample_sizes`
  y `results` siguiendo el contrato de `/AGENTS.md` §5.
