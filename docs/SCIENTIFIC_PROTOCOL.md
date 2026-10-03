Research population:
18–65 years

Geographic scope:
CVE_ENT ∈ {09, 15}

Primary scientific question:
Which dimensions of personal time decrease the most as weekday
commuting burden increases?

Primary outcomes:
sleep_weekday_min
personal_hygiene_weekday_min (exclusive hygiene/grooming)
household_conversation_weekday_min (exclusive conversation with household members)
leisure_weekday_min (approved Phase 2B components)

Primary exposure:
weekday commuting minutes

Primary comparison:
+300 weekly commuting minutes

Primary heterogeneity:
sex
children in household

Interpretation:
observational association, not causal effect

## Approved Phase 2A decisions (2026-10-03)

The reviewed Phase 1 audit authorizes semantic staging only.

Primary domain: `CVE_ENT in {"09", "15"}` and age 18–65 inclusive.
The approved active-worker definition is:

```text
active_worker = P5_1 == "1" OR P5_2 in {"1","2","3","4","5","6"}
```

`P5_2 == "7"` indicates a job holder absent in the reference week. Retain
the person in staging but exclude from the primary commuting population.
`P5_2 == "8"` is outside that population. The approved rule is not replaced
by the broader official `COND_AEE` employment classification.

`P5_7 == "2"` and the questionnaire-skipped commuting pair imply a
flagged structural zero in commuting. Other commuting blanks are classified
by sequence and remain missing; no general blank-to-zero rule is allowed.
Sleep `99` special codes mean No sabe; derived sleep is missing while raw
strings are preserved.

Staging retains all TMODULO persons, including persons outside the primary
domain, with explicit domain/eligibility flags. Selection counts describe
potential analytic populations and do not remove records from staging.

Candidate outcome meanings and exact source mappings are recorded in
`metadata/mappings/staging_v1_features.json` and reviewed in
`reports/audit/phase2a_semantic_validation.md`. In particular, personal
hygiene and household conversation are narrow candidates, not silently
approved substitutes for every possible meaning of self-care/family time.
No leisure composite or experiment model is authorized in this phase.

TSDEM household composition must be aggregated to one row per LLAVEHOG
before a validated many-to-one join. All roster ages contribute to household
size; unknown ages do not imply absence of children or minors.

## Approved Phase 2B (2026-10-03; supersedes phase-specific limits above)

Phase 2A received human scientific approval. analytic_v1 uses the same primary
population plus resolved commuting; expected n=2,563. Zero weekday work,
zero commuting and extreme observations remain and are flagged for review.
The narrow hygiene and household-conversation meanings are approved under
the precise canonical names above, with unchanged numerical definitions.
Approved leisure sums weekday P6_18, P6_19 items 1–2, P6_20 items 1–2 and
P6_22 items 1–6. Exclude all P6_21, P6_23 and weekend components. Exact
pairs and participation rules are in DATA_CONTRACT.md. Unknown child/minor
indicators remain null. Stop for unresolved leisure semantics. No experiments
are authorized; stop after the canonical dataset and validation report.
