"""FAC_PER estimating equations with PSU-cluster CR1 sandwich uncertainty.

This is a weighted cluster-robust approximation, NOT full survey-domain variance.
See docs/EXPERIMENT_ENGINE.md for the exact equation and limitations.
"""
import hashlib

import numpy as np
import pandas as pd
from scipy.stats import t

from ..models import ModelFit, direction, require
from ..schemas import Coefficient, Estimate, Interval

CATEGORIES = {"sex": ("male", "female"), "state": ("09", "15")}
UNITS = "minutes of outcome associated with an additional 300 minutes of weekday commuting"


def interval(beta, se, df, comparisons=1):
    confidence = 1 - 0.05 / comparisons
    delta = float(t.ppf(1 - 0.05 / (2 * comparisons), df)) * se
    return Interval(lower=float(beta-delta), upper=float(beta+delta),
                    confidence_level=confidence,
                    adjustment="none" if comparisons == 1 else f"Bonferroni family of {comparisons}")


def design_matrix(frame, exposure, covariates):
    values, terms = [np.ones(len(frame))], ["intercept"]
    for column in [exposure, *covariates]:
        if column in CATEGORIES:
            levels = CATEGORIES[column]
            require(frame[column].isin(levels).all(), "INVALID_CATEGORY", column)
            for level in levels[1:]:
                values.append((frame[column] == level).to_numpy(dtype=float))
                terms.append(f"{column}[{level}]")
        else:
            values.append(frame[column].to_numpy(dtype=float))
            terms.append(column)
    return np.column_stack(values), terms


def weighted_linear_regression(frame, spec, outcome, covariates, variant, provenance):
    columns = list(dict.fromkeys([outcome, spec.exposure, *covariates,
                                 spec.survey_weight, spec.cluster, spec.stratum]))
    missing = {c: int(frame[c].isna().sum()) for c in columns}
    # Only model variables participate in complete-case selection, never unrelated features.
    d = frame.loc[frame[columns].notna().all(axis=1)].sort_values("person_id").copy()
    x, terms = design_matrix(d, spec.exposure, covariates)
    y, w = d[outcome].to_numpy(dtype=float), d[spec.survey_weight].to_numpy(dtype=float)
    n, p = x.shape
    require(n > p, "INSUFFICIENT_SAMPLE", f"{n} observations for {p} parameters")
    require(np.isfinite(x).all() and np.isfinite(y).all() and np.isfinite(w).all()
            and (w > 0).all(), "INVALID_MODEL_DATA", "Nonfinite data or invalid weights")
    keys = list(zip(d[spec.stratum].tolist(), d[spec.cluster].tolist()))
    groups = sorted(set(keys))
    g = len(groups)
    require(g >= 2, "INSUFFICIENT_CLUSTERS", "At least two PSUs required")
    # Scale weights uniformly for conditioning only; population totals use original weights.
    wn = w / w.mean()
    xw = x * np.sqrt(wn)[:, None]
    yw = y * np.sqrt(wn)
    beta, _, rank, singular = np.linalg.lstsq(xw, yw, rcond=None)
    require(rank == p, "RANK_DEFICIENT", "Requested design is not full rank")
    # SVD inverse avoids squaring the condition number in the normal-equation inverse.
    pinv = np.linalg.pinv(xw)
    bread = pinv @ pinv.T
    residual = y - x @ beta
    score = x * (wn * residual)[:, None]
    grouped = np.zeros((g, p))
    lookup = {key: i for i, key in enumerate(groups)}
    np.add.at(grouped, [lookup[key] for key in keys], score)
    correction = g / (g-1) * (n-1) / (n-p)
    influence = np.sqrt(correction) * grouped @ bread
    covariance = influence.T @ influence
    require(np.isfinite(beta).all() and np.isfinite(covariance).all(),
            "NONFINITE_RESULT", "Regression produced nonfinite output")
    se = np.sqrt(np.diag(covariance))
    df = g-1
    coefficients = [Coefficient(term=name, estimate=float(b), standard_error=float(s),
                                interval=interval(b, s, df)) for name, b, s in zip(terms, beta, se)]
    ids = tuple(d.person_id.tolist())
    model_provenance = {**provenance, "source_variables": columns,
                        "formula": f"{outcome} ~ " + " + ".join([spec.exposure, *covariates]),
                        "terms": terms, "categorical_references": {
                            c: CATEGORIES[c][0] for c in covariates if c in CATEGORIES},
                        "sample_ids_sha256": hashlib.sha256("\n".join(ids).encode()).hexdigest(),
                        "covariance_method": "PSU cluster CR1, t(G-1), no stratum centering"}
    estimate = Estimate(model_id=f"{variant}:{outcome}", variant=variant, outcome=outcome,
                        exposure=spec.exposure, coefficient=float(beta[1]),
                        standard_error=float(se[1]), direction=direction(beta[1]),
                        interval=interval(beta[1], se[1], df),
                        simultaneous_outcome_interval=interval(beta[1], se[1], df, len(spec.outcomes)),
                        units=UNITS, n=n, weighted_population=float(w.sum()),
                        coefficients=coefficients, covariance=covariance.tolist(),
                        provenance=model_provenance)
    hat = np.sum(xw * pinv.T, axis=1)
    total = float(np.sum(wn * (y - np.average(y, weights=wn))**2))
    strata = d.groupby(spec.stratum)[spec.cluster].nunique()
    diagnostics = {
        "n_before_missingness": len(frame), "n_model": n, "n_missing_excluded": len(frame)-n,
        "missingness": missing, "weighted_population_before_missingness": float(frame.weight.sum()),
        "weighted_population_model": float(w.sum()), "parameters": p, "rank": int(rank),
        "clusters": g, "strata": len(strata), "psus_per_stratum": {str(k): int(v) for k,v in strata.items()},
        "singleton_strata": int((strata == 1).sum()), "inference_df": df,
        "CR1_correction": correction, "weighted_design_condition_number": float(singular[0]/singular[-1]),
        "weighted_r_squared": None if total == 0 else float(1 - np.sum(wn*residual**2)/total),
        "weighted_rmse": float(np.sqrt(np.average(residual**2, weights=wn))),
        "max_weighted_leverage": float(hat.max()), "high_leverage_count_above_2p_over_n": int((hat > 2*p/n).sum()),
        "negative_fitted_count": int((x @ beta < 0).sum()),
        "kish_weight_effective_n": float(w.sum()**2 / np.sum(w**2)),
        "kish_note": "Weight-only diagnostic; not a cluster/design effective sample size",
        "weight_min": float(w.min()), "weight_max": float(w.max()),
        "stratification_in_covariance": False, "full_survey_domain_variance": False,
        "warnings": ["CLUSTER_APPROXIMATION_NOT_FULL_SURVEY_VARIANCE"]
            + (["NEGATIVE_FITTED_TIME"] if (x @ beta < 0).any() else [])
            + (["HIGH_LEVERAGE_RETAINED"] if (hat > 2*p/n).any() else []),
    }
    return ModelFit(estimate, diagnostics, dict(zip(groups, influence[:, 1].tolist())), ids, df)
