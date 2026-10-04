# Shared Research State

Memoria científica estructurada del ciclo de descubrimiento. Se **reconstruye** de forma determinista a partir de artefactos commiteados, nunca a partir de la memoria conversacional de un LLM ni de una base de datos.

- Código: `agents/commute_lab/research_state.py` (solo librería estándar; lo puede importar el entorno de Omnigent).
- CLI: `python scripts/build_research_state.py`.
- Tests: `PYTHONPATH=agents python -m unittest discover -s agents/tests`. Están fuera de `tests/` porque el validador del motor corre esa carpeta como su propia suite.

## Fuentes de verdad y salida generada

| Qué | Dónde | ¿Fuente? |
|---|---|---|
| Resultados del motor | `reports/experiments/EXP-NNN/{spec,result,validation}.json` | Sí. Solo se indexan si `validation.json` es `PASS` y su `result_sha256` coincide con los bytes de `result.json` |
| Artefactos de agentes | `reports/discovery/<workspace>/<kind>/<ID>.json` | Sí. Un archivo por objeto, append-only |
| Dataset | `metadata/analytic_v1_manifest.json` + `metadata/analytic_v1_experiment_approval.json` | Sí |
| Hipótesis pre-registradas H1–H4 | `docs/EXPERIMENT_PROTOCOL.md` (encabezados `### Hn — …`) | Sí |
| Pregunta de investigación | `initial_state.json` | Sí |
| **Snapshot del estado** | `reports/discovery/<workspace>/research_state.json` | **No.** Es generado (lleva `_generated`), nunca se edita a mano y el loader nunca lo lee como fuente |

`<workspace>` es `local` para el ciclo basado en archivos. Las carpetas con UUID que escribe `tools.py` (ciclo con Supabase) son otros workspaces.

`<kind>` ∈ `evidence`, `critiques`, `hypotheses`, `candidates`, `decisions`. Las carpetas desconocidas se ignoran con una advertencia `UNKNOWN_KIND`, así que agregar un tipo nuevo no rompe el estado.

## Regla de cifras

El estado **no copia cifras científicas**. Cada evidencia guarda `artifact` + `pointer` (JSON Pointer) hacia el valor en su fuente; `resolve(state, evidence_id)` lo lee de ahí. Los textos de `limitations` sí se copian, siempre con su `pointer`. Los tests comprueban que el estado no contiene ningún float.

## Contrato para escribir artefactos (Hypothesis Agent, Planner, Director)

Usar `commute_lab.research_state.save_artifact(kind_dir, payload)`. Toma el ID del payload, lo usa como nombre de archivo y **nunca sobrescribe**: si el archivo existe, lanza `FileExistsError`.

Campo de ID por tipo (el primero es el canónico en el estado):

| `kind` | Campo de ID | Ejemplo de ID |
|---|---|---|
| `evidence` | `evidence_id` | `EV-001` |
| `critiques` | `critique_id` | `CRIT-EXP-001-001` (obligatorio: `CRIT-<experiment_id>-NNN`) |
| `hypotheses` | `hypothesis_id` | `HYP-001` |
| `candidates` | `candidate_id` (o `proposal_id`) | `CAND-001-A` |
| `decisions` | `decision_id` | `DEC-001` |

Los IDs deben ser únicos en todo el estado (también frente a `EXP-NNN`, `H1`–`H4` y los IDs de evidencia derivados) y seguros como nombre de archivo.

### Referencias reconocidas

Una referencia es un campo con un ID. Las listas pueden tener IDs o objetos con `evidence_id`/`id`/`ref`. Todo campo con estos nombres se valida y se convierte en una arista del grafo de trazabilidad:

| Artefacto | Campos | Relación | Debe apuntar a |
|---|---|---|---|
| critique | `experiment_id`, `provenance.source_experiment_id` | `interprets` | experimento |
| hypothesis | `motivated_by_critique_id`, `source_critique_id(s)`, `critique_id(s)` | `motivated_by` | crítica |
| hypothesis, candidate | `evidence_ids`, `supporting_evidence_ids`, `opposing_evidence_ids`, `evidence_refs`, `existing_evidence[].evidence_id` | `cites` | evidencia, crítica o experimento |
| hypothesis | `protocol_hypothesis`, `protocol_hypothesis_ids`, `parent_hypothesis_ids` | `refines` | hipótesis (p. ej. `H3`) |
| candidate | `hypothesis_id`, `hypothesis_ids`, `tests_hypothesis_ids` | `tests` | hipótesis |
| decision | `selected_candidate_id`, `candidate_id`, `proposal_id` | `selects` | candidato |
| decision | `considered_candidate_ids`, `rejected_candidate_ids` | `considers` | candidato |
| decision | `based_on_experiment_id`, `based_on_critique_id`, `based_on_ids` | `based_on` | evidencia, crítica, experimento o hipótesis |
| decision | `experiment_id`, `resulting_experiment_id` | `executed_as` | `EXP-NNN`, que puede no existir aún (advertencia `PENDING_EXPERIMENT`) |

