import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import WLS
from statsmodels.stats.sandwich_covariance import cov_cluster

from src.experiments.methods.weighted_linear_regression import design_matrix, weighted_linear_regression
from src.experiments.models import ExperimentError
from src.experiments.runner import ROOT, load_approved, ranking, run_experiment
from src.experiments.schemas import ExperimentSpec


def specification():
    return ExperimentSpec.model_validate_json((ROOT / "experiments/EXP-001/spec.json").read_text(encoding="utf-8"))


def synthetic():
    rng = np.random.default_rng(41)
    n = 120
    x = rng.uniform(0, 5, n)
    work = rng.uniform(200, 3000, n)
    y = 1500 - 25*x + .02*work + np.repeat(rng.normal(0, 25, 30), 4) + rng.normal(0, 8, n)
    return pd.DataFrame({"person_id": [f"p{i:03}" for i in range(n)], "commute_5h": x,
        "work_weekday_min": work, "sleep_weekday_min": y, "leisure_weekday_min": y*.4+rng.normal(0, 8, n),
        "age": rng.integers(18, 66, n), "sex": np.tile(["male", "female"], 60),
        "state": np.tile(["09", "09", "15", "15"], 30), "weight": rng.uniform(1, 12, n),
        "stratum": np.repeat(["a", "b", "c"], 40), "cluster": np.repeat([str(i) for i in range(30)], 4)})


class MethodTests(unittest.TestCase):
    def test_against_independent_statsmodels_and_weight_scale_invariance(self):
        d, spec = synthetic(), specification()
        result = weighted_linear_regression(d, spec, "sleep_weekday_min", spec.covariates, "adjusted", {})
        x, terms = design_matrix(d, spec.exposure, spec.covariates)
        reference = WLS(d.sleep_weekday_min.to_numpy(), x, weights=d.weight.to_numpy()).fit()
        groups = pd.factorize(pd.MultiIndex.from_frame(d[["stratum", "cluster"]]))[0]
        cov = cov_cluster(reference, groups, use_correction=True)
        np.testing.assert_allclose([c.estimate for c in result.estimate.coefficients], reference.params, rtol=1e-9, atol=1e-8)
        np.testing.assert_allclose(result.estimate.covariance, cov, rtol=1e-9, atol=1e-8)
        d.weight *= 19
        scaled = weighted_linear_regression(d, spec, "sleep_weekday_min", spec.covariates, "adjusted", {})
        np.testing.assert_allclose(result.estimate.covariance, scaled.estimate.covariance, rtol=1e-9, atol=1e-8)
        self.assertAlmostEqual(scaled.estimate.weighted_population / result.estimate.weighted_population, 19)

    def test_paired_contrast_matches_regression_of_difference(self):
        d, spec = synthetic(), specification()
        a = weighted_linear_regression(d, spec, "sleep_weekday_min", spec.covariates, "adjusted", {})
        b = weighted_linear_regression(d, spec, "leisure_weekday_min", spec.covariates, "adjusted", {})
        contrast = ranking([a, b])["paired_comparisons"][0]
        d.sleep_weekday_min = d.sleep_weekday_min-d.leisure_weekday_min
        diff = weighted_linear_regression(d, spec, "sleep_weekday_min", spec.covariates, "adjusted", {})
        self.assertAlmostEqual(abs(contrast["difference_a_minus_b"]), abs(diff.estimate.coefficient), places=8)
        self.assertAlmostEqual(contrast["standard_error"], diff.estimate.standard_error, places=8)

    def test_missingness_not_zero_and_no_unrelated_drops(self):
        d, spec = synthetic(), specification()
        d["unrelated"] = np.nan
        d.loc[0, "sleep_weekday_min"] = np.nan
        fit = weighted_linear_regression(d, spec, "sleep_weekday_min", [], "unadjusted", {})
        self.assertEqual(fit.estimate.n, 119)
        self.assertEqual(fit.diagnostics["missingness"]["sleep_weekday_min"], 1)
        self.assertEqual(fit.diagnostics["n_missing_excluded"], 1)

    def test_failure_on_nonfinite_weights_rank_and_clusters(self):
        for change in [lambda d: d.assign(weight=-1), lambda d: d.assign(weight=np.inf),
                       lambda d: d.assign(commute_5h=1), lambda d: d.assign(stratum="a", cluster="1")]:
            with self.assertRaises(ExperimentError):
                weighted_linear_regression(change(synthetic()), specification(), "sleep_weekday_min", [], "u", {})

    def test_inconclusive_with_shared_estimates_and_different_samples(self):
        d, spec = synthetic(), specification()
        d.leisure_weekday_min = d.sleep_weekday_min
        a = weighted_linear_regression(d, spec, "sleep_weekday_min", [], "u", {})
        b = weighted_linear_regression(d, spec, "leisure_weekday_min", [], "u", {})
        self.assertEqual(ranking([a, b])["status"], "INCONCLUSIVE_RANKING")
        d.loc[0, "leisure_weekday_min"] = np.nan
        b = weighted_linear_regression(d, spec, "leisure_weekday_min", [], "u", {})
        self.assertEqual(ranking([a, b])["paired_comparisons"], [])


class RunnerFailureTests(unittest.TestCase):
    def test_unknown_variable_and_method_fail_structurally_before_read(self):
        for key,value in [("outcomes", ["unknown"]), ("method", "unknown")]:
            data = specification().model_dump()
            data[key] = value
            with patch("src.experiments.runner.load_approved") as load:
                with self.assertRaises(ExperimentError) as error:
                    run_experiment(data)
                self.assertEqual(error.exception.as_dict()["status"], "EXPERIMENT_FAILED")
                load.assert_not_called()

    def test_approval_hash_mismatch_fails(self):
        with patch("src.experiments.runner.sha", return_value="tampered"):
            with self.assertRaisesRegex(ExperimentError, "hash mismatch"):
                load_approved(ROOT)

    def test_wrong_expected_n_fails(self):
        data = specification().model_dump()
        data["population"]["expected_n"] = 1
        with self.assertRaises(ExperimentError) as error:
            run_experiment(data)
        self.assertEqual(error.exception.code, "UNEXPECTED_SAMPLE_SIZE")

