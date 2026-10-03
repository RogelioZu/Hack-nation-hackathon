# Phase 2A — validación semántica

**Estado: STAGING_VALIDATED_REQUIRES_SCIENTIFIC_REVIEW**. Revisión científica pendiente; no se construyó analytic_v1 ni se estimaron modelos.

Staging conserva una fila por persona de TMODULO y todas sus columnas originales. Las selecciones siguientes son indicadores y conteos: no eliminan filas del staging.

## Población y flujo

| Paso acumulativo | n |
|---|---:|
| raw_tmodulo | 74,053 |
| geographic_09_15 | 4,754 |
| geographic_and_age18_65 | 3,659 |
| active_worker_in_domain | 2,563 |
| primary_after_absent_and_code8_exclusion | 2,563 |
| primary_with_resolved_commute | 2,563 |
| staging_rows_retained | 74,053 |

| Indicador | Todo staging | Entidades 09/15, 18–65 | Población primaria |
|---|---:|---:|---:|
| active_worker_count | 43912 | 2563 | 2563 |
| P5_2_7_excluded_count | 707 | 37 | 0 |
| commute_observed_count | 43583 | 2517 | 2517 |
| commute_observed_zero_count | 4117 | 144 | 144 |
| structural_zero_commute_count | 329 | 46 | 46 |
| unresolved_commute_blanks | 0 | 0 | 0 |
| sleep_special_code_count | 20 | 0 | 0 |
| has_child_u15_person_count | 38802 | 1500 | 1038 |
| has_minor_u18_person_count | 44687 | 1736 | 1196 |
| households_with_child_u15 | 12998 | 632 | 589 |
| households_with_minor_u18 | 14713 | 729 | 678 |

El conteo de P5_2=7 en el dominio indica personas excluidas de la población primaria, pero conservadas en staging. Un cero observado y un cero estructural se reportan por separado.

### Razones de traslado faltante o cero estructural

| Razón | Todo staging | Dominio | Primaria |
|---|---:|---:|---:|
| exclusively_virtual_P5_7_2 | 329 | 46 | 46 |
| not_employed_P5_2_8 | 29434 | 1059 | 0 |
| reference_week_absent_P5_2_7 | 707 | 37 | 0 |
| reported_time | 43583 | 2517 | 2517 |

### Códigos especiales en otros tiempos

| Campo derivado / componente | Todo staging | Dominio | Primaria |
|---|---:|---:|---:|
| work_weekday_status | 1 | 0 | 0 |
| work_branch2_weekday_status | 1 | 0 | 0 |
| sleep_weekday_status | 20 | 0 | 0 |
| sleep_weekend_status | 20 | 0 | 0 |

## Integridad y composición del hogar

```json
{
  "cardinality": "many-to-one",
  "tsdem_rows": 94565,
  "aggregated_household_rows": 29181,
  "persons_before_join": 74053,
  "persons_after_join": 74053,
  "unmatched_household_persons": 0,
  "unmatched_distinct_households": 0,
  "households_with_unknown_age": 119,
  "unknown_age_roster_records": 161
}
```

TSDEM se agregó antes del join: una fila por LLAVEHOG, contando integrantes de todas las edades. Una edad desconocida no se interpreta como ausencia de menores: si no hay un menor confirmado, el indicador queda nulo. Si ya hay uno confirmado, queda verdadero.

### Muestra primaria por sexo y entidad

| Entidad | Sexo | n |
|---|---|---:|
| 09 | female | 578 |
| 09 | male | 611 |
| 15 | female | 578 |
| 15 | male | 796 |

## Faltantes de todas las candidatas

| Variable | Todo staging n (%) | Dominio n (%) | Primaria n (%) |
|---|---:|---:|---:|
| person_id | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| household_id | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| state | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| sex | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| age | 129 (0.17%) | 0 (0.00%) | 0 (0.00%) |
| active_worker | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| employment_reference_week_absent | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| work_modality | 48277 (65.19%) | 2053 (56.11%) | 957 (37.34%) |
| commute_weekday_min | 30141 (40.70%) | 1096 (29.95%) | 0 (0.00%) |
| commute_5h | 30141 (40.70%) | 1096 (29.95%) | 0 (0.00%) |
| commute_structural_zero | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| sleep_weekday_min | 20 (0.03%) | 0 (0.00%) | 0 (0.00%) |
| selfcare_weekday_min | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| family_weekday_min | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| work_weekday_min | 30142 (40.70%) | 1096 (29.95%) | 0 (0.00%) |
| has_child_u15 | 162 (0.22%) | 3 (0.08%) | 3 (0.12%) |
| has_minor_u18 | 143 (0.19%) | 3 (0.08%) | 3 (0.12%) |
| household_size | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| weight | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| stratum | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |
| cluster | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) |

