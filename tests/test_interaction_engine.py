"""Binary-moderator interaction capability, tested on synthetic data only (no real scientific result)."""
import copy
import json
import unittest

import numpy as np
import pandas as pd
from pydantic import ValidationError
from statsmodels.regression.linear_model import WLS
from statsmodels.stats.sandwich_covariance import cov_cluster

from src.experiments.capabilities import capabilities
from src.experiments.methods.weighted_linear_regression import design_matrix, weighted_linear_regression
from src.experiments.models import ExperimentError
from src.experiments.runner import ROOT, canonical_json
from src.experiments.schemas import ExperimentSpec

OUTCOME = "sleep_weekday_min"


def spec(moderator="sex", reference="male", comparison="female", covariates=("work_weekday_min", "age"), **extra):
    data = json.loads((ROOT / "experiments/EXP-001/spec.json").read_text(encoding="utf-8"))
    data.update(experiment_id="EXP-900", hypothesis_ids=["H3"], outcomes=[OUTCOME], covariates=list(covariates),
                sensitivity_analyses=[], include_unadjusted=False, interaction={
                    "type": "binary_moderator", "moderator": moderator,
                    "reference_level": reference, "comparison_level": comparison})
    data["population"].pop("expected_n", None)
    data.update(extra)
    return ExperimentSpec.model_validate(data)


