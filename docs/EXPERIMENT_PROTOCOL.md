# Experiment Protocol

## Purpose

This document defines what constitutes a valid scientific experiment in the Time Poverty Lab.

The system investigates how commuting burden is associated with the allocation of personal time among workers living in Mexico City and the State of Mexico using ENUT 2024.

Experiments must generate reproducible evidence that can modify the next scientific decision made by the discovery system.

---

## Core Scientific Question

Among workers living in Mexico City and the State of Mexico, which dimensions of personal time show the largest reduction as weekday commuting burden increases, after accounting for working hours and observable sociodemographic characteristics?

Additionally:

- Does this relationship differ by sex?
- Does this relationship differ according to the presence of children or minors in the household?
- Are observed relationships linear or nonlinear?
- Does commuting reduce the duration of activities, the probability of participating in them, or both?

---

## Scientific Scope

### Population

Primary analytic population:

- age between 18 and 65 years
- resident of Mexico City (`CVE_ENT = 09`) or State of Mexico (`CVE_ENT = 15`)
- classified as part of the relevant employed population according to the approved population definition
- valid information for the variables required by the experiment

The exact employment filter must be defined in `SCIENTIFIC_PROTOCOL.md` and must not be silently modified by an experiment.

### Primary Exposure

`commute_weekday_min`

Total reported minutes spent commuting to and from work from Monday through Friday.

For model interpretation, the preferred standardized exposure is:

`commute_5h = commute_weekday_min / 300`

One unit therefore represents 300 additional commuting minutes per week.

### Primary Outcomes

The canonical outcomes are:

- `sleep_weekday_min`
- `personal_hygiene_weekday_min` (exclusive personal hygiene/grooming)
- `household_conversation_weekday_min` (exclusive household conversation)
- `leisure_weekday_min` (Phase 2B approved components in DATA_CONTRACT.md)

Experiments may investigate component variables separately when scientifically justified.

### Primary Heterogeneity Dimensions

Initial effect-modification analyses may consider:

- sex
- presence of children under 15 in the household
- presence of minors under 18 in the household
- state of residence
- work modality

Additional subgroup analyses must be justified by a scientific hypothesis.

---

## Definition of a Valid Experiment

A valid experiment must contain all of the following:

1. A clearly stated scientific question.
2. At least one falsifiable hypothesis.
3. A defined population.
4. A defined exposure.
5. One or more measurable outcomes.
6. A specified statistical or computational method.
7. Explicit covariates or controls.
8. A reproducible execution procedure.
9. Quantitative results.
10. An uncertainty assessment.
11. A scientific interpretation.
12. A limitations assessment.
13. A decision about what should be investigated next.

An experiment is incomplete if it only produces a chart, descriptive statistic, model coefficient, or narrative without affecting the next scientific decision.

---

## Discovery Loop

Every experiment must participate in the following loop:

```text
Question
↓
Evidence
↓
Hypothesis
↓
Candidate experiments
↓
Experiment selection
↓
Execution
↓
Result
↓
Scientific critique
↓
Updated decision
↓
Next experiment
```

The system must not execute a permanently hard-coded sequence of experiments.

Results must be allowed to change the next action.

---

## Initial Hypotheses

### H1 — Time Displacement

Higher commuting burden is associated with lower time allocation to at least one personal-time dimension.

### H2 — Unequal Displacement

The magnitude of the association differs across:

- sleep
- exclusive household conversation
- leisure
- exclusive personal hygiene/grooming

The system should determine which category exhibits the largest negative association rather than assuming the answer beforehand.

### H3 — Sex Heterogeneity

The relationship between commuting burden and personal-time allocation differs between men and women.

This should be evaluated using interaction terms or other statistically justified comparison methods.

### H4 — Household Constraint

The relationship between commuting burden and personal-time allocation differs according to the presence of children or minors in the household.

---

## Baseline Experiment

The initial experiment should estimate the relationship between commuting burden and each approved time-use outcome.

A generic baseline specification is:

```text
Outcome =
    intercept
    + commuting burden
    + work time
    + demographic controls
    + socioeconomic controls
    + error
```

Conceptually:

\[
Y_k =
\alpha +
\beta_k Commute5h +
\gamma WorkHours +
X\theta +
\epsilon
\]

where:

- `Y_k` is one approved time-use outcome
- `Commute5h` represents 300 additional commuting minutes per week
- `WorkHours` controls for working-time burden
- `X` contains approved covariates