Modalidad nula puede ser un salto documentado para ocupaciones distintas de empleado/obrero; no se rellena como presencial. Las ausencias semánticas se distinguen con columnas *_status y *_reason.

## Distribuciones de tiempo

Minutos totales de lunes a viernes. Estadísticas descriptivas muestrales **sin ponderar**; percentiles por interpolación lineal. El JSON incluye bins, medias y conteos de extremos. Ningún extremo se elimina ni se winsoriza.

### all_staging

| Variable | n observado/derivado | Min | P1 | P5 | P25 | P50 | P75 | P95 | P99 | Máx | >3 IQR superior |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| commute_weekday_min | 43912 | 0 | 0 | 0 | 50 | 150 | 300 | 608 | 1200 | 5100 | 731 |
| work_weekday_min | 43911 | 0 | 0 | 240 | 1500 | 2400 | 2700 | 3600 | 4320 | 6000 | 0 |
| sleep_weekday_min | 74033 | 20 | 1200 | 1500 | 2100 | 2400 | 2400 | 3000 | 3300 | 5400 | 698 |
| selfcare_weekday_min | 74053 | 1 | 50 | 90 | 150 | 300 | 300 | 600 | 750 | 5400 | 734 |
| family_weekday_min | 74053 | 0 | 0 | 0 | 0 | 40 | 180 | 600 | 900 | 4950 | 933 |

### geographic_age_domain

| Variable | n observado/derivado | Min | P1 | P5 | P25 | P50 | P75 | P95 | P99 | Máx | >3 IQR superior |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| commute_weekday_min | 2563 | 0 | 0 | 0 | 100 | 300 | 600 | 1200 | 1500 | 3000 | 6 |
| work_weekday_min | 2563 | 0 | 0 | 480 | 1920 | 2400 | 2880 | 3600 | 4320 | 5940 | 1 |
| sleep_weekday_min | 3659 | 120 | 1200 | 1500 | 1800 | 2100 | 2400 | 2700 | 3000 | 5400 | 1 |
| selfcare_weekday_min | 3659 | 20 | 50 | 100 | 150 | 300 | 300 | 450 | 600 | 1200 | 19 |
| family_weekday_min | 3659 | 0 | 0 | 0 | 0 | 60 | 300 | 600 | 900 | 2100 | 4 |

### primary_commuting_population

| Variable | n observado/derivado | Min | P1 | P5 | P25 | P50 | P75 | P95 | P99 | Máx | >3 IQR superior |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| commute_weekday_min | 2563 | 0 | 0 | 0 | 100 | 300 | 600 | 1200 | 1500 | 3000 | 6 |
| work_weekday_min | 2563 | 0 | 0 | 480 | 1920 | 2400 | 2880 | 3600 | 4320 | 5940 | 1 |
| sleep_weekday_min | 2563 | 120 | 1200 | 1500 | 1800 | 2100 | 2400 | 2700 | 3000 | 3600 | 0 |
| selfcare_weekday_min | 2563 | 20 | 60 | 111 | 150 | 300 | 300 | 450 | 600 | 1200 | 8 |
| family_weekday_min | 2563 | 0 | 0 | 0 | 0 | 60 | 240 | 600 | 900 | 1200 | 8 |

## Comparación con TVAR_CREA

Se reconstruyen auxiliares de semana completa sólo para validación y se dividen entre 60. Tolerancia: 1e-8 horas. No se exige igualdad entre componentes diarios/semanales de alcance distinto.

