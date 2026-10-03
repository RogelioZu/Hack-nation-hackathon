# Pipeline ENUT (pendiente)

El pipeline ENUT completo lo proporciona el usuario. Mientras tanto, no escribir transformaciones basadas en supuestos.

## Salida: `data/processed/analytic_v1.parquet`

El pipeline lee el ZIP bruto localmente (`data/raw/`, ignorado por git) y escribe **un** dataset analítico limpio y validado, versionado en git junto con su contrato y su metadata como archivos hermanos con el mismo nombre base (por ejemplo `analytic_v1.contract.json` y `analytic_v1.metadata.json`):

```
data/processed/
  analytic_v1.parquet
  analytic_v1.<contrato>
  analytic_v1.<metadata>
```

- `describe_dataset` (`agents/commute_lab/tools.py`) devuelve a los agentes todos los archivos `analytic_v1.*` menos el parquet (los JSON ya parseados, el resto como texto) y el `sha256` del parquet. Nunca devuelve filas.
- `run_experiment` calcula el `sha256` del parquet, lo guarda en `experiment_runs.dataset_hash` y pasa **ese mismo archivo** al protocolo.
- Una versión nueva es un archivo nuevo (`analytic_v2.parquet`), no una sobrescritura: los runs viejos se reproducen por su hash.

### Qué deben decir el contrato y la metadata

El formato lo define el pipeline. Para que el Data Steward, el runner y el crítico cumplan `/AGENTS.md` §2, deben cubrir al menos:

- **Por columna:** nombre, tipo, unidad (las actividades y el traslado en **minutos semanales**), descripción y pregunta o variable ENUT de origen (p. ej. pregunta 5.9 del cuestionario 2024 para el traslado).
- **Diseño muestral:** columnas de `FAC_PER`, `UPM_DIS` y `EST_DIS`, más entidad (CDMX `09`, Edomex `15`) y sexo.
- **Cohorte:** filtros aplicados y `n` antes y después de cada exclusión.
- **Faltantes:** porcentaje por columna y cómo se trataron los faltantes estructurales. Ejemplo: con 5.7 = 2 (solo virtual) la persona salta la 5.9, así que su traslado no es un cero medido.
- **Medición:** si los cuidados incluyen cuidado pasivo o simultáneo; sueño separado del resto del cuidado personal (6.1) y cuidados (6.11–6.15) separados de convivencia (6.21).
- **Procedencia:** año ENUT, URL y hash del ZIP de origen, versión (commit) del pipeline, fecha de generación, y fuente y licencia de INEGI.

## Protocolos cerrados

Van en `analysis/enut/protocols.py`, que es donde `run_experiment` los busca. Se escriben **contra el contrato**, cuando exista:

```python
PROTOCOLS = {
    "weighted_means_by_group": fn,   # fn(dataset_path: Path, parameters: dict) -> {"results": ..., "sample_sizes": ...}
    "wls_commute_by_sex": fn,
}
```

`results` sigue el contrato de `/AGENTS.md` §5. `dataset_hash` y `code_version` los pone el runner.
