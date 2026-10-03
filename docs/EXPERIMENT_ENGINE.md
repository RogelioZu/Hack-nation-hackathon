# Phase 3 — deterministic experiment contract, version 1.0

The human Phase 3 request grants APPROVED_FOR_EXPERIMENTS to analytic_v1
and authorizes EXP-001. Earlier pending-approval statements describe the
Phase 2B build date. `metadata/analytic_v1_experiment_approval.json` records
this later authorization; the original manifest, audits and Parquet are
preserved. This phase changes no data pipeline transformation and must not
rebuild the approved Parquet. Dataset hash, missingness and quality checks
are repeated read-only. Sample delta from Phase 2B is zero.

## Interface and scope

`run_experiment(spec: ExperimentSpec) -> ExperimentResult` is read-only.
Pydantic strict models reject extra fields, unknown variable roles, casts,
methods and sensitivity rules. JSON Schema contains both public models.
The closed method registry permits only weighted_linear_regression.
No formulas are evaluated as code. Scientific outcomes and controls must
appear in the canonical DATA_CONTRACT table and original manifest. Initial
supported controls are only work_weekday_min, age, sex and state; other
canonical fields remain available for QA, not automatically as controls.
Adding a model/method/role requires an explicit contract revision and tests.

Only analytic_v1.parquet is loaded as person data. Metadata and protocols
provide validation/provenance. No raw/staging data are read by the runner.
The separate approval record anchors the reviewed SHA256. Failures raise
ExperimentError with structured code/message; the CLI emits JSON to stderr
and exits nonzero. No successful result is returned on failure.

Population filters are ordered state, inclusive age, then sex; bounds cannot
extend beyond the approved domain. EXP-001 selects the entire domain and
asserts n=2563. Each model uses complete cases on its own variables; every
exclusion and weight sum is recorded. Unrelated missing fields do not drop
people. Missing design values, invalid weights, unexpected nonfinite data,
rank deficiency, n<=p or fewer than two PSUs stop execution. These last
thresholds are computational feasibility checks, not a claim of sufficient
scientific power. No scientific minimum beyond the expected EXP-001 n has
been supplied. No automatic outlier removal occurs.

## Statistical method fixed before execution

Point estimation minimizes sum_i w_i (y_i - x_i' b)^2, where w is FAC_PER.
The numerical solver uniformly divides weights by their mean; this leaves
coefficients and sandwich variance invariant. Original weights are used
for weighted population totals. The solver uses weighted least squares
via SVD. X contains an intercept, commute_5h and the requested controls.
Age and work minutes enter linearly in their original units; male is the
sex reference, state 09 is the state reference. No interactions, education,
marital status or other controls are inferred.

Let A = inverse(X' W X), u_i = y_i - x_i' b, and
S_g = sum_{i in PSU g} w_i x_i u_i. The covariance is

    V = [G/(G-1)] [(n-1)/(n-p)] A [sum_g S_g S_g'] A

The implementation calculates A from the weighted design pseudoinverse
after requiring full column rank. Groups are exact (EST_DIS, UPM_DIS)
pairs; this prevents accidental cross-stratum merging of reused identifiers.
The small-sample multiplier is CR1; confidence limits use Student t(G-1).
There is no frequency-weight residual degrees-of-freedom expansion.
All coefficient estimates, the complete covariance matrix and provenance
are persisted. Each exposure is one additional 300-minute weekday commute
unit, and each outcome is total weekday minutes.

This is **not full complex-survey inference**. EST_DIS is reported and used
for PSU identity, but the covariance is not centered within strata. No FPC,
replicate weights, calibration adjustment or full-domain design is provided.
PSUs absent from analytic_v1 cannot contribute to the domain variance;
loading full staging to reconstruct that design would exceed the approved
input contract. Thus intervals and hypothesis assessments are provisional
and may understate or overstate design uncertainty. A future full survey
implementation requires reviewed design metadata and permission for the
necessary design input. Do not describe this approximation as svyglm or
survey-adjusted stratified variance.

Implementation reference: [statsmodels cluster sandwich source](https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html).
The weights enter the score once (w*x*u), not sqrt(w)*x*u. Tests compare
coefficients and the full covariance to statsmodels WLS with cluster CR1,
including nonuniform weights and weight-scale invariance.
For why domain variance needs design information beyond a filtered table,
see [survey subset documentation](https://r-survey.r-forge.r-project.org/survey/html/subset.survey.design.html).
References consulted 2026-10-03; numerical runtime versions are recorded.

## Ranking and multiplicity fixed before execution

Adjusted estimates are primary; unadjusted estimates are comparisons.
The four primary coefficients have pointwise 95% t intervals and separate
Bonferroni intervals with individual coverage 98.75% (family coverage at
least 95% under the approximation). H1 evidence requires at least one
negative simultaneous interval. Lack of such evidence is inconclusive
unless all requested simultaneous intervals are nonnegative; even that
is not a general falsification. No scientific claim becomes a boolean.

Ranking starts with ascending point estimates. Six paired differences use
the difference of CR1-scaled PSU exposure influences, preserving covariance
between outcomes in the same people. Use Bonferroni t intervals for six
contrasts (individual coverage 99.1667%, family nominal 95%). A complete
ranking is distinguishable only if every ordered difference excludes zero
in the expected direction. Otherwise return INCONCLUSIVE_RANKING. If model
samples differ, return inconclusive without fabricating paired contrasts.
H2 may have evidence of some differences without a resolved complete order.
No interval overlap heuristic is used. Point order never identifies a
definitive most-sacrificed outcome. No cross-family or cross-sensitivity
familywise guarantee is claimed.

## Prespecified sensitivity and review boundary

Exclude work_weekday_min==0 only in the requested sensitivity. Missing
work values are not classified as zeros. Estimate the same adjusted and
unadjusted models, record counts, coefficients, intervals, directions and
rank changes. Primary records remain unchanged. Approximately 34 records
are expected to be excluded; actual counts are reported.

The runner uses fixed evidence templates, not explanations, mechanisms or
LLMs. It reports diagnostics including weighted fit, negative predictions,
leverage and weight-only Kish effective n (not design-effective n). Two
unselected follow-up alternatives satisfy the protocol's candidate contract;
no EXP-002 is assigned, selected or executed. Completion is a technical
status; results require human review. No Scientific Critic or Omnigent is
implemented, and no result enters an autonomous discovery decision.

## Reproduction

Python >=3.11; install requirements-experiments.txt in an isolated runtime.
The repository's CLI also supports packages under .local_deps.

    pip install -r requirements-experiments.txt
    python scripts/validate_experiment_engine.py
    python scripts/run_experiment.py experiments/EXP-001/spec.json

The validator needs only the committed analytic_v1, its manifest and its
approval record. Raw ENUT files, staging_v1 and the pipeline tests belong to
the upstream pipeline repository and are not read. It checks the approved
hash and manifest consistency, the JSON Schema against the strict models,
the closed method registry, runs the experiment-engine tests, reruns EXP-001
twice, requires exact equality with the committed result.json apart from
code/runtime fingerprints, checks the inputs are unchanged and persists
engine_validation.json. The CLI runs each
spec twice, requires identical serialized numerical/provenance results,
checks the input SHA256 before and after, and writes result.json, summary.md,
spec.json and validation.json under reports/experiments/<id>/.
Results omit wall-clock timestamps so identical code, input, spec and
runtime yield identical result bytes. Changes in source fingerprints or
runtime are explicitly reflected in provenance.
