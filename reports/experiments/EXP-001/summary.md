# EXP-001 — revisión científica

Estado: **EXPERIMENT_COMPLETED**. Revisión: **REQUIRES_HUMAN_REVIEW**.

Población primaria: **2,563 personas**; suma FAC_PER: **12,737,236 personas**.
Minutos totales de lunes a viernes; coeficientes por 300 minutos adicionales de traslado.

## Asociaciones

Ajuste primario: trabajo entre semana, edad, sexo y estado. Referencias: hombre y CDMX (09).

| Outcome | Modelo | n | Coeficiente | IC 95% puntual |
|---|---|---:|---:|---:|
| sleep_weekday_min | adjusted | 2563 | -48.711 | [-63.481, -33.940] |
| personal_hygiene_weekday_min | adjusted | 2563 | 3.094 | [-0.760, 6.948] |
| household_conversation_weekday_min | adjusted | 2563 | -3.816 | [-10.344, 2.712] |
| leisure_weekday_min | adjusted | 2563 | -20.396 | [-43.436, 2.644] |
| sleep_weekday_min | unadjusted | 2563 | -56.414 | [-71.438, -41.389] |
| personal_hygiene_weekday_min | unadjusted | 2563 | 2.041 | [-1.950, 6.031] |
| household_conversation_weekday_min | unadjusted | 2563 | -4.395 | [-11.142, 2.351] |
| leisure_weekday_min | unadjusted | 2563 | -27.223 | [-50.791, -3.656] |
| sleep_weekday_min | exclude_zero_weekday_work:adjusted | 2529 | -49.253 | [-63.992, -34.514] |
| personal_hygiene_weekday_min | exclude_zero_weekday_work:adjusted | 2529 | 3.318 | [-0.526, 7.162] |
| household_conversation_weekday_min | exclude_zero_weekday_work:adjusted | 2529 | -3.965 | [-10.460, 2.530] |
| leisure_weekday_min | exclude_zero_weekday_work:adjusted | 2529 | -21.568 | [-44.563, 1.426] |
| sleep_weekday_min | exclude_zero_weekday_work:unadjusted | 2529 | -55.994 | [-71.088, -40.899] |
| personal_hygiene_weekday_min | exclude_zero_weekday_work:unadjusted | 2529 | 2.602 | [-1.392, 6.596] |
| household_conversation_weekday_min | exclude_zero_weekday_work:unadjusted | 2529 | -4.594 | [-11.219, 2.032] |
| leisure_weekday_min | exclude_zero_weekday_work:unadjusted | 2529 | -27.169 | [-50.897, -3.440] |

## Orden e incertidumbre

**INCONCLUSIVE_RANKING**.

Orden descriptivo de los coeficientes ajustados (más negativo primero):
1. sleep_weekday_min: -48.711
2. leisure_weekday_min: -20.396
3. household_conversation_weekday_min: -3.816
4. personal_hygiene_weekday_min: 3.094

Las diferencias usan la covarianza entre outcomes estimados en las mismas personas. Bonferroni sobre todos los pares, con cobertura familiar nominal de 95%.

| A − B | Diferencia | Intervalo simultáneo |
|---|---:|---:|
| sleep_weekday_min − leisure_weekday_min | -28.314 | [-66.170, 9.541] |
| sleep_weekday_min − household_conversation_weekday_min | -44.894 | [-66.887, -22.902] |
| sleep_weekday_min − personal_hygiene_weekday_min | -51.804 | [-72.055, -31.554] |
| leisure_weekday_min − household_conversation_weekday_min | -16.580 | [-46.955, 13.794] |
| leisure_weekday_min − personal_hygiene_weekday_min | -23.490 | [-54.507, 7.527] |
| household_conversation_weekday_min − personal_hygiene_weekday_min | -6.910 | [-17.642, 3.822] |

El orden puntual no implica una jerarquía definitiva. No resolver una diferencia tampoco demuestra equivalencia.

## Sensibilidad

