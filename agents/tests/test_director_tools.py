"""Discovery Director tools: validation rules, capability-aware reruns and append-only persistence.

Run from the repo root:  PYTHONPATH=agents python -m unittest discover -s agents/tests
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from commute_lab import director_tools as director
from commute_lab import research_state
from commute_lab.planner_tools import capability_audit

WAITING = {
    "candidate_proposal_ids": ["PROP-003", "PROP-005", "PROP-008", "PROP-009"],
    "preferred_proposal_id": "PROP-003",
    "best_executable_proposal_id": "PROP-005",
    "decision_status": "WAITING_FOR_ENGINE_CAPABILITY",
    "scientific_rationale": "PROP-003 is a formal commute by sex interaction test for sleep, the outcome with the "
                            "strongest negative point estimate in EXP-001, and directly addresses HYP-005.",
    "expected_learning": "An interval for the interaction coefficient that excludes zero would indicate that the "
                         "association differs by sex; an interval including zero would leave the question open.",
    "alternatives": [
        {"proposal_id": "PROP-005", "reason_not_selected": "It is a women-only exploratory model; it cannot "
                                                           "establish a difference between women and men."},
        {"proposal_id": "PROP-008", "reason_not_selected": "It also needs a covariate outside the schema, so it "
                                                           "depends on a larger engine extension."},
        {"proposal_id": "PROP-009", "reason_not_selected": "It targets leisure, whose EXP-001 interval was wider, "
                                                           "so sleep is the more informative first moderator test."},
    ],
    "capability_check": {"currently_executable": False, "missing_capabilities": ["interaction_terms"]},
    "uncertainties": ["Observational, cross-sectional data; CR1 PSU-clustered variance is an approximation."],
    "human_constraints_respected": ["REV-001: separate subgroup models are not treated as heterogeneity tests."],
    "next_action": "Request the human-approved engine extension for interaction terms, then rerun the Director.",
}


def before_extension():
    """The engine as it was for DEC-001: no interaction field in the schema, no capability export."""
    audit = capability_audit()
    audit = {**audit, "supported": {**audit["supported"], "interaction_terms": False,
                                    "formal_between_group_comparison": False}}
    patches = [mock.patch.object(director, "capability_audit", return_value=audit),
               mock.patch.object(director, "_engine_capabilities", return_value={})]

    class Both:
        def __enter__(self):
            for p in patches:
                p.start()

        def __exit__(self, *exc):
            for p in patches:
                p.stop()
    return Both()


READY = {**copy.deepcopy(WAITING), "decision_status": "READY_TO_EXECUTE", "best_executable_proposal_id": "PROP-003",
         "capability_check": {"currently_executable": True, "missing_capabilities": []},
         "next_action": "Request human approval of this decision before the runner builds the spec."}
READY["alternatives"] = [
    {"proposal_id": "PROP-005", "reason_not_selected": "It is a women-only exploratory model; it cannot establish "
                                                       "a difference between women and men."},
    {"proposal_id": "PROP-008", "reason_not_selected": "It tests the child moderator, a secondary question after the "
                                                       "sex difference that EXP-001 left open for sleep."},
    {"proposal_id": "PROP-009", "reason_not_selected": "It targets leisure, whose EXP-001 interval was wider, so "
                                                       "sleep is the more informative first moderator test."},
]


def validate(decision):
    return json.loads(director.validate_discovery_decision(decision))


class ReadTools(unittest.TestCase):
    def test_reads_persisted_artifacts_and_live_capabilities(self):
        state = json.loads(director.read_research_state())
        self.assertTrue(state["ok"])
        self.assertEqual(state["state_next_action"], research_state.build_state()[0]["next_action"])
        self.assertEqual({h["hypothesis_id"] for h in state["approved_hypotheses"]}, {"HYP-005", "HYP-007", "HYP-008"})
        proposals = json.loads(director.read_candidate_proposals())["proposals"]
        self.assertEqual([p["proposal_id"] for p in proposals], WAITING["candidate_proposal_ids"])
        with before_extension():
            caps = json.loads(director.read_engine_capabilities())["proposals"]
        self.assertFalse(caps["PROP-003"]["currently_executable"])
        self.assertEqual(caps["PROP-003"]["missing_capabilities"], ["interaction_terms"])
        self.assertTrue(caps["PROP-005"]["currently_executable"])

    def test_current_engine_supports_binary_moderators(self):
        caps = json.loads(director.read_engine_capabilities())["proposals"]
        for pid, moderator in (("PROP-003", "sex"), ("PROP-008", "has_child_u15"), ("PROP-009", "sex")):
            self.assertTrue(caps[pid]["currently_executable"], caps[pid])
            self.assertEqual(caps[pid]["checks"]["binary_moderators"], [moderator])
        self.assertEqual(caps["PROP-005"]["checks"]["binary_moderators"], [])


class Validation(unittest.TestCase):
    """Rules checked against the engine as it was for DEC-001 (interactions not yet available)."""

    def setUp(self):
        self.engine = before_extension()
        self.engine.__enter__()
        self.addCleanup(self.engine.__exit__)

    def assertRejected(self, change, fragment):
        decision = copy.deepcopy(WAITING)
        change(decision)
        result = validate(decision)
        self.assertFalse(result["valid"], "expected a rejection")
        self.assertTrue(any(fragment in e for e in result["errors"]), result["errors"])

    def test_valid_waiting_decision(self):
        self.assertEqual(validate(WAITING)["errors"], [])

    def test_nonexistent_proposal(self):
        self.assertRejected(lambda d: d.update(preferred_proposal_id="PROP-404"), "not an active proposal")

    def test_all_alternatives_must_be_explained(self):
        self.assertRejected(lambda d: d["alternatives"].pop(), "alternatives must cover")
        self.assertRejected(lambda d: d["alternatives"][0].update(reason_not_selected="Weaker."), "explain why")

    def test_feasibility_must_not_override_science(self):
        def prefer_005(d):
            d.update(preferred_proposal_id="PROP-005", decision_status="READY_TO_EXECUTE",
                     capability_check={"currently_executable": True, "missing_capabilities": []})
            d["alternatives"] = [{"proposal_id": "PROP-003", "reason_not_selected": "It is blocked by the engine "
                                  "today, while the women-only model can run now."}] + d["alternatives"][1:]
        self.assertRejected(prefer_005, "feasibility must not override scientific value")

    def test_status_and_capability_must_match_the_engine(self):
        self.assertRejected(lambda d: d.update(decision_status="READY_TO_EXECUTE"), "expected WAITING")
        self.assertRejected(lambda d: d.update(capability_check={"currently_executable": True,
                                                                 "missing_capabilities": []}), "capability_check")
        self.assertRejected(lambda d: d.update(best_executable_proposal_id=None), "can run today")

    def test_exploratory_subgroup_is_not_a_heterogeneity_test(self):
        self.assertRejected(lambda d: d["alternatives"][0].update(
            reason_not_selected="PROP-005 would establish that women and men differ, but it is less complete."),
            "exploratory subgroup")

    def test_no_selection_by_significance(self):
        self.assertRejected(lambda d: d.update(scientific_rationale=d["scientific_rationale"] +
                                               " It is the most likely to be statistically significant."),
                            "significance")

    def test_no_causal_claims(self):
        self.assertRejected(lambda d: d.update(expected_learning="It shows how commuting reduces sleep for "
                                                                 "women and men in the population."), "causal")

    def test_no_invented_numbers_or_ids(self):
        self.assertRejected(lambda d: d.update(scientific_rationale=d["scientific_rationale"] +
                                               " The sex gap is -12.5 minutes."), "numbers not found")
        self.assertRejected(lambda d: d.update(scientific_rationale=d["scientific_rationale"] + " See HYP-404."),
                            "does not exist")

    def test_no_experiment_id_and_no_execution(self):
        self.assertRejected(lambda d: d.update(next_action="Run PROP-003 as EXP-002 after the engine extension "
                                                           "is approved by the team."), "new experiment id")
        self.assertRejected(lambda d: d.update(experiment_id="EXP-002"), "decides only")
        self.assertRejected(lambda d: d.update(next_action="PROP-005 was executed already so we can compare "
                                                           "it later with the formal test."), "was run or executed")

    def test_exp001_ranking_stays_inconclusive(self):
        # Phrases from a discarded run (never committed): they overstate EXP-001.
        self.assertRejected(lambda d: d.update(scientific_rationale="PROP-003 focuses on the dimension with the "
                                               "strongest observed negative association in EXP-001."), "POINT estimate")
        self.assertRejected(lambda d: d.update(scientific_rationale=d["scientific_rationale"] +
                                               " It can clarify the inconclusive ranking of personal-time dimensions."),
                            "does not resolve or clarify the ranking")
        self.assertRejected(lambda d: d.update(expected_learning=d["expected_learning"] +
                                               " This learning will resolve uncertainty about sex patterns."),
                            "not what the test will establish")
        ok = copy.deepcopy(WAITING)
        ok["scientific_rationale"] = ("PROP-003 tests sleep, which had the strongest negative point association "
                                      "in EXP-001, and directly addresses HYP-005.")
        self.assertEqual(validate(ok)["errors"], [])

    def test_human_review_constraints(self):
        self.assertRejected(lambda d: d.update(human_constraints_respected=["Association language only."]),
                            "REV-001")


class CapabilityRerun(unittest.TestCase):
    def test_same_preference_changes_status_after_engine_extension(self):
        with before_extension():
            self.assertEqual(validate(WAITING)["errors"], [])
            self.assertTrue(any("expected WAITING" in e for e in validate(READY)["errors"]))
        # The committed engine (binary moderator interactions): same preference, new status.
        self.assertTrue(any("expected READY_TO_EXECUTE" in e for e in validate(WAITING)["errors"]))
        self.assertEqual(validate(READY)["errors"], [])

    def test_ready_decision_names_the_human_approval(self):
        no_gate = {**copy.deepcopy(READY), "next_action": "The next step is to run PROP-003 with the engine "
                                                          "using its interaction specification."}
        self.assertTrue(any("human approval" in e for e in validate(no_gate)["errors"]))


class Persistence(unittest.TestCase):
    def test_decisions_are_append_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decisions = root / "reports/discovery/local/decisions"

            def save(kind, payload):
                return research_state.save_artifact(kind, payload, root=root)
            with mock.patch.object(director, "DECISION_DIR", decisions), \
                    mock.patch.object(director, "save_artifact", save):
                with before_extension():
                    first = json.loads(director.save_discovery_decision(WAITING))
                second = json.loads(director.save_discovery_decision(READY))
            self.assertEqual((first["decision_id"], second["decision_id"]), ("DEC-001", "DEC-002"))
            saved = json.loads((decisions / "DEC-001.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["decision_status"], "WAITING_FOR_ENGINE_CAPABILITY")
            self.assertNotIn("experiment_id", saved)
            self.assertFalse(saved["provenance"]["engine_capability_audit"]["supported"]["interaction_terms"])
            later = json.loads((decisions / "DEC-002.json").read_text(encoding="utf-8"))
            self.assertTrue(later["provenance"]["engine_capability_audit"]["supported"]["interaction_terms"])

    def test_rejected_decision_is_not_saved(self):
        bad = copy.deepcopy(READY)
        bad["alternatives"] = []
        before = sorted(director.DECISION_DIR.glob("DEC-*.json")) if director.DECISION_DIR.exists() else []
        result = json.loads(director.save_discovery_decision(bad))
        self.assertFalse(result["ok"])
        after = sorted(director.DECISION_DIR.glob("DEC-*.json")) if director.DECISION_DIR.exists() else []
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