| Dominio | Agregado | Comparables | Iguales con tolerancia | Diferencias | Máxima diferencia (h) | Derivación faltante |
|---|---|---:|---:|---:|---:|---:|
| all_staging | TRAS_TRAB | 43912 | 43912 | 0 | 7.105427357601002e-15 | 30141 |
| all_staging | TRAB_MERC_PV | 43911 | 43911 | 0 | 1.4210854715202004e-14 | 30142 |
| all_staging | ACTIV_CUID_PER | 74033 | 74033 | 0 | 5.684341886080802e-14 | 20 |
| all_staging | ACTIV_CONVIV | 74053 | 74053 | 0 | 5.684341886080802e-14 | 0 |
| primary_commuting_population | TRAS_TRAB | 2563 | 2563 | 0 | 7.105427357601002e-15 | 0 |
| primary_commuting_population | TRAB_MERC_PV | 2563 | 2563 | 0 | 1.4210854715202004e-14 | 0 |
| primary_commuting_population | ACTIV_CUID_PER | 2563 | 2563 | 0 | 1.4210854715202004e-14 | 0 |
| primary_commuting_population | ACTIV_CONVIV | 2563 | 2563 | 0 | 1.4210854715202004e-14 | 0 |

- **TRAS_TRAB:** weekday + weekend commuting, divided by 60; virtual-only zeros explicit; inactive/absent not imputed.

- **TRAB_MERC_PV:** weekday + weekend work across required modality branches, divided by 60.

- **ACTIV_CUID_PER:** all-week P6_1 sleep+eating+hygiene, plus P6_23 items 1/2; broader than selfcare_weekday_min.

- **ACTIV_CONVIV:** all-week P6_18,19,20,21,22 with explicit nonparticipation zeros; broader than family_weekday_min; diagnostic only, not leisure.

## Fuentes y transformaciones exactas

Las candidatas de autocuidado y familia tienen definiciones estrechas, documentadas abajo. Su aprobación científica final sigue pendiente. Para pares se exige formato de dos dígitos, minutos 00–59 y códigos especiales por campo. Horas 99 no se tratan globalmente como faltante.

### person_id

- Fuente: **TMODULO**; `LLAVEMOD`.
- Regla: Exact string alias; unique and nonempty required.
- Unidad: identifier.
- Faltantes: fail.
### household_id

- Fuente: **TMODULO**; `LLAVEHOG`.
- Regla: Exact string alias.
- Unidad: identifier.
- Faltantes: fail.
### state

- Fuente: **TMODULO**; `CVE_ENT`.
- Regla: Exact string; primary domain 09/15; staging preserves other states.
- Unidad: state code.
- Faltantes: fail.
### sex

- Fuente: **TMODULO**; `SEXO`.
- Regla: 1=male, 2=female; original SEXO retained.
- Unidad: category.
- Faltantes: unknown code becomes null and is counted.
### age

- Fuente: **TMODULO**; `EDAD_V`.
- Regla: Exact integer age 00..96; 97 is retained as lower bound 97+; 98/99 are unknown, not ages.
- Unidad: completed years; 97 top-coded.
- Faltantes: null for special/invalid/empty; outside primary domain.
### active_worker

- Fuente: **TMODULO**; `P5_1, P5_2`.
- Regla: P5_1 == 1 OR P5_2 in 1..6; exact approved rule.
- Unidad: boolean.
- Faltantes: unrecognized employment codes fail validation rather than silently redefine eligibility.
### employment_reference_week_absent

- Fuente: **TMODULO**; `P5_2`.
- Regla: P5_2 == 7; retained but excluded from primary_commuting_population.
- Unidad: boolean.
- Faltantes: blank is not code 7.
### work_modality

- Fuente: **TMODULO**; `P5_7, P5_5, P5_1, P5_2`.
- Regla: P5_7: 1=in_person, 2=virtual, 3=hybrid; applies to employees P5_5=1.
- Unidad: category.
- Faltantes: null for skips, with work_modality_status; never infer in-person for other occupations.
- Evidencia: questionnaire p12, filter 5.7; DDI V3524.
### commute_weekday_min

- Fuente: **TMODULO**; `P5_9_1, P5_9_2, P5_7, P5_1, P5_2, P5_5, P5_8_1_1, P5_8_1_2, P5_8_1_3, P5_8_1_4, P5_8_2_1, P5_8_2_2, P5_8_2_3, P5_8_2_4`.
- Regla: 60*hours+minutes for valid observed pair; zero for confirmed virtual-only skip; includes trips for all jobs.
- Unidad: total minutes Monday-Friday.
- Faltantes: other skips remain null: P5_2=7, P5_2=8, total weekly work <60min; unexplained or partial blanks unresolved; special/invalid/conflicting pairs null.
- Evidencia: questionnaire p12, filters 5.8/5.9; DDI V3533/V3534.
### commute_5h

