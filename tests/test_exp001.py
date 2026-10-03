import json
import re
import unittest

import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import WLS
from statsmodels.stats.sandwich_covariance import cov_cluster

from src.experiments.methods.weighted_linear_regression import design_matrix
from src.experiments.report import render_summary
from src.experiments.runner import ROOT, canonical_json, run_experiment, sha
from src.experiments.schemas import ExperimentResult, ExperimentSpec


class EXP001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = ExperimentSpec.model_validate_json((ROOT / "experiments/EXP-001/spec.json").read_text(encoding="utf-8"))
        cls.before = sha(ROOT / "data/processed/analytic_v1.parquet")
        cls.result = run_experiment(cls.spec)

    def test_repeated_execution_and_hash(self):
        again = run_experiment(self.spec)
        self.assertEqual(canonical_json(self.result.model_dump()), canonical_json(again.model_dump()))
        self.assertEqual(self.before, sha(ROOT / "data/processed/analytic_v1.parquet"))
        self.assertEqual(self.result, ExperimentResult.model_validate_json(self.result.model_dump_json()))

    def test_counts_missingness_and_sensitivity(self):
        r = self.result
        self.assertEqual(r.sample_size, 2563)
        self.assertEqual(r.weighted_population, 12737236)
        self.assertEqual(len(r.estimates), 16)
        self.assertEqual(r.sensitivity_results[0]["n_excluded"], 34)
        self.assertEqual(r.sensitivity_results[0]["n_after"], 2529)
        self.assertEqual(r.missingness["work_modality"], 957)
        self.assertEqual(r.missingness["has_child_u15"], 3)
        for key,d in r.model_diagnostics.items():
            self.assertEqual(d["n_missing_excluded"], 0)
        for v in self.spec.outcomes:
            self.assertEqual(r.missingness[v], 0)

    def test_all_estimates_have_provenance_and_no_causal_templates(self):
        for e in self.result.estimates:
            self.assertEqual(e.provenance["dataset_sha256"], self.before)
            self.assertIn(e.outcome, e.provenance["source_variables"])
            self.assertIn("formula", e.provenance)
            self.assertTrue(np.isfinite(e.covariance).all())
        text = " ".join(self.result.scientific_interpretation) + render_summary(self.result)
        self.assertIsNone(re.search(r"\b(causes|leads to|results in|causa|provoca|genera una reducción)\b", text, re.I))
        self.assertTrue(all(not c["selected"] for c in self.result.candidate_next_experiments))

    def test_real_data_coefficients_and_covariance_against_statsmodels(self):
        d = pd.read_parquet(ROOT / "data/processed/analytic_v1.parquet").sort_values("person_id")
        for e in self.result.estimates:
            subset = d.loc[d.work_weekday_min != 0] if e.variant.startswith("exclude_") else d
            controls = [] if e.variant.endswith("unadjusted") else self.spec.covariates
            x, _ = design_matrix(subset, self.spec.exposure, controls)
            reference = WLS(subset[e.outcome].to_numpy(dtype=float), x, weights=subset.weight.to_numpy(dtype=float)).fit()
            groups = pd.factorize(pd.MultiIndex.from_frame(subset[["stratum", "cluster"]]))[0]
            covariance = cov_cluster(reference, groups, use_correction=True)
            np.testing.assert_allclose([c.estimate for c in e.coefficients], reference.params, rtol=1e-8, atol=1e-7)
            np.testing.assert_allclose(e.covariance, covariance, rtol=1e-8, atol=1e-7)

