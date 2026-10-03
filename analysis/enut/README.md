# Pipeline ENUT (pendiente)

El pipeline ENUT completo lo proporciona el usuario. Mientras tanto, no escribir transformaciones basadas en supuestos.

Cuando llegue, debe:
- leer el ZIP bruto localmente (`data/`, en `.gitignore`). Las filas individuales nunca salen de esta máquina.
- exponer los protocolos cerrados en `analysis/enut/protocols.py`, que es donde `run_experiment` (`agents/commute_lab/tools.py`) los busca:
  ```python
  PROTOCOLS = {
      "weighted_means_by_group": fn,   # fn(parameters: dict) -> {"results": ..., "sample_sizes": ..., "dataset_hash": ...}
      "wls_commute_by_sex": fn,
  }
  ```
- escribir una fila en `experiment_runs` por ejecución, con `dataset_hash`, `code_version`, `parameters`, `sample_sizes`
  y `results` siguiendo el contrato de `/AGENTS.md` §5.
