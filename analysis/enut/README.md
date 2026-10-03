# Pipeline ENUT (cerrado; se construyó fuera de este directorio)

El pipeline ENUT 2024 se construyó y validó en otro entorno, por fases con aprobación humana (1 auditoría → 2A staging → 2B dataset canónico → 3 motor de experimentos). **No reconstruirlo aquí, no reinterpretar los datos crudos y no volver a limpiar datos** salvo que una validación científica explícita falle.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Dataset canónico (`APPROVED_FOR_EXPERIMENTS`, n = 2,563) | `data/processed/analytic_v1.parquet` |
| Staging histórico de la fase 2A y CSV crudos | `data/interim/staging_v1.parquet`, `data/raw/enut_2024/` (solo locales, ignorados por git; el motor no los lee) |
| Auditorías y validaciones de las fases 1, 2A y 2B | `reports/audit/` |
| Cuestionario y diccionario DDI archivados | `metadata/official/` |
| Definiciones de variables y población | `docs/DATA_CONTRACT.md` |
| Decisiones científicas por fase | `docs/SCIENTIFIC_PROTOCOL.md` |
| Procedencia, linaje, faltantes y validaciones | `metadata/analytic_v1_manifest.json` |
| Motor de experimentos | `src/experiments/` (contrato en `docs/EXPERIMENT_ENGINE.md`) |

## Protocolos cerrados: reemplazados

La idea original era escribir aquí `protocols.py` con `PROTOCOLS = {"weighted_means_by_group": fn, "wls_commute_by_sex": fn}`. **Ya no se va a escribir.** Ahora el único camino computacional es el motor determinista:

```
ExperimentSpec → src.experiments.runner.run_experiment(spec) → ExperimentResult
```

La tool `run_experiment` de `agents/commute_lab/tools.py` todavía busca `analysis/enut/protocols.py`. Hay que adaptarla para que llame al motor (ver `AGENTS.md` §7.4).
