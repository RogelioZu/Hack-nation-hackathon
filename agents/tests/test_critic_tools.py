"""Scientific Critic tools on the committed EXP-002 interaction result (writes only to a temporary directory)."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from commute_lab import critic_tools
from commute_lab.critic_tools import ROOT, read_experiment_artifact, save_scientific_critique

EXP = "EXP-002"


def _values():
    r = json.loads((ROOT / "reports/experiments/EXP-002/result.json").read_text(encoding="utf-8"))["interactions"][0]
    f = lambda x: f"{x:.3f}"  # noqa: E731 - formatting of artifact values, no computation
    return {"ref": f(r["reference_group_slope"]["estimate"]), "cmp": f(r["comparison_group_slope"]["estimate"]),
            "int": f(r["interaction"]["estimate"]), "lo": f(r["interaction"]["interval"]["lower"]),
            "hi": f(r["interaction"]["interval"]["upper"]), "status": r["interpretation_status"]}


def good_critique():
    v = _values()
    return dict(
        experiment_id=EXP, scientific_status="UNCERTAIN",
        status_rationale="Interaction interval includes zero; therefore the result is inconclusive.",
        evidence_summary=[
            {"kind": "OBSERVED_EVIDENCE", "statement": f"Interaction (female minus male) {v['int']} with 95% interval "
             f"[{v['lo']}, {v['hi']}]; status {v['status']}.", "source": "interactions[0].interaction"},
            {"kind": "INFERENCE", "statement": "The interval includes zero, so heterogeneity by sex is inconclusive."}],
        uncertainties=["The interval includes zero, so the result is inconclusive about a sex difference.",
                       "An interval including zero does not establish equivalence; no equivalence margin exists.",
                       "EXP-001 cross-outcome ranking remains INCONCLUSIVE_RANKING."],
        limitations=["Observational, cross-sectional design; associations only.",
                     "CR1 PSU-clustered uncertainty is an approximation, not full ENUT complex-survey variance.",
                     "Limited power to detect a difference in slopes is possible.",
                     "FAC_PER-weighted linear commute specification; high-leverage observations retained.",
                     "Retained high-leverage observations may be influencing the estimates."],
        unsupported_claims=["There is no sex difference.", "H3 is false.", "Sex heterogeneity is established."],
        untested_questions=["Does the commute-sleep association differ by sex in other outcomes?"],
        hypothesis_assessments=[{"hypothesis_id": "HYP-005", "previous_status": "UNTESTED",
                                 "new_status": "INCONCLUSIVE", "reason": "The interaction interval includes zero: inconclusive."}],
        point_estimate_observations=[f"Male (reference) slope {v['ref']}; female slope {v['cmp']}: more negative "
                                     "among women at the point-estimate level."],
        formal_inference=[f"Interaction {v['int']}, 95% interval [{v['lo']}, {v['hi']}], {v['status']}: inconclusive."],
        scientific_update={"what_was_known_before": "H3 / HYP-005 had not been tested before EXP-002 (UNTESTED).",
                           "what_was_tested": "A formal commute_5h x sex interaction for sleep_weekday_min.",
                           "what_changed": "HYP-005 moved from UNTESTED to INCONCLUSIVE.",
                           "what_remains_unresolved": "Whether the association truly differs by sex."},
    )


class CriticOnInteractionResult(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for prior in critic_tools.CRITIQUE_DIR.glob("CRIT-*.json"):  # earlier experiments' critiques stay visible
            if not prior.name.startswith(f"CRIT-{EXP}-"):
                shutil.copy(prior, self.tmp)
        self.patch = patch.object(critic_tools, "CRITIQUE_DIR", self.tmp)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        shutil.rmtree(self.tmp)

    def save(self, **changes):
        data = good_critique()
        data.update(changes)
        return json.loads(save_scientific_critique(**data))

    def test_view_has_verified_lineage_interactions_and_prior_status(self):
        view = json.loads(read_experiment_artifact(EXP))
        self.assertTrue(view["ok"], view)
        self.assertTrue(view["lineage"]["verified"])
        self.assertEqual(view["lineage"]["decision_approval_id"], "REV-DEC-005-001")
        self.assertEqual(view["result"]["interactions"][0]["interpretation_status"], "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO")
        self.assertEqual(view["required_hypothesis_assessments"]["HYP-005"],
                         {"protocol_hypothesis_id": "H3", "previous_status": "UNTESTED", "new_status": "INCONCLUSIVE"})
        prior = view["prior_scientific_state"]["experiments"][0]
        self.assertEqual((prior["experiment_id"], prior["ranking_status"]), ("EXP-001", "INCONCLUSIVE_RANKING"))

    def test_exp001_view_unchanged(self):
        view = json.loads(read_experiment_artifact("EXP-001"))
        self.assertNotIn("lineage", view)
        self.assertNotIn("interactions", view["result"])

    def test_valid_critique_is_saved_with_structure_and_provenance(self):
        out = self.save()
        self.assertTrue(out["ok"], out)
        saved = json.loads((self.tmp / f"{out['critique_id']}.json").read_text(encoding="utf-8"))
        self.assertEqual(out["critique_id"], "CRIT-EXP-002-001")
        self.assertEqual(saved["hypothesis_assessments"][0]["protocol_hypothesis_id"], "H3")
        self.assertTrue(saved["provenance"]["lineage_verified"])
        self.assertEqual(saved["provenance"]["hypothesis_status_before"]["H3"]["previous_status"], "UNTESTED")
        for key in ("point_estimate_observations", "formal_inference", "scientific_update"):
            self.assertIn(key, saved)

    def test_misinterpretations_are_rejected(self):
        v = _values()
        neg = lambda x: x[1:] if x.startswith("-") else x  # noqa: E731 - drop the sign, no computation
        cases = {
            "equality": dict(status_rationale="Men and women have the same association."),
            "no difference": dict(uncertainties=["There is no sex difference in the slope."]),
            "established": dict(status_rationale="The analysis demonstrates a sex difference in the slope."),
            "not evaluated": dict(limitations=["H3 was not evaluated.", "CR1 approximation.", "Observational."]),
            "ranking": dict(status_rationale="EXP-002 resolves the ranking of outcomes."),
            "next experiment": dict(untested_questions=["EXP-003 should test leisure."]),
            "other proposal": dict(status_rationale="PROP-008 is the natural follow-up; inconclusive."),
            "invented number": dict(formal_inference=[f"Interaction {v['int']}, 95% interval [{v['lo']}, {v['hi']}], "
                                                      f"{v['status']}: inconclusive; ratio 1.234."]),
            "flipped sign": dict(point_estimate_observations=[f"Male slope {neg(v['ref'])}; female slope {v['cmp']} "
                                                              f"and {v['ref']} at the point-estimate level."]),
            "wrong status": dict(hypothesis_assessments=[{"hypothesis_id": "HYP-005", "previous_status": "UNTESTED",
                                                          "new_status": "NOT_SUPPORTED", "reason": "x"}]),
            "intervention": dict(uncertainties=["Employers should reduce commuting for women; inconclusive.",
                                                "No equivalence margin exists.", "INCONCLUSIVE_RANKING kept."]),
            "unqualified comparison": dict(point_estimate_observations=[f"Women ({v['cmp']}) have a stronger "
                                                                        f"association than men ({v['ref']})."]),
            "ranking dropped": dict(uncertainties=["The result is inconclusive.", "No equivalence margin exists."]),
            "causal": dict(formal_inference=[f"Commuting causes less sleep: {v['int']} [{v['lo']}, {v['hi']}] {v['status']}."]),
            "includes zero alone": dict(status_rationale="The interval includes zero."),
            "reference slope as pooled": dict(evidence_summary=[{"kind": "OBSERVED_EVIDENCE", "statement":
                f"The adjusted association between commuting and sleep is {v['ref']} minutes."}]),
            "causal question": dict(untested_questions=["Does commuting time affect leisure?"]),
            "missing method caveats": dict(limitations=["Observational, cross-sectional design.",
                                                        "CR1 is an approximation, not full ENUT survey variance."]),
        }
        for name, change in cases.items():
            with self.subTest(name):
                out = self.save(**change)
                self.assertFalse(out["ok"], f"{name} was accepted")
        self.assertEqual(list(self.tmp.glob("CRIT-EXP-002-*.json")), [])

    def test_retired_critiques_keep_their_ids(self):
        (self.tmp / "superseded").mkdir()
        (self.tmp / "superseded" / "CRIT-EXP-002-001.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.save()["critique_id"], "CRIT-EXP-002-002")

    def test_tampered_provenance_stops_the_critic(self):
        spec_dir = self.tmp / "experiments"
        shutil.copytree(ROOT / "experiments" / EXP, spec_dir / EXP)
        prov = json.loads((spec_dir / EXP / "provenance.json").read_text(encoding="utf-8"))
        broken = copy.deepcopy(prov)
        broken["source_artifacts"]["decision"]["sha256"] = "0" * 64
        (spec_dir / EXP / "provenance.json").write_text(json.dumps(broken), encoding="utf-8")
        with patch.object(critic_tools, "SPEC_DIR", spec_dir):
            out = json.loads(read_experiment_artifact(EXP))
            self.assertFalse(out["ok"])
            self.assertIn("does not validate", out["error"])
            self.assertFalse(self.save()["ok"])


if __name__ == "__main__":
    unittest.main()