Los campos con otros nombres no se validan ni se enlazan. Un UUID que no está en el índice (fila de Supabase) da la advertencia `EXTERNAL_REFERENCE`, no un error.

### IDs de evidencia derivados (para citar desde hipótesis)

| ID | Apunta a |
|---|---|
| `EXP-001/estimates/<model_id>` (p. ej. `adjusted:sleep_weekday_min`) | `/estimates/i` de `result.json` |
| `EXP-001/ranking` | `/ranking` |
| `EXP-001/sensitivity/<name>` | `/sensitivity_results/i` |
| `EXP-001/hypotheses/H1` | evaluación del motor de H1 |
| `CRIT-EXP-001-001/evidence/<n>` (1-based) | `/evidence_summary/n-1` de la crítica |

Ejemplo mínimo de hipótesis:

```json
{
  "hypothesis_id": "HYP-001",
  "statement": "…",
  "status": "proposed",
  "motivated_by_critique_id": "CRIT-EXP-001-001",
  "evidence_ids": ["CRIT-EXP-001-001/evidence/5", "EXP-001/ranking"],
  "protocol_hypothesis": "H3"
}
```

## Estado

`research_id`, `research_question`, `dataset` (`version`, `population_n`, hash, aprobación), `evidence`, `critiques`, `hypotheses` (H1–H4 del protocolo con `evaluated_in`, más las de agentes), `candidate_experiments`, `experiments` (con `critiques` y `selected_by` inversos), `decisions`, `limitations`, `links` (aristas `from → to` con relación y campo), `next_action`, `provenance` (hash de cada entrada e `inputs_sha256`) y `validation`.

`next_action` es contabilidad, no ciencia: indica la **etapa** que falta para el último experimento (`critique` → `hypotheses` → `candidate_experiments` → `decision` → `run_experiment`) y quién la ejecuta. Nunca elige un candidato ni un experimento. También lista lo que sigue en `REQUIRES_HUMAN_REVIEW`.

## Validaciones

Errores (el estado queda inválido y el snapshot no se escribe):

| Código | Caso |
|---|---|
| `DUPLICATE_ID` | Dos objetos con el mismo ID |
| `MISSING_REFERENCE` / `MISSING_EVIDENCE` | Referencia a un objeto que no existe (`MISSING_EVIDENCE` si es una cita) |
| `WRONG_REFERENCE_KIND` | El ID existe pero es de otro tipo (p. ej. una decisión que "selecciona" una hipótesis) |
| `INVALID_EXPERIMENT_ID` | Carpeta o referencia que no es `EXP-NNN`, o spec/result con otro ID |
| `INVALID_CRITIQUE_ID` | Crítica que no es `CRIT-<experiment_id>-NNN` |
| `UNVALIDATED_RESULT` | `result.json` sin `validation.json` PASS o con otros bytes |
| `SOURCE_CHANGED` | Crítica escrita para otros bytes de `result.json` |
| `DATASET_VERSION_MISMATCH` | Spec, resultado, crítica, manifiesto y aprobación no coinciden en versión o hash |
| `SPEC_MISMATCH` | `experiments/EXP-NNN/spec.json` difiere del spec publicado |
| `ID_FILENAME_MISMATCH` / `MISSING_ID` | El ID del payload no coincide con el nombre del archivo, o falta |
| `ACCIDENTAL_OVERWRITE` / `ARTIFACT_REMOVED` | Un artefacto indexado en el snapshot anterior cambió de bytes o desapareció. Si fue intencional: `--allow-changed <ruta>` |

Advertencias: `EMPTY_WORKSPACE`, `UNKNOWN_KIND`, `UNLINKED_HYPOTHESIS` (hipótesis sin crítica), `PENDING_EXPERIMENT` y `EXTERNAL_REFERENCE`.

No juzga el contenido científico; eso es trabajo del crítico y de la revisión humana.

## Comandos

```bash
python scripts/build_research_state.py                    # valida, escribe el snapshot si cambió, imprime resumen
python scripts/build_research_state.py --check            # solo valida
python scripts/build_research_state.py --print            # imprime el estado completo
python scripts/build_research_state.py --trace DEC-001    # de qué depende y quién lo usa
```

Preguntas de trazabilidad y cómo se responden:

- ¿Qué experimento produjo esta evidencia? `--trace <evidence_id>` (relación `part_of`).
- ¿Qué crítica la interpretó? `experiments[].critiques` o `--trace EXP-NNN` (`used_by`).
- ¿Qué hipótesis salieron de esa crítica? `--trace CRIT-…` (`motivated_by`).
- ¿Qué propuesta salió de cada hipótesis? `--trace HYP-…` (`tests`).
- ¿Por qué se eligió un experimento? `--trace DEC-…` y el `rationale` del artefacto de la decisión.
