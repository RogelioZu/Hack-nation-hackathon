"""Dry-run feasibility check for an agent-proposed ExperimentSpec (stdin JSON -> stdout JSON).

Validates the strict schema and executes the deterministic engine without writing anything, so
runtime failures (e.g. RANK_DEFICIENT when a constant covariate is kept) surface at planning time.
It reports only validity and sample size: no coefficients reach the planner before the
experiment is selected and run through scripts/run_experiment.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiments.models import ExperimentError
from src.experiments.runner import run_experiment


def main():
    try:
        result = run_experiment(json.load(sys.stdin))
        report = {"valid": True, "sample_size": result.sample_size,
                  "model_count": len(result.estimates), "population_counts": result.population_counts}
    except ExperimentError as exc:
        report = {"valid": False, **exc.as_dict()}
    except ValueError as exc:  # malformed JSON
        report = {"valid": False, "status": "EXPERIMENT_FAILED", "code": "INPUT_ERROR", "message": str(exc)}
    print(json.dumps(report, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
