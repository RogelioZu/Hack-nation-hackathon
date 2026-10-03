# Phase 2B — canonical analytic validation

Estado técnico: **EXPERIMENT_READY**. **Aprobación humana final pendiente.** No se ejecutaron modelos, pruebas H1–H4 ni EXP-001.

## Población

| Filtro acumulativo | n |
|---|---:|
| raw_tmodulo | 74,053 |
| geographic_09_15 | 4,754 |
| geographic_age_domain | 3,659 |
| active_workers_in_domain | 2,563 |
| after_absent_exclusion | 2,563 |
| resolved_commute | 2,563 |

Diferencia frente a la población aprobada: **0 personas**. No se excluyen ceros, extremos ni indicadores de menores desconocidos.

## Comprobación anterior al build

Registrada antes de escribir Parquet: 2026-10-03T22:03:55.985803+00:00 (UTC).

- Trabajo entre semana igual a cero: **34**.
- Traslado igual a cero: **190** = **144 observados** + **46 virtuales estructurales**.
- Casos conservados con review_zero_work / review_zero_commute.

| Trabajo=0 | Traslado=0 | n |
|---|---|---:|
| False | False | 2373 |
| False | True | 156 |
| True | False | 0 |
| True | True | 34 |

Las 34 personas con trabajo entre semana cero reportan trabajo en fin de semana; se conserva la definición de actividad de la semana de referencia. No se añade un filtro de trabajo positivo entre semana.

## Once componentes de ocio

Para cada indicador: 1 requiere un par válido; 2 con ambos campos vacíos implica cero estructural. Cualquier valor semántico no resuelto, parcial, inválido o incompatible detiene la publicación. Suma completa, sin ignorar faltantes.

| Componente | Indicador | Horas | Minutos | Observados | Ceros estructurales |
|---|---|---|---|---:|---:|
| sport | P6_18 | P6_18A_1 | P6_18A_2 | 857 | 1706 |
| arts | P6_19_1 | P6_19A_1_1 | P6_19A_1_2 | 93 | 2470 |
| games_hobbies | P6_19_2 | P6_19A_2_1 | P6_19A_2_2 | 304 | 2259 |
| entertainment_venues | P6_20_1 | P6_20A_1_1 | P6_20A_1_2 | 341 | 2222 |
| cultural_venues | P6_20_2 | P6_20A_2_1 | P6_20A_2_2 | 238 | 2325 |
| screen_entertainment | P6_22_1 | P6_22A_1_1 | P6_22A_1_2 | 1921 | 642 |
| audio_entertainment | P6_22_2 | P6_22A_2_1 | P6_22A_2_2 | 791 | 1772 |
| recreational_reading | P6_22_3 | P6_22A_3_1 | P6_22A_3_2 | 560 | 2003 |
| unpaid_social_posting | P6_22_4 | P6_22A_4_1 | P6_22A_4_2 | 522 | 2041 |
| recreational_social_browsing | P6_22_5 | P6_22A_5_1 | P6_22A_5_2 | 2054 | 509 |
| other_recreational_internet | P6_22_6 | P6_22A_6_1 | P6_22A_6_2 | 362 | 2201 |

Verificado contra DDI archivado y cuestionario pp23–24. V4082 tiene el error tipográfico "vienes" en la etiqueta; el periodo se confirma con el cuestionario y el campo de minutos. Se excluyen todos los P6_21, P6_23 y fines de semana. No existe superposición de campos fuente con household_conversation_weekday_min.

## Faltantes canónicos

| Variable | Faltantes | % |
|---|---:|---:|
| person_id | 0 | 0.000 |
| household_id | 0 | 0.000 |
| state | 0 | 0.000 |
| sex | 0 | 0.000 |
| age | 0 | 0.000 |
| active_worker | 0 | 0.000 |
| employment_reference_week_absent | 0 | 0.000 |
| work_modality | 957 | 37.339 |
| commute_weekday_min | 0 | 0.000 |
| commute_5h | 0 | 0.000 |
| commute_structural_zero | 0 | 0.000 |
| sleep_weekday_min | 0 | 0.000 |
| personal_hygiene_weekday_min | 0 | 0.000 |
| household_conversation_weekday_min | 0 | 0.000 |
| work_weekday_min | 0 | 0.000 |
| has_child_u15 | 3 | 0.117 |
| has_minor_u18 | 3 | 0.117 |
| household_size | 0 | 0.000 |
| weight | 0 | 0.000 |
| stratum | 0 | 0.000 |
| cluster | 0 | 0.000 |
| leisure_weekday_min | 0 | 0.000 |

Los cuatro outcomes no tienen faltantes en esta población. Modalidad no preguntada e indicadores inciertos de menores permanecen nulos. No se aplica filtrado por casos completos.

## Distribuciones y extremos conservados

