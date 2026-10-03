# Canonical analytic_v1 contract — Phase 2B

Human-approved 2026-10-03. Output: `data/processed/analytic_v1.parquet`.
One row per primary person; expected n=2,563. A discrepancy stops publication.

## Population

States 09/15; age 18–65 inclusive; active_worker = P5_1=1 OR P5_2 in 1–6;
employment_reference_week_absent=false (P5_2 is not 7); resolved commuting.
P5_2=8 is outside the active population. No positive-work, positive-commute,
complete-case or outlier filter is added. Zero times are flagged, not removed.

## Canonical columns

Sources are TMODULO unless stated otherwise. All weekday times are total
minutes Monday–Friday, not daily averages. Every output column has exact
machine-readable lineage in `metadata/analytic_v1_manifest.json`.

| Variable | Source | Definition / missingness |
|---|---|---|
| person_id | LLAVEMOD | Unique nonempty exact string |
| household_id | LLAVEHOG | Nonempty exact string |
| state | CVE_ENT | String 09 or 15 |
| sex | SEXO | 1=male, 2=female; raw retained |
| age | EDAD_V | Completed years 18–65; unknown codes do not enter age domain |
| active_worker | P5_1, P5_2 | Approved boolean rule above |
| employment_reference_week_absent | P5_2 | Code 7; retained in staging, excluded here |
| commute_weekday_min | P5_9_1/P5_9_2; P5_7 and employment/work flow | 60×hours+minutes; approved virtual-only skipped pair gives flagged zero; other blanks remain missing |
| commute_5h | commute_weekday_min | Divide by 300; inherits exposure provenance |
| commute_structural_zero | P5_7, P5_9_1/P5_9_2; employment flow | True only for approved virtual-only skip |
| work_weekday_min | P5_8_1_1/2, P5_8_2_1/2; P5_5, P5_7, P5_1, P5_2 | Select applicable work branches: modality 1 first, 2 second, 3 both; P5_5=2–6 with unasked modality uses first as all work. Required missing branch propagates null |
| work_modality | P5_7, P5_5 | 1=in_person, 2=virtual, 3=hybrid; unasked remains null |
| sleep_weekday_min | P6_1_1_1/P6_1_1_2 | Exclusive sleep including naps; 99 in either field is No sabe/null |
| personal_hygiene_weekday_min | P6_1_3_1/P6_1_3_2 | Exclusive hygiene/grooming; not all self-care |
| household_conversation_weekday_min | P6_21_1, P6_21A_1_1/P6_21A_1_2 | Exclusive conversation with household members; indicator 2 plus blank pair gives flagged zero; not total family time |
| leisure_weekday_min | Eleven weekday pairs below | Sum fully resolved components only; never skip missing components |
| has_child_u15 | TSDEM.LLAVEHOG, LLAVESDE, EDAD | Any known age <15; if none confirmed and some ages unknown, null |
| has_minor_u18 | Same TSDEM fields | Threshold <18; unknown remains null |
| household_size | TSDEM.LLAVEHOG, LLAVESDE | All roster persons aggregated per household before many-to-one join |
| weight | FAC_PER | Positive finite numeric factor; raw retained |
| stratum | EST_DIS | Nonempty exact string |
| cluster | UPM_DIS | Nonempty exact string |

These four time outcomes are the canonical primary outcomes. No other
scientific covariates are approved here. Raw sources, parser statuses,
component minutes and review flags are provenance/QA fields, not new controls.

## Leisure components — documented before derivation

Each row uses 60×hours+minutes for participation=1 with a valid pair.
That row's participation=2 and two blank fields implies a structural zero.
Other/unknown participation, partial or unexplained blanks, invalid minutes,
or reported time on a skipped branch stops publication. No global zero fill.

| Component | Participation | Hours | Minutes |
|---|---|---|---|
| Sport/exercise | P6_18 | P6_18A_1 | P6_18A_2 |
| Arts | P6_19_1 | P6_19A_1_1 | P6_19A_1_2 |
| Games/hobbies | P6_19_2 | P6_19A_2_1 | P6_19A_2_2 |
| Entertainment venues | P6_20_1 | P6_20A_1_1 | P6_20A_1_2 |
| Cultural venues | P6_20_2 | P6_20A_2_1 | P6_20A_2_2 |
| Screen entertainment | P6_22_1 | P6_22A_1_1 | P6_22A_1_2 |
| Audio entertainment | P6_22_2 | P6_22A_2_1 | P6_22A_2_2 |
| Recreational reading | P6_22_3 | P6_22A_3_1 | P6_22A_3_2 |
| Unpaid social posting | P6_22_4 | P6_22A_4_1 | P6_22A_4_2 |
| Recreational email/social browsing | P6_22_5 | P6_22A_5_1 | P6_22A_5_2 |
| Other recreational Internet | P6_22_6 | P6_22A_6_1 | P6_22A_6_2 |