def synthetic(n=600, slope_ref=-2.0, slope_cmp=-5.0, noise=0.0, moderator="sex", missing=0, seed=11):
    """y = 400 + b_ref x + 7 m + (b_cmp - b_ref) x m + covariates (+ noise); m = comparison group."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 3, n)
    m = rng.random(n) < 0.45
    work, age = rng.uniform(0, 3000, n), rng.integers(18, 66, n).astype(float)
    y = 400 + slope_ref * x + 7 * m + (slope_cmp - slope_ref) * x * m + 0.01 * work - 0.3 * age
    y = y + noise * rng.normal(size=n)
    frame = pd.DataFrame({
        "person_id": [f"P{i:05d}" for i in range(n)], OUTCOME: y, "commute_5h": x, "work_weekday_min": work,
        "age": age, "sex": np.where(m, "female", "male"), "state": np.where(rng.random(n) < 0.5, "09", "15"),
        "weight": rng.uniform(50, 500, n), "cluster": [f"U{i % 60:03d}" for i in range(n)],
        "stratum": [f"S{(i % 60) // 15}" for i in range(n)]})
    child = pd.array(m, dtype="boolean")
    if missing:
        child[rng.choice(n, missing, replace=False)] = pd.NA
    frame["has_child_u15"] = child
    return frame


def fit(frame, s, covariates=None):
    return weighted_linear_regression(frame, s, OUTCOME, list(s.covariates if covariates is None else covariates),
                                      "adjusted", {})


class InteractionEstimates(unittest.TestCase):
    def test_a_known_interaction_is_recovered(self):
        exact = fit(synthetic(noise=0.0), spec()).interaction
        self.assertAlmostEqual(exact.interaction.estimate, -3.0, places=8)
        self.assertAlmostEqual(exact.reference_group_slope.estimate, -2.0, places=8)
        self.assertAlmostEqual(exact.comparison_group_slope.estimate, -5.0, places=8)
        self.assertAlmostEqual(exact.moderator_main_effect.estimate, 7.0, places=7)
        noisy = fit(synthetic(noise=5.0), spec()).interaction
        self.assertLess(abs(noisy.interaction.estimate + 3.0), 4 * noisy.interaction.standard_error)
        self.assertEqual(noisy.interpretation_status, "INTERVAL_EXCLUDES_ZERO")

    def test_b_zero_interaction(self):
        exact = fit(synthetic(slope_cmp=-2.0, noise=0.0), spec()).interaction
        self.assertAlmostEqual(exact.interaction.estimate, 0.0, places=8)
        noisy = fit(synthetic(slope_cmp=-2.0, noise=5.0), spec()).interaction
        self.assertLess(abs(noisy.interaction.estimate), 3 * noisy.interaction.standard_error)
        self.assertEqual(noisy.interpretation_status, "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO")
        self.assertIn("not evidence of no difference", noisy.interpretation)
        self.assertFalse(noisy.equivalence_assessed)

    def test_c_reference_coding_swap(self):
        frame = synthetic(noise=5.0)
        a = fit(frame, spec(reference="male", comparison="female")).interaction
        b = fit(frame, spec(reference="female", comparison="male")).interaction
        self.assertAlmostEqual(b.interaction.estimate, -a.interaction.estimate, places=9)
        self.assertAlmostEqual(b.interaction.standard_error, a.interaction.standard_error, places=9)
        for x, y in [(b.reference_group_slope, a.comparison_group_slope), (b.comparison_group_slope, a.reference_group_slope)]:
            self.assertAlmostEqual(x.estimate, y.estimate, places=9)
            self.assertAlmostEqual(x.standard_error, y.standard_error, places=9)
        self.assertEqual({g.level for g in a.groups}, {"male", "female"})
        self.assertEqual(a.groups[0].n, b.groups[1].n)

    def test_d_missing_moderator_is_excluded_and_counted(self):
        frame = synthetic(noise=5.0, missing=9)
        s = spec(moderator="has_child_u15", reference=False, comparison=True)
        result = fit(frame, s)
        r = result.interaction
        self.assertEqual((r.input_n, r.analysis_n, r.excluded_n), (len(frame), len(frame) - 9, 9))
        self.assertEqual((r.missing_moderator_n, r.excluded_only_for_missing_moderator_n), (9, 9))
        self.assertEqual(sum(g.n for g in r.groups), r.analysis_n)
        complete = fit(frame.loc[frame.has_child_u15.notna()].copy(), s).interaction
        self.assertAlmostEqual(complete.interaction.estimate, r.interaction.estimate, places=10)
        self.assertEqual(result.diagnostics["missingness"]["has_child_u15"], 9)
        self.assertEqual(result.estimate.provenance["interaction"]["moderator_term"], "has_child_u15[true]")

    def test_f_moderator_main_effect_enters_once(self):
        s = spec(covariates=("work_weekday_min", "age", "sex", "state"), reference="female", comparison="male")
        result = fit(synthetic(noise=5.0), s)
        terms = [c.term for c in result.estimate.coefficients]
        self.assertEqual([t for t in terms if t.startswith("sex[")], ["sex[male]"])
        self.assertEqual(terms[-2:], ["sex[male]", "commute_5h:sex[male]"])
        self.assertIn("state[15]", terms)
        self.assertTrue(result.estimate.provenance["interaction"]["moderator_removed_from_covariates"])
        self.assertEqual(len(terms), len(set(terms)))

    def test_g_comparison_slope_uses_full_covariance(self):
        frame = synthetic(noise=5.0)
        result = fit(frame, spec())
        r, cov = result.interaction, np.array(result.estimate.covariance)
        terms = [c.term for c in result.estimate.coefficients]
        e, i = 1, terms.index(r.interaction_term)
        expected = np.sqrt(cov[e, e] + cov[i, i] + 2 * cov[e, i])
        self.assertAlmostEqual(r.comparison_group_slope.standard_error, expected, places=10)
        naive = np.sqrt(cov[e, e] + cov[i, i])
        self.assertGreater(abs(naive - expected), 1e-3)
        swapped = fit(frame, spec(reference="female", comparison="male")).interaction
        self.assertAlmostEqual(r.comparison_group_slope.standard_error, swapped.reference_group_slope.standard_error, places=9)

    def test_matches_statsmodels_wls_cluster_cr1(self):
        frame = synthetic(noise=5.0).sort_values("person_id")
        s = spec()
        result = fit(frame, s)
        x, _ = design_matrix(frame, s.exposure, list(s.covariates), s.interaction)
        reference = WLS(frame[OUTCOME].to_numpy(), x, weights=frame.weight.to_numpy()).fit()
        groups = pd.factorize(pd.MultiIndex.from_frame(frame[["stratum", "cluster"]]))[0]
        np.testing.assert_allclose([c.estimate for c in result.estimate.coefficients], reference.params, rtol=1e-8, atol=1e-8)
        np.testing.assert_allclose(result.estimate.covariance, cov_cluster(reference, groups, use_correction=True),
                                   rtol=1e-8, atol=1e-10)


class InvalidModerators(unittest.TestCase):
    def test_e_schema_rejects_malformed_interactions(self):
        bad = [
            dict(moderator="work_modality"), dict(moderator="commute_5h"), dict(reference="male", comparison="male"),
            dict(reference="men", comparison="female"), dict(moderator="has_child_u15", reference="false", comparison=True),
            dict(moderator="state", reference=9, comparison=15),
        ]
        for case in bad:
            with self.subTest(case=case), self.assertRaises(ValidationError):
                spec(**case)
        for extra in [dict(hypothesis_ids=["H1"]), dict(interaction={"type": "multi_category", "moderator": "sex",
                                                                      "reference_level": "male", "comparison_level": "female"}),
                      dict(population={"source": "approved_analytic_v1", "states": ["09", "15"], "age_min": 18,
                                       "age_max": 65, "sexes": ["female"]})]:
            with self.subTest(extra=list(extra)), self.assertRaises(ValidationError):
                spec(**extra)
        data = json.loads((ROOT / "experiments/EXP-001/spec.json").read_text(encoding="utf-8"))
        data["hypothesis_ids"] = ["H3"]
        with self.assertRaises(ValidationError):  # heterogeneity hypothesis without an interaction
            ExperimentSpec.model_validate(data)

    def test_e_runtime_rejects_unexpected_levels_and_empty_groups(self):
        frame = synthetic(noise=5.0)
        frame.loc[frame.index[:3], "sex"] = "other"
        with self.assertRaises(ExperimentError) as caught:
            fit(frame, spec())
        self.assertEqual(caught.exception.code, "INVALID_MODERATOR_LEVEL")
        frame = synthetic(noise=5.0)
        frame["sex"] = "male"
        with self.assertRaises(ExperimentError) as caught:
            fit(frame, spec())
        self.assertEqual(caught.exception.code, "EMPTY_MODERATOR_GROUP")


class RunnerIntegration(unittest.TestCase):
    """End-to-end ExperimentResult on synthetic data: load_approved is replaced, analytic_v1 is never read."""

    def test_result_carries_machine_readable_interactions(self):
        from unittest.mock import patch
        from src.experiments.runner import run_experiment, sha

        frame = synthetic(noise=5.0, missing=4).assign(active_worker=True, employment_reference_week_absent=False)
        variables = sorted(set(frame.columns) - {"person_id"})
        manifest = {"canonical_variables": variables, "feature_definitions": {v: {} for v in variables}}
        digest = sha(ROOT / "data/processed/analytic_v1.parquet")  # read-only hash check, unchanged
        s = spec(moderator="has_child_u15", reference=False, comparison=True, hypothesis_ids=["H4"])
        with patch("src.experiments.runner.load_approved", return_value=(frame, manifest, digest, set(variables))):
            result = run_experiment(s)
        self.assertEqual(len(result.interactions), 1)
        r = result.interactions[0]
        self.assertEqual((r.moderator, r.reference_level, r.comparison_level), ("has_child_u15", False, True))
        self.assertEqual(r.missing_moderator_n, 4)
        self.assertEqual(result.estimates[0].coefficient, r.reference_group_slope.estimate)
        assessed = {h["id"]: h for h in result.supported_hypotheses + result.inconclusive_hypotheses}
        self.assertIn("H4", assessed)
        self.assertNotIn("H1", assessed)
        self.assertIn("interactions", result.model_dump())
        self.assertTrue(any("CR1" in line for line in result.limitations))


class CapabilityAndCompatibility(unittest.TestCase):
    def test_capabilities_advertise_binary_interactions_only(self):
        caps = capabilities()
        published = json.loads((ROOT / "metadata/experiment_engine_capabilities.json").read_text(encoding="utf-8"))
        self.assertEqual(published, caps)
        self.assertTrue(caps["supported"]["exposure_x_binary_moderator_interaction"])
        self.assertTrue(caps["supported"]["formal_interaction_coefficient_inference"])
        for unsupported in ("nonlinear_terms", "multi_category_interactions", "equivalence_testing"):
            self.assertFalse(caps["supported"][unsupported])

    def test_planner_style_specs_are_schema_capable_without_running(self):
        manifest = json.loads((ROOT / "metadata/analytic_v1_manifest.json").read_bytes().decode("utf-8"))
        approved = set(manifest["canonical_variables"])
        cases = [("sex", "male", "female", "sleep_weekday_min"),
                 ("has_child_u15", False, True, "sleep_weekday_min"),
                 ("sex", "male", "female", "leisure_weekday_min")]
        for moderator, reference, comparison, outcome in cases:
            with self.subTest(moderator=moderator, outcome=outcome):
                s = spec(moderator=moderator, reference=reference, comparison=comparison,
                         covariates=("work_weekday_min", "age", "sex", "state"), outcomes=[outcome])
                self.assertLessEqual({s.exposure, outcome, *s.covariates, moderator}, approved)
                self.assertEqual(ExperimentSpec.model_validate_json(s.model_dump_json()), s)

    def test_exp001_contract_serialization_unchanged(self):
        data = json.loads((ROOT / "experiments/EXP-001/spec.json").read_text(encoding="utf-8"))
        s = ExperimentSpec.model_validate(data)
        self.assertNotIn("interaction", s.model_dump())
        self.assertEqual(canonical_json(s.model_dump()), canonical_json(copy.deepcopy(data)))


def run_synthetic(s, frame):
    """run_experiment on synthetic data; load_approved is replaced, analytic_v1 is only hashed."""
    from unittest.mock import patch
    from src.experiments.runner import run_experiment, sha

    frame = frame.assign(active_worker=True, employment_reference_week_absent=False)
    variables = sorted(set(frame.columns) - {"person_id"})
    manifest = {"canonical_variables": variables, "feature_definitions": {v: {} for v in variables}}
    digest = sha(ROOT / "data/processed/analytic_v1.parquet")
    with patch("src.experiments.runner.load_approved", return_value=(frame, manifest, digest, set(variables))):
        return run_experiment(s)


class OutputSemantics(unittest.TestCase):
    """Interaction-aware result text and summary.md, on synthetic data (no real scientific result)."""

    @classmethod
    def setUpClass(cls):
        from src.experiments.report import render_summary

        # Equal true slopes plus noise: the interaction interval includes zero (checked below).
        cls.result = run_synthetic(spec(covariates=("work_weekday_min", "age", "sex")),
                                   synthetic(slope_ref=-2.0, slope_cmp=-2.0, noise=40.0))
        cls.summary = render_summary(cls.result)
        cls.r = cls.result.interactions[0]

    def test_a_summary_has_interaction_section(self):
        r = self.r
        self.assertIn("## Interacción (exposición × moderador)", self.summary)
        self.assertIn("Moderador: **sex**", self.summary)
        self.assertIn("Grupo de referencia: **male**", self.summary)
        self.assertIn("Grupo de comparación: **female**", self.summary)
        for label, s in [("grupo de referencia (sex = male)", r.reference_group_slope),
                         ("grupo de comparación (sex = female)", r.comparison_group_slope),
                         ("diferencia de pendientes (female − male)", r.interaction)]:
            self.assertIn(f"{label} | {s.estimate:.3f} | {s.standard_error:.3f} | "
                          f"[{s.interval.lower:.3f}, {s.interval.upper:.3f}] |", self.summary)
        self.assertIn(f"Estado de la interacción: **{r.interpretation_status}**", self.summary)

    def test_b_reference_group_slope_is_labeled(self):
        self.assertNotIn("| Coeficiente |", self.summary)
        self.assertIn("| Pendiente del grupo de referencia (sex = male) |", self.summary)
        self.assertIn("no un coeficiente agrupado", self.summary)
        self.assertIn("reference group sex = male", self.result.scientific_interpretation[0])
        self.assertEqual(self.result.estimates[0].coefficient, self.r.reference_group_slope.estimate)

    def test_c_h3_evaluated_but_inconclusive(self):
        self.assertEqual(self.r.interpretation_status, "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO")
        self.assertEqual([h["id"] for h in self.result.inconclusive_hypotheses], ["H3"])
        self.assertFalse(self.result.supported_hypotheses or self.result.unsupported_hypotheses)
        self.assertIn("- Inconclusas: H3", self.summary)
        self.assertIn("H1, H2 y H4 no se evaluaron.", self.summary)
        self.assertNotRegex(self.summary, r"H3[^.\n]*no se evalu")
        self.assertIn("No es evidencia de que no haya diferencia", self.summary)

    def test_d_no_stale_interaction_text_after_interaction_run(self):
        text = canonical_json(self.result.model_dump()) + self.summary
        self.assertNotIn("interactions require a new approved specification", text)
        self.assertNotIn("not evaluated in EXP-001", text)
        self.assertNotIn("Does the association differ by sex?", text)
        # Another moderator: the sex candidate stays, without the "unsupported" wording.
        other = run_synthetic(spec(moderator="has_child_u15", reference=False, comparison=True, hypothesis_ids=["H4"]),
                              synthetic(noise=5.0))
        sex = [c for c in other.candidate_next_experiments if c["question"] == "Does the association differ by sex?"]
        self.assertEqual(sex[0]["hypothesis"], "H3, not evaluated in EXP-900")
        self.assertNotIn("interactions require a new approved specification", canonical_json(other.model_dump()))

    def test_e_single_outcome_ranking_not_applicable(self):
        from src.experiments.runner import RANKING_NOT_APPLICABLE, ranking

        rank = self.result.ranking
        self.assertEqual(rank["status"], RANKING_NOT_APPLICABLE)
        self.assertEqual((rank["comparison_count"], rank["paired_comparisons"]), (0, []))
        self.assertIsNone(rank["same_complete_case_persons"])
        self.assertEqual(ranking([fit(synthetic(), spec())])["status"], RANKING_NOT_APPLICABLE)
        for flag in ("INCONCLUSIVE_RANKING", "DISTINGUISHABLE_RANKING", RANKING_NOT_APPLICABLE, "MULTIPLE_COMPARISON_FAMILIES"):
            self.assertNotIn(flag, self.result.quality_flags)
        self.assertNotIn("INCONCLUSIVE_RANKING", canonical_json(self.result.model_dump()) + self.summary)
        self.assertNotIn("Separate Bonferroni families", " ".join(self.result.limitations))
        self.assertIn("Hay un solo outcome primario", self.summary)
