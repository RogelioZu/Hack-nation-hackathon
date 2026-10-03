"""Strict, versioned public contract. Unknown keys and implicit casts are rejected."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

OUTCOMES = (
    "sleep_weekday_min", "personal_hygiene_weekday_min",
    "household_conversation_weekday_min", "leisure_weekday_min",
)
CONTROLS = ("work_weekday_min", "age", "sex", "state")
Outcome = Literal["sleep_weekday_min", "personal_hygiene_weekday_min",
                  "household_conversation_weekday_min", "leisure_weekday_min"]
Control = Literal["work_weekday_min", "age", "sex", "state"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


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


class ExperimentSpec(StrictModel):
    schema_version: Literal["1.0"]
    experiment_id: str = Field(pattern=r"^EXP-[0-9]{3,}$")
    research_question: str = Field(min_length=10)
    hypothesis_ids: list[Literal["H1", "H2"]] = Field(min_length=1)
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

    @model_validator(mode="after")
    def unique_lists(self):
        for key in ("outcomes", "covariates", "hypothesis_ids", "sensitivity_analyses"):
            values = getattr(self, key)
            if len(values) != len(set(values)):
                raise ValueError(f"Duplicate entries in {key}")
        if "H2" in self.hypothesis_ids and len(self.outcomes) < 2:
            raise ValueError("H2 requires at least two outcomes")
        return self


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