Regla: Exclude work_weekday_min == 0; retain missing until model-specific handling. Excluye **34** personas; n=2529; suma de pesos=12,561,985.
Estado de orden: **INCONCLUSIVE_RANKING**. La población primaria permanece intacta.

| Outcome | Cambio coeficiente | Dirección primaria → sensibilidad | Rango primario → sensibilidad |
|---|---:|---|---|
| sleep_weekday_min | -0.542 | negative → negative | 1 → 1 |
| personal_hygiene_weekday_min | 0.224 | positive → positive | 4 → 4 |
| household_conversation_weekday_min | -0.149 | negative → negative | 3 → 3 |
| leisure_weekday_min | -1.172 | negative → negative | 2 → 2 |

## Población y faltantes

| Paso | n | Suma de pesos |
|---|---:|---:|
| approved_analytic_v1 | 2563 | 12,737,236 |
| states | 2563 | 12,737,236 |
| age_inclusive | 2563 | 12,737,236 |
| sexes | 2563 | 12,737,236 |

| Variable canónica | Faltantes primarios |
|---|---:|
| person_id | 0 |
| household_id | 0 |
| state | 0 |
| sex | 0 |
| age | 0 |
| active_worker | 0 |
| employment_reference_week_absent | 0 |
| work_modality | 957 |
| commute_weekday_min | 0 |
| commute_5h | 0 |
| commute_structural_zero | 0 |
| sleep_weekday_min | 0 |
| personal_hygiene_weekday_min | 0 |
| household_conversation_weekday_min | 0 |
| work_weekday_min | 0 |
| has_child_u15 | 3 |
| has_minor_u18 | 3 |
| household_size | 0 |
| weight | 0 |
| stratum | 0 |
| cluster | 0 |
| leisure_weekday_min | 0 |

## Diagnósticos

| Modelo | Excluidos por faltantes | UPM | Estratos | gl | R² ponderado | Predicciones negativas | Leverage >2p/n |
|---|---:|---:|---:|---:|---:|---:|---:|
| adjusted:sleep_weekday_min | 0 | 351 | 19 | 350 | 0.0581 | 0 | 168 |
| adjusted:personal_hygiene_weekday_min | 0 | 351 | 19 | 350 | 0.0494 | 0 | 168 |
| adjusted:household_conversation_weekday_min | 0 | 351 | 19 | 350 | 0.0051 | 0 | 168 |
| adjusted:leisure_weekday_min | 0 | 351 | 19 | 350 | 0.0618 | 0 | 168 |
| unadjusted:sleep_weekday_min | 0 | 351 | 19 | 350 | 0.0346 | 0 | 178 |
| unadjusted:personal_hygiene_weekday_min | 0 | 351 | 19 | 350 | 0.0005 | 0 | 178 |
| unadjusted:household_conversation_weekday_min | 0 | 351 | 19 | 350 | 0.0008 | 0 | 178 |
| unadjusted:leisure_weekday_min | 0 | 351 | 19 | 350 | 0.0033 | 0 | 178 |
| exclude_zero_weekday_work:adjusted:sleep_weekday_min | 0 | 351 | 19 | 350 | 0.0581 | 0 | 166 |
| exclude_zero_weekday_work:adjusted:personal_hygiene_weekday_min | 0 | 351 | 19 | 350 | 0.0493 | 0 | 166 |
| exclude_zero_weekday_work:adjusted:household_conversation_weekday_min | 0 | 351 | 19 | 350 | 0.0053 | 0 | 166 |
| exclude_zero_weekday_work:adjusted:leisure_weekday_min | 0 | 351 | 19 | 350 | 0.0655 | 0 | 166 |
| exclude_zero_weekday_work:unadjusted:sleep_weekday_min | 0 | 351 | 19 | 350 | 0.0340 | 0 | 176 |
| exclude_zero_weekday_work:unadjusted:personal_hygiene_weekday_min | 0 | 351 | 19 | 350 | 0.0007 | 0 | 176 |
| exclude_zero_weekday_work:unadjusted:household_conversation_weekday_min | 0 | 351 | 19 | 350 | 0.0009 | 0 | 176 |
| exclude_zero_weekday_work:unadjusted:leisure_weekday_min | 0 | 351 | 19 | 350 | 0.0032 | 0 | 176 |