- Fuente: **TMODULO**; `P5_9_1, P5_9_2, P5_7`.
- Regla: commute_weekday_min / 300; inherits all commute dependencies.
- Unidad: 300-minute units.
- Faltantes: propagate commute null.
### commute_structural_zero

- Fuente: **TMODULO**; `P5_7, P5_9_1, P5_9_2, P5_1, P5_2`.
- Regla: true only for blank time pair on approved active virtual-only branch.
- Unidad: boolean.
- Faltantes: false otherwise; reported zero remains observed.
### sleep_weekday_min

- Fuente: **TMODULO**; `P6_1_1_1, P6_1_1_2`.
- Regla: 60*hours+minutes; exclusive sleep including naps.
- Unidad: total minutes Monday-Friday.
- Faltantes: 99 in either field means No sabe: null; preserve pair and special_code status.
- Evidencia: questionnaire p14; DDI V3544/V3545.
### selfcare_weekday_min

- Fuente: **TMODULO**; `P6_1_3_1, P6_1_3_2`.
- Regla: 60*hours+minutes for exclusive personal hygiene/grooming; excludes eating, sleep, health care and resting.
- Unidad: total minutes Monday-Friday.
- Faltantes: special/invalid/unresolved pairs null; no blanket zero.
- Evidencia: questionnaire p14 item 6.1.3; DDI V3552/V3553.
### family_weekday_min

- Fuente: **TMODULO**; `P6_21_1, P6_21A_1_1, P6_21A_1_2`.
- Regla: 60*hours+minutes for exclusive conversation with household members, in person or virtual; P6_21_1=2 and blank pair gives flagged structural zero.
- Unidad: total minutes Monday-Friday.
- Faltantes: P6_21_1=1 with blanks unresolved; No with reported time is a conflict; special/invalid null.
- Evidencia: questionnaire p24 item 6.21.1; DDI V4096/V4097/V4098.
### work_weekday_min

- Fuente: **TMODULO**; `P5_8_1_1, P5_8_1_2, P5_8_2_1, P5_8_2_2, P5_1, P5_2, P5_5, P5_7`.
- Regla: Sum required weekday branches: P5_7=1 first, =2 second, =3 both. P5_5=2..6 with P5_7 blank: first branch holds all work without modality distinction. Includes all jobs and meal time during work; excludes home-work commuting.
- Unidad: total minutes Monday-Friday.
- Faltantes: inactive/absent structural null; unused branches remain structural blanks, not generic zeros; required missing component makes sum null.
- Evidencia: questionnaire p12; DDI V3525..V3530 interview instructions.
### has_child_u15

- Fuente: **TSDEM**; `LLAVEHOG, LLAVESDE, EDAD`.
- Regla: Any known roster age <15 per household, then validated many-to-one join.
- Unidad: nullable boolean.
- Faltantes: true if known child; null if none known and any unknown age; otherwise false.
### has_minor_u18

- Fuente: **TSDEM**; `LLAVEHOG, LLAVESDE, EDAD`.
- Regla: Any known roster age <18 per household, then validated many-to-one join.
- Unidad: nullable boolean.
- Faltantes: true if known minor; null if none known and any unknown age; otherwise false.
### household_size

- Fuente: **TSDEM**; `LLAVEHOG, LLAVESDE`.
- Regla: Number of unique roster persons per household; all ages; no exclusions; duplicate person IDs fail.
- Unidad: persons.
- Faltantes: unmatched household fails staging validation.
### weight

- Fuente: **TMODULO**; `FAC_PER`.
- Regla: Numeric alias; raw FAC_PER retained.
- Unidad: person expansion factor.
- Faltantes: missing/nonfinite/nonpositive fails.
### stratum

- Fuente: **TMODULO**; `EST_DIS`.
- Regla: Exact string alias, retaining leading zeros.
- Unidad: survey stratum.
- Faltantes: fail.
### cluster

- Fuente: **TMODULO**; `UPM_DIS`.
- Regla: Exact string alias, retaining leading zeros.
- Unidad: primary sampling unit.
- Faltantes: fail.

## Componentes candidatos de ocio; variable no creada

