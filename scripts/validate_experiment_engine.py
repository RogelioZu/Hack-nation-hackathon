"""Read-only experiment-engine validation from the committed analytic_v1 alone.

Raw ENUT CSVs, staging_v1 and the pipeline tests belong to the upstream pipeline
repository; this script neither reads nor reports them.
"""
import json
import sys
import typing
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local_deps"))

from pydantic.json_schema import models_json_schema

from src.experiments.methods import METHODS
from src.experiments.models import ExperimentError
from src.experiments.runner import canonical_json, load_approved, run_experiment, sha
from src.experiments.schemas import ExperimentResult, ExperimentSpec

IMMUTABLE = ["data/processed/analytic_v1.parquet", "metadata/analytic_v1_manifest.json",
             "metadata/analytic_v1_experiment_approval.json"]
SPEC = "experiments/EXP-001/spec.json"
REFERENCE = "reports/experiments/EXP-001/result.json"
RUN_RECORD = "reports/experiments/EXP-001/validation.json"
OUTPUT = "reports/experiments/EXP-001/engine_validation.json"
# Provenance describing the code, protocol text and runtime of a run; it legitimately
# changes with source edits or line endings, never with the estimates.
ENVIRONMENT_PROVENANCE = {"code_sha256", "code_fingerprints", "protocol_fingerprints", "runtime"}


def differences(reference, actual, path=""):
    """Paths whose values or types differ, skipping environment provenance. Floats must be equal."""
    if isinstance(reference, dict) and isinstance(actual, dict):
        found = []
        for key in sorted(set(reference) | set(actual)):
            if path.endswith("provenance") and key in ENVIRONMENT_PROVENANCE:
                continue
            if key not in reference or key not in actual:
                found.append(f"{path}.{key}")
            else:
                found += differences(reference[key], actual[key], f"{path}.{key}")
        return found
    if isinstance(reference, list) and isinstance(actual, list):
        if len(reference) != len(actual):
            return [path]
        return [d for i, (a, b) in enumerate(zip(reference, actual)) for d in differences(a, b, f"{path}[{i}]")]
    return [] if type(reference) is type(actual) and reference == actual else [path]


def numeric_leaves(value):
    if isinstance(value, dict):
        return sum(numeric_leaves(v) for v in value.values())
    if isinstance(value, list):
        return sum(numeric_leaves(v) for v in value)
    return int(isinstance(value, (int, float)) and not isinstance(value, bool))


def check(condition, code, message):
    if not condition:
        raise ExperimentError(code, message)


def main():
    before = {p: sha(ROOT / p) for p in IMMUTABLE}

    # Approved dataset, manifest and contract consistency (hash, rows, variables, missingness).
    data, manifest, digest, variables = load_approved(ROOT)
    check(manifest["dataset_path"] == IMMUTABLE[0], "MANIFEST_DRIFT", "Manifest dataset_path differs")

    # Public contract: committed JSON Schema equals the strict Pydantic models.
    _, generated = models_json_schema([(ExperimentSpec, "validation"), (ExperimentResult, "validation")])
    committed = json.loads((ROOT / "metadata/experiment_contract.schema.json").read_text(encoding="utf-8"))
    check(committed["$defs"] == generated["$defs"], "SCHEMA_DRIFT", "experiment_contract.schema.json differs from schemas.py")
    spec_data = json.loads((ROOT / SPEC).read_text(encoding="utf-8"))
    ExperimentSpec.model_validate(spec_data)

    # Closed method registry agrees with the schema.
    allowed = set(typing.get_args(ExperimentSpec.model_fields["method"].annotation))
    check(set(METHODS) == allowed == {"weighted_linear_regression"}, "METHOD_REGISTRY_DRIFT",
          f"Registry {sorted(METHODS)} vs schema {sorted(allowed)}")

    # Experiment-engine tests only.
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    tests = unittest.TextTestRunner(verbosity=2).run(suite)
    check(tests.wasSuccessful(), "TESTS_FAILED", f"{len(tests.failures)} failures, {len(tests.errors)} errors")

    # EXP-001: repeated execution and exact numerical equivalence with the committed result.
    first, second = run_experiment(spec_data), run_experiment(spec_data)
    check(canonical_json(first.model_dump()) == canonical_json(second.model_dump()),
          "NONREPRODUCIBLE_RESULT", "Repeated execution differs")
    actual = json.loads(json.dumps(first.model_dump(), allow_nan=False))
    recorded = json.loads((ROOT / RUN_RECORD).read_text(encoding="utf-8"))["result_sha256"]
    check(sha(ROOT / REFERENCE) == recorded, "RESULT_BYTES_DRIFT",
          f"{REFERENCE} bytes differ from result_sha256 in {RUN_RECORD}")
    reference = json.loads((ROOT / REFERENCE).read_text(encoding="utf-8"))
    ExperimentResult.model_validate(reference)
    drift = differences(reference, actual)
    check(not drift, "EXP001_DRIFT", f"Committed result differs at {drift[:10]}")
    environment_changes = sorted(k for k in ENVIRONMENT_PROVENANCE
                                 if reference["provenance"].get(k) != actual["provenance"].get(k))

    after = {p: sha(ROOT / p) for p in IMMUTABLE}
    check(before == after, "DATASET_CHANGED", "Approved inputs changed during validation")

    record = {
        "status": "PASS",
        "scope": "experiment engine only; upstream ENUT pipeline inputs and tests are not part of this repository",
        "approved_inputs_sha256": after,
        "analytic_hash_matches_manifest_and_approval": True,
        "analytic_n": len(data),
        "row_delta_from_manifest": len(data) - manifest["row_count"],
        "canonical_variables_checked": len(variables),
        "missingness_matches_manifest": True,
        "json_schema_matches_models": True,
        "supported_methods": sorted(METHODS),
        "experiment_engine_tests_run": tests.testsRun,
        "experiment_engine_test_failures": len(tests.failures) + len(tests.errors),
        "exp001_result_bytes_match_validation_record": True,
        "exp001_repeated_execution_identical": True,
        "exp001_numeric_values_compared": numeric_leaves(reference),
        "exp001_numerical_differences": 0,
        "exp001_non_environment_differences": 0,
        "exp001_environment_provenance_changed": environment_changes,
        "analytic_v1_unchanged": True,
        "dataset_rebuilt": False,
    }
    (ROOT / OUTPUT).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExperimentError, OSError, ValueError) as exc:
        error = exc.as_dict() if isinstance(exc, ExperimentError) else {"status": "VALIDATION_FAILED", "message": str(exc)}
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
