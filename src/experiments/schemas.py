"""Strict, versioned public contract. Unknown keys and implicit casts are rejected."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_serializer, model_validator

OUTCOMES = (
    "sleep_weekday_min", "personal_hygiene_weekday_min",
    "household_conversation_weekday_min", "leisure_weekday_min",
)
CONTROLS = ("work_weekday_min", "age", "sex", "state")
Outcome = Literal["sleep_weekday_min", "personal_hygiene_weekday_min",
                  "household_conversation_weekday_min", "leisure_weekday_min"]
Control = Literal["work_weekday_min", "age", "sex", "state"]
# Approved binary moderators and their only admissible levels (docs/DATA_CONTRACT.md). The
# statistical code is generic: it codes indicator = 1 when moderator == comparison_level.
MODERATOR_LEVELS = {"sex": ("male", "female"), "state": ("09", "15"),
                    "has_child_u15": (False, True), "has_minor_u18": (False, True)}
Moderator = Literal["sex", "state", "has_child_u15", "has_minor_u18"]
# Population filter that must keep both levels of a moderator that is also a population field.
MODERATOR_POPULATION_FIELD = {"sex": "sexes", "state": "states"}
INTERACTION_HYPOTHESES = ("H3", "H4")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


def _omit_when_absent(data: dict, *keys: str) -> dict:
    """Optional extensions are left out of serialization when absent, so specs and results that
    predate them (EXP-001) keep byte-identical canonical JSON and hashes."""
    for key in keys:
        if data.get(key) is None:
            data.pop(key, None)
    return data


class Population(StrictModel):
    source: Literal["approved_analytic_v1"]
    states: list[Literal["09", "15"]] = Field(min_length=1)
    age_min: int = Field(ge=18, le=65)
    age_max: int = Field(ge=18, le=65)
    sexes: list[Literal["male", "female"]] = Field(min_length=1)
    expected_n: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def boundaries(self):
        if self.age_min > self.age_max:
            raise ValueError("age_min must not exceed age_max")
        if len(set(self.states)) != len(self.states) or len(set(self.sexes)) != len(self.sexes):
            raise ValueError("Repeated population categories")
        return self


class BinaryModeratorInteraction(StrictModel):
    """One exposure x binary-moderator interaction; the moderator main effect is always included."""
    type: Literal["binary_moderator"]
    moderator: Moderator
    reference_level: str | bool
    comparison_level: str | bool

    @model_validator(mode="after")
    def levels(self):
        allowed = MODERATOR_LEVELS[self.moderator]
        for level in (self.reference_level, self.comparison_level):
            if not any(type(level) is type(a) and level == a for a in allowed):
                raise ValueError(f"{self.moderator} levels must be among {list(allowed)} (exact type)")
        if self.reference_level == self.comparison_level:
            raise ValueError("reference_level and comparison_level must differ")
        return self


class ExperimentSpec(StrictModel):
    schema_version: Literal["1.0"]
    experiment_id: str = Field(pattern=r"^EXP-[0-9]{3,}$")
    research_question: str = Field(min_length=10)
    hypothesis_ids: list[Literal["H1", "H2", "H3", "H4"]] = Field(min_length=1)
    dataset_version: Literal["analytic_v1"]
    population: Population
    exposure: Literal["commute_5h"]
    outcomes: list[Outcome] = Field(min_length=1)
    covariates: list[Control]
    method: Literal["weighted_linear_regression"]
    survey_weight: Literal["weight"]
    cluster: Literal["cluster"]
    stratum: Literal["stratum"]
    sensitivity_analyses: list[Literal["exclude_zero_weekday_work"]]
    missingness_policy: Literal["model_specific_complete_case"]
    uncertainty: Literal["psu_cluster_CR1_t"]
    confidence_level: Literal[0.95]
    include_unadjusted: bool
    interaction: BinaryModeratorInteraction | None = None

    @model_validator(mode="after")
    def unique_lists(self):
        for key in ("outcomes", "covariates", "hypothesis_ids", "sensitivity_analyses"):
            values = getattr(self, key)
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate entries in {key}")
        if "H2" in self.hypothesis_ids and len(self.outcomes) < 2:
            raise ValueError("H2 requires at least two outcomes")
        heterogeneity = set(self.hypothesis_ids) & set(INTERACTION_HYPOTHESES)
        if self.interaction is None and heterogeneity:
            raise ValueError(f"{sorted(heterogeneity)} require an interaction specification")
        if self.interaction is not None:
            if set(self.hypothesis_ids) - set(INTERACTION_HYPOTHESES):
                raise ValueError(f"an interaction spec tests heterogeneity hypotheses {INTERACTION_HYPOTHESES} only")
            if self.interaction.moderator == self.exposure:
                raise ValueError("moderator must differ from the exposure")
            field = MODERATOR_POPULATION_FIELD.get(self.interaction.moderator)
            kept = set(getattr(self.population, field)) if field else None
            if kept is not None and not {self.interaction.reference_level, self.interaction.comparison_level} <= kept:
                raise ValueError(f"population.{field} must keep both moderator levels (an empty group cannot be compared)")
        return self

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        return _omit_when_absent(handler(self), "interaction")


class Interval(StrictModel):
    lower: float
    upper: float
    confidence_level: float = Field(gt=0, lt=1)
    adjustment: str


class Coefficient(StrictModel):
    term: str
    estimate: float
    standard_error: float = Field(ge=0)
    interval: Interval


class Estimate(StrictModel):
    model_id: str
    variant: str
    outcome: Outcome
    exposure: Literal["commute_5h"]
    coefficient: float
    standard_error: float = Field(ge=0)
    direction: Literal["negative", "zero", "positive"]
    interval: Interval
    simultaneous_outcome_interval: Interval
    units: str
    n: int = Field(gt=0)
    weighted_population: float = Field(gt=0)
    coefficients: list[Coefficient]
    covariance: list[list[float]]
    provenance: dict[str, JsonValue]


class SlopeEstimate(StrictModel):
    estimate: float
    standard_error: float = Field(ge=0)
    interval: Interval


class ModeratorGroup(StrictModel):
    role: Literal["reference", "comparison"]
    level: str | bool
    n: int = Field(ge=0)
    weighted_population: float = Field(ge=0)


class InteractionResult(StrictModel):
    """Machine-readable binary-moderator interaction for one fitted model."""
    model_id: str
    variant: str
    outcome: Outcome
    exposure: Literal["commute_5h"]
    moderator: Moderator
    reference_level: str | bool
    comparison_level: str | bool
    coding: str
    moderator_term: str
    interaction_term: str
    reference_group_slope: SlopeEstimate
    comparison_group_slope: SlopeEstimate
    comparison_slope_method: str
    moderator_main_effect: SlopeEstimate
    interaction: SlopeEstimate
    interpretation_status: Literal["INTERVAL_EXCLUDES_ZERO", "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO"]
    interpretation: str
    equivalence_assessed: bool
    input_n: int = Field(ge=0)
    analysis_n: int = Field(gt=0)
    excluded_n: int = Field(ge=0)
    missing_moderator_n: int = Field(ge=0)
    excluded_only_for_missing_moderator_n: int = Field(ge=0)
    groups: list[ModeratorGroup] = Field(min_length=2, max_length=2)
    limitations: list[str]


class ExperimentResult(StrictModel):
    schema_version: Literal["1.0"]
    experiment_id: str
    status: Literal["EXPERIMENT_COMPLETED"]
    dataset_version: Literal["analytic_v1"]
    sample_size: int = Field(gt=0)
    weighted_population: float = Field(gt=0)
    estimates: list[Estimate]
    confidence_intervals: dict[str, Interval]
    model_diagnostics: dict[str, JsonValue]
    sensitivity_results: list[dict[str, JsonValue]]
    quality_flags: list[str]
    limitations: list[str]
    scientific_interpretation: list[str]
    supported_hypotheses: list[dict[str, str]]
    unsupported_hypotheses: list[dict[str, str]]
    inconclusive_hypotheses: list[dict[str, str]]
    candidate_next_experiments: list[dict[str, JsonValue]]
    ranking: dict[str, JsonValue]
    population_counts: list[dict[str, JsonValue]]
    missingness: dict[str, int]
    transformations: list[str]
    provenance: dict[str, JsonValue]
    review_status: Literal["REQUIRES_HUMAN_REVIEW"]
    interactions: list[InteractionResult] | None = None

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        return _omit_when_absent(handler(self), "interactions")

