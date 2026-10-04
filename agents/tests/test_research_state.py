"""Shared Research State: rebuild from committed artifacts, traceability and validation.

Run from the repo root:  PYTHONPATH=agents python -m unittest discover -s agents/tests
(kept out of tests/, which the experiment-engine validator runs as its own suite).
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from commute_lab.research_state import ROOT, build_state, dumps, resolve, save_artifact, trace

SOURCES = ["reports/experiments/EXP-001", "experiments/EXP-001/spec.json", "metadata/analytic_v1_manifest.json",
           "metadata/analytic_v1_experiment_approval.json", "docs/EXPERIMENT_PROTOCOL.md", "initial_state.json",
           "reports/discovery/local/critiques/CRIT-EXP-001-001.json"]
CRIT = "CRIT-EXP-001-001"


def hypothesis(hid="HYP-001", **extra):
    return {"hypothesis_id": hid, "statement": "The association differs between men and women.",
            "status": "proposed", "motivated_by_critique_id": CRIT,
            "evidence_ids": [f"{CRIT}/evidence/1", "EXP-001/ranking"], "protocol_hypothesis": "H3", **extra}


class RepoState(unittest.TestCase):
    """The committed repository: EXP-001 + CRIT-EXP-001-001 + approved hypotheses + planner candidates."""

    def test_rebuilds_valid_state(self):
        state, _ = build_state(ROOT)
        self.assertTrue(state["validation"]["valid"], state["validation"]["errors"])
        self.assertEqual(state["dataset"]["version"], "analytic_v1")
        self.assertEqual(state["dataset"]["population_n"], 2563)
        self.assertEqual([e["experiment_id"] for e in state["experiments"]], ["EXP-001"])
        self.assertEqual(state["experiments"][0]["critiques"], [CRIT])
        self.assertEqual([h["hypothesis_id"] for h in state["hypotheses"]][:4], ["H1", "H2", "H3", "H4"])
        # Hypothesis Agent and Experiment Planner outputs are indexed; superseded/ subfolders are not.
        self.assertEqual([h["hypothesis_id"] for h in state["hypotheses"]][4:], ["HYP-005", "HYP-007", "HYP-008"])
        candidates = [c["candidate_id"] for c in state["candidate_experiments"]]
        self.assertEqual(candidates, ["PROP-003", "PROP-005", "PROP-008", "PROP-009"])
        # The stage follows the committed artifacts (it advances as the loop does); with decisions, the latest governs.
        action = state["next_action"]
        self.assertIn(action["stage"], {"critique", "hypotheses", "candidate_experiments", "decision",
                                        "engine_extension", "human_review", "run_experiment"})
        if state["decisions"]:
            self.assertEqual(action["inputs"], [state["decisions"][-1]["decision_id"]])

    def test_deterministic_and_number_free(self):
        first, second = build_state(ROOT)[0], build_state(ROOT)[0]
        self.assertEqual(dumps(first), dumps(second))

        def floats(value):
            if isinstance(value, float):
                yield value
            elif isinstance(value, dict):
                for v in value.values():
                    yield from floats(v)
            elif isinstance(value, list):
                for v in value:
                    yield from floats(v)
        self.assertEqual(list(floats(first)), [])

    def test_pointer_resolves_to_engine_value(self):
        state, _ = build_state(ROOT)
        result = json.loads((ROOT / "reports/experiments/EXP-001/result.json").read_text(encoding="utf-8"))
        self.assertEqual(resolve(state, "EXP-001/estimates/adjusted:sleep_weekday_min"), result["estimates"][0])


class FutureArtifacts(unittest.TestCase):
    """A temporary copy of the sources, to add future artifacts and break things on purpose."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in SOURCES:
            src, dst = ROOT / rel, self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, previous=None, allow=frozenset()):
        return build_state(self.root, "local", previous, allow)[0]

    def codes(self, state):
        return {e["code"] for e in state["validation"]["errors"]}

    def write(self, kind, payload, name=None):
        path = self.root / "reports/discovery/local" / kind / f"{name or next(iter(payload.values()))}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_full_chain_is_traceable(self):
        save_artifact("hypotheses", hypothesis(), self.root)
        self.assertEqual(self.build()["next_action"]["stage"], "candidate_experiments")
        for label in ("A", "B"):
            save_artifact("candidates", {"candidate_id": f"CAND-001-{label}", "hypothesis_id": "HYP-001",
                                         "title": f"Candidate {label}"}, self.root)
        self.assertEqual(self.build()["next_action"]["stage"], "decision")
        save_artifact("decisions", {"decision_id": "DEC-001", "selected_candidate_id": "CAND-001-A",
                                    "considered_candidate_ids": ["CAND-001-A", "CAND-001-B"],
                                    "based_on_critique_id": CRIT, "experiment_id": "EXP-002",
                                    "rationale": "Highest expected learning."}, self.root)
        state = self.build()
        self.assertTrue(state["validation"]["valid"], state["validation"]["errors"])
        self.assertEqual(state["next_action"]["stage"], "run_experiment")
        self.assertIn("PENDING_EXPERIMENT", {w["code"] for w in state["validation"]["warnings"]})

        def ids(chain):
            return [i["id"] for item in chain for i in [item, *[{"id": x} for x in ids(item.get("chain", []))]]]
        upstream = ids(trace(state, "DEC-001")["relies_on"])
        for expected in ("CAND-001-A", "CAND-001-B", "HYP-001", CRIT, f"{CRIT}/evidence/1", "EXP-001", "H3"):
            self.assertIn(expected, upstream)
        downstream = ids(trace(state, "EXP-001")["used_by"])
        for expected in (CRIT, "HYP-001", "CAND-001-A", "DEC-001"):
            self.assertIn(expected, downstream)

    def test_latest_discovery_decision_sets_the_stage(self):
        save_artifact("hypotheses", hypothesis(), self.root)
        save_artifact("candidates", {"proposal_id": "PROP-001", "hypothesis_ids": ["HYP-001"]}, self.root)
        save_artifact("decisions", {"decision_id": "DEC-001", "preferred_proposal_id": "PROP-001",
                                    "candidate_proposal_ids": ["PROP-001"], "alternatives": [],
                                    "decision_status": "WAITING_FOR_ENGINE_CAPABILITY"}, self.root)
        action = self.build()["next_action"]
        self.assertEqual((action["stage"], action["inputs"]), ("engine_extension", ["DEC-001"]))
        save_artifact("decisions", {"decision_id": "DEC-002", "preferred_proposal_id": "PROP-001",
                                    "candidate_proposal_ids": ["PROP-001"],
                                    "decision_status": "READY_TO_EXECUTE"}, self.root)
        action = self.build()["next_action"]
        self.assertEqual((action["stage"], action["inputs"]), ("run_experiment", ["DEC-002"]))

    def test_candidate_with_supabase_style_proposal_id(self):
        save_artifact("hypotheses", hypothesis(), self.root)
        save_artifact("candidates", {"proposal_id": "CAND-X", "hypothesis_id": "HYP-001"}, self.root)
        state = self.build()
        self.assertTrue(state["validation"]["valid"])
        self.assertEqual(state["candidate_experiments"][0]["candidate_id"], "CAND-X")

    def test_hypothesis_with_missing_evidence(self):
        save_artifact("hypotheses", hypothesis(evidence_ids=["EXP-001/estimates/adjusted:naps"]), self.root)
        self.assertIn("MISSING_EVIDENCE", self.codes(self.build()))

    def test_hypothesis_with_missing_critique(self):
        save_artifact("hypotheses", hypothesis(motivated_by_critique_id="CRIT-EXP-001-009"), self.root)
        self.assertIn("MISSING_REFERENCE", self.codes(self.build()))

    def test_decision_with_missing_proposal(self):
        save_artifact("decisions", {"decision_id": "DEC-001", "proposal_id": "CAND-404"}, self.root)
        self.assertIn("MISSING_REFERENCE", self.codes(self.build()))

    def test_duplicate_ids(self):
        save_artifact("hypotheses", hypothesis(), self.root)
        save_artifact("candidates", {"candidate_id": "HYP-001", "hypothesis_id": "HYP-001"}, self.root)
        self.assertIn("DUPLICATE_ID", self.codes(self.build()))

    def test_id_must_match_filename(self):
        self.write("hypotheses", hypothesis(), name="HYP-002")
        self.assertIn("ID_FILENAME_MISMATCH", self.codes(self.build()))

    def test_invalid_experiment_ids(self):
        shutil.copytree(self.root / "reports/experiments/EXP-001", self.root / "reports/experiments/EXP-2")
        save_artifact("decisions", {"decision_id": "DEC-001", "experiment_id": "exp2"}, self.root)
        errors = [e for e in self.build()["validation"]["errors"] if e["code"] == "INVALID_EXPERIMENT_ID"]
        self.assertEqual(len(errors), 2)

    def test_inconsistent_dataset_version(self):
        path = self.root / "reports/discovery/local/critiques/CRIT-EXP-001-001.json"
        critique = json.loads(path.read_text(encoding="utf-8"))
        critique["provenance"]["dataset_version"] = "analytic_v2"
        path.write_text(json.dumps(critique), encoding="utf-8")
        self.assertIn("DATASET_VERSION_MISMATCH", self.codes(self.build()))

    def test_tampered_result_is_rejected(self):
        path = self.root / "reports/experiments/EXP-001/result.json"
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
        codes = self.codes(self.build())
        self.assertIn("UNVALIDATED_RESULT", codes)
        self.assertIn("MISSING_REFERENCE", codes)  # the critique now points to an unindexed experiment

    def test_accidental_overwrite_and_removal(self):
        save_artifact("hypotheses", hypothesis(), self.root)
        previous = self.build()
        with self.assertRaises(FileExistsError):
            save_artifact("hypotheses", hypothesis(status="supported"), self.root)
        self.write("hypotheses", hypothesis(status="supported"))  # bypasses save_artifact on purpose
        self.assertIn("ACCIDENTAL_OVERWRITE", self.codes(self.build(previous)))
        allowed = frozenset({"reports/discovery/local/hypotheses/HYP-001.json"})
        self.assertTrue(self.build(previous, allowed)["validation"]["valid"])
        (self.root / "reports/discovery/local/hypotheses/HYP-001.json").unlink()
        self.assertIn("ARTIFACT_REMOVED", self.codes(self.build(previous)))

    def test_unknown_kind_is_tolerated(self):
        self.write("notes", {"note_id": "N-1"})
        state = self.build()
        self.assertTrue(state["validation"]["valid"])
        self.assertIn("UNKNOWN_KIND", {w["code"] for w in state["validation"]["warnings"]})


if __name__ == "__main__":
    unittest.main()