The initial experiment must not determine in advance which outcome will show the strongest association.

---

## Candidate Experiment Selection

Before executing a follow-up experiment, the Experiment Planner should propose at least two scientifically plausible alternatives whenever feasible.

Each candidate should include:

- hypothesis tested
- expected information gain
- feasibility
- required variables
- computational cost
- potential limitations
- reason the experiment could change the current scientific interpretation

The next experiment should be selected based primarily on expected scientific learning, not on which test is most likely to produce a statistically significant result.

---

## Branching Rules

The experiment workflow must adapt to observed evidence.

Examples:

### Strong difference by sex

If the baseline analysis reveals substantial heterogeneity by sex:

```text
Baseline result
↓
Possible sex heterogeneity
↓
Test Commute × Sex interaction
```

### Household composition may explain heterogeneity

If a sex interaction weakens substantially after household controls:

```text
Sex heterogeneity
↓
Household controls introduced
↓
Difference changes
↓
Investigate Commute × HouseholdWithChildren
```

### Evidence of nonlinearity

If commuting effects appear different across the commuting distribution:

```text
Linear model
↓
Residual or subgroup evidence of nonlinearity
↓
Test nonlinear specification
```

Possible methods include:

- commuting categories
- splines
- polynomial terms
- quantile-based comparisons

### Participation versus duration

If leisure or another activity decreases with commuting:

```text
Observed activity decline
↓
Is participation disappearing or duration shrinking?
↓
Two-part analysis
```

Part 1:

\[
P(Activity > 0)
\]

Part 2:

\[
Time \mid Activity > 0
\]

### Weak or null result

A null result must not automatically terminate investigation.

The Scientific Critic should evaluate:

- statistical power
- sample size
- measurement quality
- model specification
- heterogeneity
- nonlinearity
- missingness
- alternative hypotheses

A new experiment should only be executed if there is a scientifically justified reason.

---

## Survey Design Requirements

ENUT is survey data and must not be treated as a simple random sample without justification.

The analytic layer must preserve:

- `FAC_PER`
- `EST_DIS`
- `UPM_DIS`

Experiments should use survey-aware or appropriately weighted methods whenever supported.

At minimum, experiments must document:

- whether weights were used
- how uncertainty was estimated
- whether clustering was considered
- whether stratification was considered
- whether subgroup sample size is sufficient

The analysis must distinguish between:

- raw sample count
- weighted population estimates

---

## Covariate Policy

Potential controls may include:

- age
- sex
- state
- education
- marital status
- working time
- work modality
- household composition
- other scientifically justified socioeconomic characteristics

Covariates must not be added solely because they improve model fit.

Every control should have a scientific justification.

The system must record which variables were used in each experiment.

---

## Missing Data Policy

Experiments must not automatically convert missing values to zero.

The system must distinguish, whenever possible, between:

- zero
- not applicable
- not reported
- invalid
- structurally missing

Each experiment must report missingness for variables it uses.

If missingness could materially affect interpretation, the Scientific Critic must flag the result.

---

## Outlier Policy

Extreme observations must not be deleted automatically.

Potential outliers must first be:

1. detected
2. documented
3. checked against valid questionnaire ranges
4. evaluated for scientific plausibility

Sensitivity analyses may compare results with and without extreme observations when justified.

Any exclusion must be recorded.

---

## Causal Language Policy

ENUT 2024 is observational.

Unless a future approved methodology provides a valid causal identification strategy, experiments must use language such as:

- associated with
- related to
- observed relationship
- observed difference
- statistical association

Experiments must not automatically claim that commuting:

- causes
- produces
- leads to
- results in

changes in personal time.

---

## Statistical Significance

Statistical significance must not be treated as the sole criterion for scientific relevance.

Every result should consider:

- estimated effect size
- uncertainty interval
- direction
- consistency
- subgroup sample size
- robustness
- practical interpretation

A small p-value alone is not sufficient evidence for an important scientific finding.

---

## Multiple Testing

Because multiple outcomes, subgroups, and hypotheses may be evaluated, the system must record the number of comparisons performed.

Exploratory findings must be labeled as exploratory.

The Scientific Critic should flag cases where multiple comparisons could substantially increase false-positive risk.

---

## Reproducibility Requirements

Every experiment must be reproducible from:

```text
analytic_v1.parquet
+
ExperimentSpec
+
experiment code
```