Descriptivos muestrales sin ponderar, minutos totales de lunes a viernes. Umbral superior de 3 IQR sólo para revisión, sin recorte ni exclusión.

| Variable | n | Min | P25 | P50 | P75 | P95 | P99 | Máx | Sobre 3 IQR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| commute_weekday_min | 2563 | 0 | 100 | 300 | 600 | 1200 | 1500 | 3000 | 6 |
| work_weekday_min | 2563 | 0 | 1920 | 2400 | 2880 | 3600 | 4320 | 5940 | 1 |
| sleep_weekday_min | 2563 | 120 | 1800 | 2100 | 2400 | 2700 | 3000 | 3600 | 0 |
| personal_hygiene_weekday_min | 2563 | 20 | 150 | 300 | 300 | 450 | 600 | 1200 | 8 |
| household_conversation_weekday_min | 2563 | 0 | 0 | 60 | 240 | 600 | 900 | 1200 | 8 |
| leisure_weekday_min | 2563 | 0 | 270 | 550 | 950 | 1800 | 2621.4 | 6360 | 15 |

## Hogares y diseño muestral

```json
{
  "approved_staging_hash": true,
  "raw_hashes_match_phase2a": true,
  "source_fields_unchanged": true,
  "existing_features_reconstructed_from_raw": true,
  "household_join_many_to_one": true,
  "household_join_unmatched": 0,
  "household_table_rows": 29181,
  "person_rows_before_join": 2563,
  "person_rows_after_join": 2563
}
```

Composición agregada a una fila por LLAVEHOG antes del join many-to-one. FAC_PER, EST_DIS y UPM_DIS originales y sus aliases canónicos se conservan. Pesos positivos y finitos; diseño completo.

| Estado | Sexo | n |
|---|---|---:|
| 09 | female | 578 |
| 09 | male | 611 |
| 15 | female | 578 |
| 15 | male | 796 |

## Validación y reproducción

```json
{
  "one_row_per_person": true,
  "expected_2563_persons": true,
  "same_persons_as_approved_population": true,
  "approved_population_rules": true,
  "no_negative_time": true,
  "finite_times": true,
  "exposure_resolved": true,
  "survey_fields_complete": true,
  "positive_finite_weights": true,
  "survey_aliases_exact": true,
  "canonical_renames_exact": true,
  "deprecated_outcome_names_absent": true,
  "unknown_children_not_imputed": true,
  "leisure_resolved": true,
  "all_columns_have_provenance": true,
  "no_leisure_conversation_overlap": true,
  "no_weekend_in_leisure": true,
  "zero_work_and_commute_retained": true,
  "leisure_sum_complete": true,
  "raw_files_unchanged": true,
  "approved_staging_unchanged": true,
  "parquet_roundtrip_exact": true
}
```

PASS: 25 pipeline tests.

Verificación independiente: PASS.

Los valores renombrados son idénticos al staging aprobado. Cambio en conteos de faltantes de variables existentes: 0; ocio es una variable nueva aprobada. Los originales y staging coinciden con sus hashes aprobados.

```text
python scripts/build_analytic_v1.py --preflight
python scripts/build_analytic_v1.py
python scripts/validate_analytic_v1.py
```

Python ≥3.11; dependencias fijadas en requirements.txt. No se necesita red. El build verifica el staging aprobado, reconstruye sus candidatas desde raw y publica sólo después de los controles. Código, datos, fuentes oficiales, campos y reglas tienen hashes/lineage en metadata/analytic_v1_manifest.json.

## Límites y revisión pendiente

- Observational survey: supports associations, not causal effects.
- Technical readiness does not authorize execution. Final human approval remains pending; no regressions, H1-H4 tests or EXP-001 were run.
- 34 persons have zero weekday work; retained and flagged. Eligibility refers to active work in the reference week, not positive weekday hours.
- 957 work_modality values are unasked structural missing values; do not silently treat as in-person or apply complete-case population changes.
- Three persons retain unknown child/minor indicators; no imputation. Models using them must specify and report missingness handling.
- Leisure components exclude P6_21/P6_23/weekends by definition; no source overlap with conversation, but reported time simultaneity cannot be ruled out.
- Extreme observations are preserved; descriptive QA flags are not exclusion rules.
- Thirty-four TSDEM domain persons without TMODULO remain outside the canonical module population but contribute to household composition.
- Survey-aware inference and domain variance estimation are future experiment responsibilities. Full staging remains available; this report uses unweighted sample descriptions.

## Preparación para experimentos

- All required integrity and semantic gates passed.
- Approved population and outcome definitions preserved.
- Parquet roundtrip succeeded; all output fields have lineage.

El estado indica preparación técnica del dataset. No autoriza ejecutar un experimento; se espera la aprobación humana final.

EXPERIMENT_READY
