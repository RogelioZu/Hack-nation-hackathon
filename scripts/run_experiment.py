"""CLI: repeated deterministic execution, then atomic result publication."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local_deps"))

from src.experiments.models import ExperimentError
from src.experiments.report import render_summary
from src.experiments.runner import canonical_json, run_experiment, sha
from src.experiments.schemas import ExperimentResult, ExperimentSpec


def write_atomic(path, content):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8", newline="\n")  # same bytes and hashes on every OS
    os.replace(temp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    try:
        spec_data = json.loads(args.spec.read_text(encoding="utf-8"))
        before = sha(ROOT / "data/processed/analytic_v1.parquet")
        first = run_experiment(spec_data)
        second = run_experiment(spec_data)
        if canonical_json(first.model_dump()) != canonical_json(second.model_dump()):
            raise ExperimentError("NONREPRODUCIBLE_RESULT", "Repeated execution differs")
        after = sha(ROOT / "data/processed/analytic_v1.parquet")
        if before != after:
            raise ExperimentError("DATASET_CHANGED", "Approved analytic dataset changed")
        result_text = json.dumps(first.model_dump(), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        ExperimentResult.model_validate_json(result_text)
        out = ROOT / "reports/experiments" / first.experiment_id
        out.mkdir(parents=True, exist_ok=True)
        write_atomic(out / "result.json", result_text)
        write_atomic(out / "summary.md", render_summary(first))
        write_atomic(out / "spec.json", json.dumps(spec_data, indent=2, ensure_ascii=False) + "\n")
        checks = {"status": "PASS", "identical_spec_identical_result": True,
                  "analytic_sha256_before": before, "analytic_sha256_after": after,
                  "result_sha256": sha(out / "result.json"), "schema_roundtrip": True,
                  "sample_size": first.sample_size, "model_count": len(first.estimates)}
        write_atomic(out / "validation.json", json.dumps(checks, indent=2) + "\n")
        print(json.dumps(checks, indent=2))
        print(first.status)
    except (ExperimentError, OSError, ValueError) as exc:
        error = exc.as_dict() if isinstance(exc, ExperimentError) else {"status": "EXPERIMENT_FAILED", "code": "INPUT_ERROR", "message": str(exc)}
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
