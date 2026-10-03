"""Read-only input validation plus complete pipeline/experiment test suite."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local_deps"))

from src.experiments.runner import load_approved, sha


def main():
    immutable = [ROOT / "data/processed/analytic_v1.parquet", ROOT / "data/interim/staging_v1.parquet",
                 ROOT / "metadata/analytic_v1_manifest.json"] + sorted((ROOT / "data/raw/enut_2024").glob("*.csv"))
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in immutable}
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    test_result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not test_result.wasSuccessful():
        return 1
    data, manifest, digest, _ = load_approved(ROOT)
    after = {p.relative_to(ROOT).as_posix(): sha(p) for p in immutable}
    if before != after:
        raise RuntimeError("Immutable inputs changed")
    for name, expected in manifest["raw_data_hashes"].items():
        if sha(ROOT / "data/raw/enut_2024" / name) != expected:
            raise RuntimeError(f"Raw hash differs: {name}")
    if sha(ROOT / "data/interim/staging_v1.parquet") != manifest["staging_sha256"]:
        raise RuntimeError("Staging hash differs")
    checks = {"status": "PASS", "tests_run": test_result.testsRun,
              "failures": len(test_result.failures), "errors": len(test_result.errors),
              "immutable_hashes": after, "raw_and_staging_match_approved_manifest": True,
              "analytic_n": len(data), "row_delta_from_phase2b": len(data)-manifest["row_count"],
              "missingness_delta_from_phase2b": {c: int(data[c].isna().sum())-v["missing"] for c,v in manifest["missingness"].items()},
              "independent_statistical_check": "All 16 EXP-001 models and nonuniform-weight synthetic fixture match statsmodels WLS + cluster CR1",
              "paired_contrast_check": "Matches regression of outcome difference on synthetic shared sample",
              "dataset_rebuilt": False, "reason": "Phase 3 explicitly prohibits modifying approved analytic_v1; transformations unchanged"}
    output = ROOT / "reports/experiments/EXP-001"
    output.mkdir(parents=True, exist_ok=True)
    (output / "engine_validation.json").write_text(json.dumps(checks, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in checks.items() if k not in ["immutable_hashes", "missingness_delta_from_phase2b"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
