import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError
from src.experiments.schemas import ExperimentSpec

ROOT = Path(__file__).resolve().parents[1]


def spec_dict():
    return json.loads((ROOT / "experiments/EXP-001/spec.json").read_text(encoding="utf-8"))


class SchemaTests(unittest.TestCase):
    def test_spec_json_roundtrip(self):
        value = ExperimentSpec.model_validate(spec_dict())
        self.assertEqual(value, ExperimentSpec.model_validate_json(value.model_dump_json()))

    def test_unknown_variables_roles_methods_keys_and_casts_rejected(self):
        cases = [("outcomes", ["family_weekday_min"]), ("covariates", ["education"]),
                 ("exposure", "P5_9_1"), ("method", "eval"), ("survey_weight", "FAC_PER"),
                 ("dataset_version", "staging_v1"), ("include_unadjusted", "true"),
                 ("extra", True), ("sensitivity_analyses", ["remove_outliers"])]
        for key, value in cases:
            with self.subTest(key=key), self.assertRaises(ValidationError):
                data = spec_dict()
                data[key] = value
                ExperimentSpec.model_validate(data)

    def test_missing_required_and_duplicate_outcomes_rejected(self):
        data = spec_dict()
        del data["cluster"]
        with self.assertRaises(ValidationError):
            ExperimentSpec.model_validate(data)
        data = spec_dict()
        data["outcomes"] *= 2
        with self.assertRaises(ValidationError):
            ExperimentSpec.model_validate(data)

    def test_population_bounds_and_hypotheses(self):
        for changes in [{"age_min": 17}, {"age_min": 65, "age_max": 20}, {"states": ["9"]}, {"expected_n": "2563"}]:
            data = spec_dict()
            data["population"].update(changes)
            with self.assertRaises(ValidationError):
                ExperimentSpec.model_validate(data)
        data = spec_dict()
        data["outcomes"] = [data["outcomes"][0]]
        with self.assertRaises(ValidationError):
            ExperimentSpec.model_validate(data)