The same inputs and software configuration should produce equivalent results.

Every experiment must receive a unique identifier.

Example:

```text
EXP-001
EXP-002
EXP-003
```

All experiment artifacts should be stored under:

```text
reports/experiments/<experiment_id>/
```

Example:

```text
reports/experiments/EXP-001/
├── spec.json
├── result.json
├── summary.md
├── model_output.json
└── figures/
```

---

## ExperimentSpec

Every experiment should be representable as a structured specification.

Example:

```json
{
  "experiment_id": "EXP-001",
  "research_question": "Which personal-time dimension shows the strongest association with commuting burden?",
  "hypothesis_ids": ["H1", "H2"],
  "dataset": "analytic_v1.parquet",
  "population": {
    "age_min": 18,
    "age_max": 65,
    "states": ["09", "15"]
  },
  "exposure": "commute_5h",
  "outcomes": [
    "sleep_weekday_min",
    "personal_hygiene_weekday_min",
    "household_conversation_weekday_min",
    "leisure_weekday_min"
  ],
  "covariates": [
    "work_weekday_min",
    "age",
    "sex",
    "state"
  ],
  "method": "weighted_regression",
  "survey_weight": "weight",
  "cluster": "cluster",
  "stratum": "stratum"
}
```

The exact schema may evolve, but changes must remain backward-compatible whenever practical and must be documented.

---

## ExperimentResult

Every completed experiment must produce a structured result.

Example:

```json
{
  "experiment_id": "EXP-001",
  "status": "completed",
  "sample_size": 0,
  "weighted_population": 0,
  "estimates": [],
  "quality_flags": [],
  "limitations": [],
  "supported_hypotheses": [],
  "unsupported_hypotheses": [],
  "inconclusive_hypotheses": [],
  "recommended_next_experiments": [],
  "scientific_interpretation": "",
  "decision": ""
}
```

The result must preserve uncertainty rather than reducing findings to a binary true/false conclusion.

---

## Scientific Critic

Every substantive result must be reviewed by the Scientific Critic before it can influence the next scientific decision.

The critic should evaluate:

- sample size
- subgroup size
- missingness
- model assumptions
- survey design
- robustness
- uncertainty
- alternative explanations
- inappropriate causal interpretation
- multiple testing
- unsupported claims
- reproducibility

The critic may return:

```text
VALID
UNCERTAIN
REQUIRES_REVISION
REQUIRES_HUMAN_REVIEW
```

A result marked `REQUIRES_REVISION` must not be treated as established evidence.

---

## Human Approval

Human approval is required when:

- the scientific population definition changes
- a primary outcome definition changes
- raw-data interpretation is ambiguous
- a derived feature changes meaning
- the analysis proposes a causal claim
- observations are excluded using a new rule
- the survey methodology is materially changed
- an experiment contradicts an existing scientific contract
- the Scientific Critic requests human review

---

## Evidence and Provenance

Every reported scientific claim must be traceable to:

```text
source data
↓
transformation
↓
experiment specification
↓
code execution
↓
numerical result
↓
scientific interpretation
```

The system must never invent numerical results.

Agent-generated hypotheses must be explicitly identified as hypotheses rather than established facts.

---

## Failure Conditions

An experiment must fail rather than silently continue when:

- required columns are missing
- the analytic dataset version is incorrect
- sample size falls below the approved minimum
- weights required by the experiment are invalid
- model execution fails
- results contain non-finite values unexpectedly
- join integrity has been violated
- the dataset fails required quality checks
- the ExperimentSpec is incomplete or invalid

Failure must produce a structured error report.

---

## Experiment Acceptance Criteria

An experiment may enter the shared research record only when:

- its specification is stored
- its input dataset version is recorded
- the execution completed successfully
- sample size is documented
- methodology is documented
- uncertainty is reported
- limitations are documented
- the Scientific Critic reviewed it
- results are reproducible
- the result leads to an explicit scientific decision

---

## Primary Success Criterion

The goal of the experiment system is not to maximize the number of analyses executed.

Its goal is to shorten the path from:

```text
scientific question
```

to:

```text
credible evidence
```

to:

```text
a better-informed next experiment
```

A successful discovery loop is therefore:

```text
Question
→ Evidence
→ Hypothesis
→ Experiment
→ Result
→ Critique
→ Updated Scientific Decision
→ Next Experiment
```