Todos los extremos permanecen; las advertencias de leverage y predicciones negativas son diagnósticos, no exclusiones.

## Hipótesis

- Evidencia compatible: H1 — Evidence consistent with a negative association under the specified model. sleep_weekday_min; Bonferroni outcome intervals below zero; provisional survey approximation
- Evidencia compatible: H2 — Evidence of at least one difference. 2 of 6 paired simultaneous intervals exclude zero; this does not establish a full ranking

H3 y H4 no se evaluaron. Las categorías conservan evidencia y límites, no valores booleanos.

## Método y límites

Estimación FAC_PER por mínimos cuadrados ponderados, errores agrupados por (EST_DIS, UPM_DIS), corrección CR1 y cuantiles t con G−1 grados de libertad. Los pesos se escalan por una constante para estabilidad numérica; los totales usan FAC_PER original.

**No es una estimación completa de varianza de encuesta.** EST_DIS identifica los conglomerados; no se aplica centrado dentro de estrato, FPC ni reconstrucción del diseño fuera del dominio.

Referencias de implementación: [statsmodels sandwich](https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html) y [survey: subpoblaciones](https://r-survey.r-forge.r-project.org/survey/html/subset.survey.design.html). Ecuaciones y decisiones completas: `docs/EXPERIMENT_ENGINE.md`.

- Observational associations; no identification of mechanisms or intervention effects.
- FAC_PER-weighted point estimates; CR1 PSU-cluster sandwich is an approximation, not full ENUT complex-survey variance.
- EST_DIS identifies nested PSUs and is reported, but covariance does not center scores within strata or apply stratification gains.
- Only approved analytic persons are loaded. PSUs outside this domain are unavailable; full survey-domain variance is not reconstructed.
- No finite-population correction, replicate weights or calibration uncertainty adjustment. Approximate intervals may be too wide or too narrow.
- Linear specification, recalled time, possible temporal overlap and unmeasured differences limit interpretation. Extremes and zeros retained in primary models.
- Pointwise 95% intervals are descriptive. Separate Bonferroni families cover primary outcomes and pairwise differences; no joint guarantee across both families or sensitivity models.
- Sensitivity and unadjusted models are comparisons, not additional confirmatory findings. Absence of resolved differences is not equivalence.
- No domain-specific minimum sample size has been scientifically approved; computational checks enforce n > p, full rank and at least two PSUs.
- Numerical completion awaits human scientific review; no Scientific Critic assessment or follow-up selection has occurred.

## Alternativas para revisión, sin selección

- Is the commuting association nonlinear? Assess adequacy of a common linear slope. Variables available; method and specification require review.
- Does the association differ by sex? Assess whether an overall association masks subgroup differences. Variables available; interactions require a new approved specification.

No se asigna EXP-002. La siguiente decisión queda pendiente de revisión humana.

## Reproducción y procedencia

Dataset SHA256: `973f2c010940da06048eb12ade53fa271525d82f68d3a157ad78e429d687dd94`.
Spec SHA256: `b7fa540b5e13f16d765ec71597bed4f08cba28299d32ef11a84983b3020f4d71`.
Código SHA256: `7867362c970e0e2d0ae33ba13813d2672ff67f492ce169d0ca55fe971c2fbedd`.
Hash de analytic_v1 sin cambios: True.

`python scripts/run_experiment.py experiments/EXP-001/spec.json` ejecuta dos veces y exige resultados idénticos antes de publicar. `validation.json` registra la verificación de ejecución; `result.json` conserva matrices, diagnósticos, transformaciones y procedencia de cada estimación.

EXPERIMENT_COMPLETED