- exercise/sport: P6_18A_1 + P6_18A_2.
- arts/games/hobbies: P6_19A_1_1 + P6_19A_1_2; P6_19A_2_1 + P6_19A_2_2.
- entertainment/cultural venues: P6_20A_1_1 + P6_20A_1_2; P6_20A_2_1 + P6_20A_2_2.
- social/family/civic/religious activities, overlaps family candidate: P6_21A_1_1 + P6_21A_1_2; P6_21A_2_1 + P6_21A_2_2; P6_21A_3_1 + P6_21A_3_2; P6_21A_4_1 + P6_21A_4_2.
- entertainment media and internet: P6_22A_1_1 + P6_22A_1_2; P6_22A_2_1 + P6_22A_2_2; P6_22A_3_1 + P6_22A_3_2; P6_22A_4_1 + P6_22A_4_2; P6_22A_5_1 + P6_22A_5_2; P6_22A_6_1 + P6_22A_6_2.
- prayer/meditation/rest; classified under official personal care: P6_23A_1_1 + P6_23A_1_2.

La selección de componentes, el solapamiento con familia y la inclusión de descanso/religión requieren definición humana. check_social_entertainment_weekly_min es una reconstrucción diagnóstica del agregado oficial; no es leisure_weekday_min.

## Preguntas semánticas pendientes

- Approve narrow selfcare as hygiene/grooming (P6_1_3), not eating/sleep/rest/health care or the broad ACTIV_CUID_PER.
- Approve family time as exclusive conversation with household members (6.21.1), not all relatives/friends or all 6.21; explicit nonparticipation is a flagged zero.
- Approve the final leisure component set and overlap policy. No leisure_weekday_min is created.
- DDI EDAD notes use 12 years while category labels use 18 for unknown-age codes 98/99. Both codes remain unknown for household thresholds; no inference from conflicting labels.
- The 34 TSDEM persons aged 18–65 in states 09/15 without TMODULO remain outside person staging; they are retained when computing household composition. Reason for absent module is not established.
- Extreme times are retained; no scientific exclusion threshold has been approved.

## Controles, reproducción y cambios

```json
{
  "all_module_rows_retained": true,
  "person_id_unique_nonempty": true,
  "household_features_unique": true,
  "household_join_many_to_one_no_unmatched": true,
  "raw_columns_exactly_preserved": true,
  "survey_fields_preserved": true,
  "survey_fields_nonmissing": true,
  "weights_positive_finite": true,
  "weight_alias_exact": true,
  "employment_codes_known": true,
  "employment_sequence_consistent": true,
  "absent_workers_retained_and_not_primary": true,
  "no_negative_derived_time": true,
  "virtual_zero_has_evidence": true,
  "sleep_special_is_missing": true,
  "leisure_not_created": true,
  "all_candidate_features_present": true,
  "invalid_pairs_not_silently_coerced": true,
  "household_coverage_matches_thogar": true,
  "raw_matches_reviewed_phase1": true,
  "raw_files_unchanged_after_build": true,
  "parquet_roundtrip_exact": true
}
```

Pruebas: python -m unittest discover -s tests -v. Resultado registrado: PASS: 17 tests, 0 failures, 0 errors.

Ejecución: `python scripts/build_staging_v1.py`. Verificación independiente: `python scripts/validate_staging_v1.py`. Dependencias fijadas en requirements.txt; Python ≥3.11.

Comparación con fase 1: TMODULO unchanged at 74,053 rows; geographic/age domain unchanged at 3,659. Its 1,142 raw commute blank pairs are classified explicitly; 46 become virtual-only structural zeros. Twenty all-module sleep special-code pairs become derived missing values; raw strings unchanged.

Validación independiente: PASS.

Cambio frente al build anterior: 0 filas; 0 conteos de faltantes cambiaron (detalle en JSON).

El JSON registra hashes de los cinco CSV antes/después, fuentes oficiales, código, archivo Parquet y variación de conteos/faltantes respecto a una ejecución previa, si existe. Se conservan FAC_PER, EST_DIS y UPM_DIS sin cambios.

## Referencias oficiales

- [INEGI ENUT 2024, DDI completo](https://www.inegi.org.mx/rnm/index.php/metadata/export/1127/ddi); copia local: `metadata/official/enut_2024_ddi.xml`; SHA-256 `1928ef3ef1cc69f7d4db3727a3d66c109d85836288f499ab05800130d63136d5`.
- [INEGI ENUT 2024, cuestionario](https://www.inegi.org.mx/contenidos/programas/enut/2024/doc/enut_2024_cuestionario.pdf); copia local: `metadata/official/enut_2024_cuestionario.pdf`; SHA-256 `949752e35fbc54fbe513466eb7caab32cef5010f046cb7777aa8490832769a62`.
