"""Machine-readable capabilities of the deterministic engine, derived from the strict contract.

Exported to metadata/experiment_engine_capabilities.json; scripts/validate_experiment_engine.py
checks that the committed file equals capabilities() so agents never rely on hard-coded knowledge.
"""
import typing

from .methods import METHODS
from .schemas import (CONTROLS, INTERACTION_HYPOTHESES, MODERATOR_LEVELS, MODERATOR_POPULATION_FIELD, OUTCOMES,
                      ExperimentSpec)

EXPORT_PATH = "metadata/experiment_engine_capabilities.json"


def _allowed(field: str) -> list:
    annotation = ExperimentSpec.model_fields[field].annotation
    args = typing.get_args(annotation)
    inner = typing.get_args(args[0]) if args and typing.get_origin(args[0]) is typing.Literal else args
    return list(inner)


def capabilities() -> dict:
    return {
        "contract": "metadata/experiment_contract.schema.json",
        "methods": sorted(METHODS),
        "exposure": _allowed("exposure"),
        "outcomes": list(OUTCOMES),
        "covariates": list(CONTROLS),
        "population_filters": ["states", "age_min", "age_max", "sexes"],
        "hypothesis_ids": _allowed("hypothesis_ids"),
        "uncertainty": _allowed("uncertainty"),
        "supported": {
            "weighted_linear_regression": True,
            "population_filter_stratification": True,
            "binary_moderator_main_effect": True,
            "exposure_x_binary_moderator_interaction": True,
            "formal_interaction_coefficient_inference": True,
            "derived_group_slopes_from_full_covariance": True,
            "nonlinear_terms": False,
            "multi_category_interactions": False,
            "multiple_moderators": False,
            "equivalence_testing": False,
            "p_values": False,
            "full_complex_survey_variance": False,
        },
        "interaction": {
            "spec_field": "interaction",
            "type": "binary_moderator",
            "binary_moderators": {m: list(levels) for m, levels in MODERATOR_LEVELS.items()},
            "moderators_requiring_both_levels_in_population": dict(MODERATOR_POPULATION_FIELD),
            "hypothesis_ids": list(INTERACTION_HYPOTHESES),
            "model": "Y = b0 + b_exposure X + b_moderator M + b_interaction X*M + covariates; "
                     "M = 1 if moderator == comparison_level, 0 if reference_level",
            "estimand": "b_interaction: difference in the exposure slope (comparison minus reference group)",
            "comparison_group_slope": "b_exposure + b_interaction with variance V_ee + V_ii + 2 V_ei",
            "moderator_in_covariates": "removed from covariates; its main effect enters once via the interaction",
            "missing_moderator": "excluded by model-specific complete cases, counted, never assigned to a group",
            "interpretation_statuses": ["INTERVAL_EXCLUDES_ZERO", "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO"],
        },
        "limitations": [
            "CR1 PSU-cluster uncertainty approximates, and is not, full ENUT complex-survey variance.",
            "Observational, cross-sectional data: estimates are associations, not causal effects.",
            "An interaction interval that includes zero is inconclusive; equivalence is not assessed.",
        ],
    }