Exclude all P6_21, P6_23 and weekend fields. Source components do not overlap
household conversation; this does not prove reported times never overlap
temporally. This composite is not the broader weekly ACTIV_CONVIV aggregate.

Evidence: archived questionnaire pp23–24 and DDI catalog 1127, V4071–V4093
and V4116–V4143. Exact per-field IDs and rules are in
`metadata/mappings/analytic_v1_leisure.json`. V4082's label contains the typo
"vienes"; the questionnaire and paired minute field confirm Monday–Friday.

## Phase boundaries

Phase 2A and its full staging are approved historical artifacts. Canonical
renames do not alter numeric values. Old broad aliases are absent from the
analytic output. Original raw fields and all survey design fields are
preserved for traceability. No outlier deletion, clipping or winsorization.
Technical EXPERIMENT_READY is not authorization to run an experiment;
final human approval remains pending. No regressions, tests of H1–H4 or EXP-001.

## Historical Phase 1 / Phase 2A contract (superseded where stated above)

The following records the earlier staging definitions and phase-specific
limits, not current analytic names or Phase 2B authorization.

person_id
source: TMODULO.LLAVEMOD
type: string
nullable: false
unique: true


household_id
source: TMODULO.LLAVEHOG
type: string
nullable: false


state
source: TMODULO.CVE_ENT
type: category
allowed: 09, 15


commute_weekday_min
source:
  TMODULO.P5_9_1
  TMODULO.P5_9_2

formula:
  hours * 60 + minutes

unit:
  total minutes Monday-Friday


commute_5h
formula:
  commute_weekday_min / 300


sleep_weekday_min
source:
  P6_1_1_1
  P6_1_1_2


weight
source:
  FAC_PER


stratum
source:
  EST_DIS


cluster
source:
  UPM_DIS


## Phase 2A staging contract (2026-10-03)

Output: `data/interim/staging_v1.parquet`, one row per original TMODULO person.
All 694 original module columns, including raw time components and survey
design fields, are retained unchanged as strings. Raw CSVs remain immutable.

The `state` restriction above applies to the primary analytic domain, not
to the complete staging table. Staging also preserves other state codes.
`in_geographic_domain`, `in_age_domain`, and `primary_commuting_population`
record selection without dropping persons. `primary_commuting_population`
implements the approved rule in SCIENTIFIC_PROTOCOL.md, excluding absent
workers and code 8; it does not impose complete-case outcome filtering.

The complete machine-readable candidate feature contract is
`metadata/mappings/staging_v1_features.json`. It documents source tables,
columns, formulas, units, special codes, missingness and approval status for
every requested candidate. Time units are totals for Monday–Friday, not a
daily average. `commute_5h` divides that total by 300.

Each time parser preserves the raw pair and produces explicit statuses:
`valid`, `special_code`, `structural_blank`, `structural_zero`,
`unresolved_blank`, `invalid`, or `flow_conflict`. Special codes are specific
to the field, read from the archived INEGI DDI. Partial pairs never become
zero. Required missing work branches invalidate the total rather than being
ignored by a skip-missing sum.

The candidate `selfcare_weekday_min` uses exclusive hygiene/grooming
P6_1_3_1/P6_1_3_2. `family_weekday_min` uses exclusive household conversation
P6_21A_1_1/P6_21A_1_2, with P6_21_1=2 nonparticipation explicitly coded as a
flagged zero only when its skipped time pair is blank. These narrow meanings
await scientific review. Work time selects/sums the applicable P5_8 branches
according to questionnaire instructions; it covers all jobs.

Weekend, eating and `check_*` fields are auxiliary reconciliation fields.
`check_personal_weekly_min` reconstructs all-week P6_1 items 1–3 plus P6_23
items 1–2. `check_social_entertainment_weekly_min` reconstructs all-week
P6_18–P6_22. These auxiliary checks use explicit participation indicators for
structural zeros; they are not new analytic outcomes or an approved leisure
definition. The weekly checks are compared to corresponding TVAR_CREA
hours only on jointly nonmissing records.

Age codes 98/99 remain unknown; code 97 is top-coded 97+. A confirmed child
is sufficient for a true household indicator. If no child is confirmed and
any roster age is unknown, the corresponding indicator is null.

Do not write `data/processed/analytic_v1.parquet` during Phase 2A.
