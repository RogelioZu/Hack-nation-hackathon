# EXP-002 — revisión científica

Estado: **EXPERIMENT_COMPLETED**. Revisión: **REQUIRES_HUMAN_REVIEW**.

Población primaria: **2,563 personas**; suma FAC_PER: **12,737,236 personas**.
Minutos totales de lunes a viernes; coeficientes por 300 minutos adicionales de traslado.

## Asociaciones

Ajuste primario: trabajo entre semana, edad, sexo y estado. Referencias: hombre y CDMX (09).

Modelo con interacción: la columna de pendiente es la del **grupo de referencia** (sex = male), no un coeficiente agrupado de toda la población. Las pendientes de ambos grupos y su diferencia están en la sección de interacción.

| Outcome | Modelo | n | Pendiente del grupo de referencia (sex = male) | IC 95% puntual |
|---|---|---:|---:|---:|
| sleep_weekday_min | adjusted | 2563 | -41.596 | [-59.099, -24.094] |

## Interacción (exposición × moderador)

Modelo `adjusted:sleep_weekday_min`. Moderador: **sex**. Grupo de referencia: **male** (n=1407; suma FAC_PER=7,126,906). Grupo de comparación: **female** (n=1156; suma FAC_PER=5,610,330).
Codificación: sex[female] = 1 if sex == female, 0 if male (reference). Personas analizadas: 2563 de 2563; sin dato del moderador: 0.

| Estimando | Estimación | EE | IC 95% |
|---|---:|---:|---:|
| Pendiente de commute_5h en el grupo de referencia (sex = male) | -41.596 | 8.899 | [-59.099, -24.094] |
| Pendiente de commute_5h en el grupo de comparación (sex = female) | -59.312 | 12.469 | [-83.836, -34.788] |
| Interacción: diferencia de pendientes (female − male) | -17.715 | 15.160 | [-47.532, 12.101] |
| Efecto principal del moderador (sex[female]) | -5.002 | 21.649 | [-47.581, 37.578] |

Estado de la interacción: **INCONCLUSIVE_INTERVAL_INCLUDES_ZERO**. El intervalo de la interacción incluye el cero: resultado inconcluso sobre una diferencia entre los grupos del moderador. No es evidencia de que no haya diferencia. No se evaluó equivalencia.
Pendiente del grupo de comparación: b_exposure + b_interaction; variance V_ee + V_ii + 2 V_ei from the CR1 covariance.

## Orden e incertidumbre

**NOT_APPLICABLE_SINGLE_OUTCOME**.

Hay un solo outcome primario, así que no se evalúa un orden entre outcomes.

## Sensibilidad

La especificación aprobada no incluye análisis de sensibilidad.

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
| adjusted:sleep_weekday_min | 0 | 351 | 19 | 350 | 0.0589 | 0 | 183 |

Todos los extremos permanecen; las advertencias de leverage y predicciones negativas son diagnósticos, no exclusiones.

## Hipótesis

- Inconclusas: H3 — Interaction interval includes zero: inconclusive about heterogeneity; not evidence of no difference. sleep_weekday_min: commute_5h x sex (female vs reference male) INCONCLUSIVE_INTERVAL_INCLUDES_ZERO

H1, H2 y H4 no se evaluaron. Las categorías conservan evidencia y límites, no valores booleanos.

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
- Pointwise 95% intervals are descriptive. With one primary outcome there are no Bonferroni outcome or pairwise-difference families; no joint guarantee across sensitivity models.
- Sensitivity and unadjusted models are comparisons, not additional confirmatory findings. Absence of resolved differences is not equivalence.
- No domain-specific minimum sample size has been scientifically approved; computational checks enforce n > p, full rank and at least two PSUs.
- Numerical completion awaits human scientific review; no Scientific Critic assessment or follow-up selection has occurred.
- Observational, cross-sectional association; the interaction does not identify a causal effect or mechanism.
- The interaction coefficient is the formal estimand for the difference in exposure slopes between the two moderator groups.
- An interval that includes zero is inconclusive about heterogeneity; it is not evidence of no difference.
- No equivalence margin has been approved, so equivalence is not assessed.
- CR1 PSU-cluster uncertainty is an approximation, not full ENUT complex-survey variance.
- Rows missing the moderator are excluded under the model-specific complete-case policy, never assigned to a group.
- In moderated models the Estimate coefficient refers to the reference-group exposure slope; heterogeneity is assessed only through the interaction coefficient.

## Alternativas para revisión, sin selección

- Is the commuting association nonlinear? Assess adequacy of a common linear slope. Variables available; method and specification require review.

No se asigna EXP-003. La siguiente decisión queda pendiente de revisión humana.

## Reproducción y procedencia

Dataset SHA256: `973f2c010940da06048eb12ade53fa271525d82f68d3a157ad78e429d687dd94`.
Spec SHA256: `843e74a4da2a59b43810b008798581971085de887e34ce64eada987cac214e72`.
Código SHA256: `0ff03ce062f722d1604918fae59694b1b678cd53a951fb3d32073ac391644c42`.
Hash de analytic_v1 sin cambios: True.

`python scripts/run_experiment.py experiments/EXP-002/spec.json` ejecuta dos veces y exige resultados idénticos antes de publicar. `validation.json` registra la verificación de ejecución; `result.json` conserva matrices, diagnósticos, transformaciones y procedencia de cada estimación.

EXPERIMENT_COMPLETED
