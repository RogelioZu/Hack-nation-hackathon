"""Internal model objects and explicit failures (not public JSON schemas)."""
from dataclasses import dataclass

import numpy as np

from .schemas import Estimate, InteractionResult


class ExperimentError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

    def as_dict(self):
        return {"status": "EXPERIMENT_FAILED", "code": self.code, "message": str(self)}


@dataclass
class ModelFit:
    estimate: Estimate
    diagnostics: dict
    # CR1-scaled PSU influence for the exposure, enabling paired outcome contrasts.
    cluster_influence: dict[tuple[str, str], float]
    sample_ids: tuple[str, ...]
    df: int
    # Present only when the spec requests an exposure x binary-moderator interaction.
    interaction: InteractionResult | None = None


def require(condition, code, message):
    if not condition:
        raise ExperimentError(code, message)


def direction(value):
    return "negative" if value < 0 else "positive" if value > 0 else "zero"

