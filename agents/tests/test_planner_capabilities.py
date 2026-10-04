"""Planner capability audit reads the engine's own export (no hard-coded proposals or variables).

Run from the repo root:  PYTHONPATH=agents python -m unittest discover -s agents/tests
"""
import json
import unittest
from pathlib import Path
from unittest import mock

import commute_lab.planner_tools as planner

ROOT = Path(__file__).resolve().parents[2]


def proposal(**extra):
    """A synthetic formal test (not a persisted artifact) built from PROP-008's shape."""
    base = json.loads((ROOT / "reports/discovery/local/candidates/PROP-008.json").read_text(encoding="utf-8"))
    keys = ("hypothesis_ids", "scientific_question", "experimental_test", "analysis_role", "population", "exposure",
            "outcome", "covariates", "method", "required_variables", "comparison_or_estimand",
            "expected_information_gain", "scientific_value", "required_engine_capabilities", "limitations",
            "result_interpretation_plan")
    p = {k: base[k] for k in keys}
    p["feasibility"] = {"status": "EXECUTABLE_NOW", "reason": "Binary moderator interaction is supported."}
    p["required_engine_capabilities"] = ["interaction_terms", "formal_between_group_comparison"]
    p.update(extra)
    return p


class EngineExportBridge(unittest.TestCase):
    def test_formal_interaction_counts_as_between_group_comparison(self):
        audit = planner.capability_audit()
        declared = json.loads(planner.ENGINE_CAPABILITIES.read_text(encoding="utf-8"))["supported"]
        self.assertTrue(declared["formal_interaction_coefficient_inference"])
        self.assertTrue(audit["supported"]["interaction_terms"])
        self.assertTrue(audit["supported"]["formal_between_group_comparison"])
        self.assertFalse(audit["supported"]["nonlinear_terms"])
        self.assertEqual(audit["evidence"]["engine_capabilities"], "metadata/experiment_engine_capabilities.json")
        self.assertEqual(sorted(audit["engine_binary_moderators"]),
                         sorted(json.loads(planner.ENGINE_CAPABILITIES.read_text(encoding="utf-8"))
                                ["interaction"]["binary_moderators"]))

    def test_without_engine_export_the_schema_audit_alone_applies(self):
        with mock.patch.object(planner, "ENGINE_CAPABILITIES", ROOT / "metadata" / "does_not_exist.json"):
            audit = planner.capability_audit()
        self.assertFalse(audit["supported"]["formal_between_group_comparison"])
        self.assertEqual(audit["engine_binary_moderators"], [])

    def test_engine_moderator_is_not_an_outside_covariate(self):
        errors, _ = planner._check(proposal(), "REV-001")
        self.assertFalse([e for e in errors if "covariates_outside_schema" in e or "contradicts the engine" in e], errors)
        with mock.patch.object(planner, "ENGINE_CAPABILITIES", ROOT / "metadata" / "does_not_exist.json"):
            old_errors, _ = planner._check(proposal(), "REV-001")
        self.assertTrue(any("EXECUTABLE_NOW contradicts the engine audit" in e for e in old_errors), old_errors)


if __name__ == "__main__":
    unittest.main()
