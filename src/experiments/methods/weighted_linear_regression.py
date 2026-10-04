"""FAC_PER estimating equations with PSU-cluster CR1 sandwich uncertainty.

This is a weighted cluster-robust approximation, NOT full survey-domain variance.
See docs/EXPERIMENT_ENGINE.md for the exact equation and limitations.
"""
import hashlib

import numpy as np
import pandas as pd
from scipy.stats import t

from ..models import ModelFit, direction, require
from ..schemas import Coefficient, Estimate, InteractionResult, Interval, ModeratorGroup, SlopeEstimate

CATEGORIES = {"sex": ("male", "female"), "state": ("09", "15")}
UNITS = "minutes of outcome associated with an additional 300 minutes of weekday commuting"
INTERACTION_LIMITATIONS = [
    "Observational, cross-sectional association; the interaction does not identify a causal effect or mechanism.",
    "The interaction coefficient is the formal estimand for the difference in exposure slopes between the two moderator groups.",
    "An interval that includes zero is inconclusive about heterogeneity; it is not evidence of no difference.",
    "No equivalence margin has been approved, so equivalence is not assessed.",
    "CR1 PSU-cluster uncertainty is an approximation, not full ENUT complex-survey variance.",
    "Rows missing the moderator are excluded under the model-specific complete-case policy, never assigned to a group.",
]


def interval(beta, se, df, comparisons=1):
    confidence = 1 - 0.05 / comparisons
    delta = float(t.ppf(1 - 0.05 / (2 * comparisons), df)) * se
    return Interval(lower=float(beta-delta), upper=float(beta+delta),
                    confidence_level=confidence,
                    adjustment="none" if comparisons == 1 else f"Bonferroni family of {comparisons}")


def _level_label(level):
    return str(level).lower() if isinstance(level, bool) else str(level)


def moderator_terms(exposure, interaction):
    """Term names of the moderator main effect and the exposure x moderator interaction."""
    moderator = f"{interaction.moderator}[{_level_label(interaction.comparison_level)}]"
    return moderator, f"{exposure}:{moderator}"


def design_matrix(frame, exposure, covariates, interaction=None):
    if interaction is not None:
        # The moderator enters once, coded as the spec states; it is never also a covariate dummy.
        covariates = [c for c in covariates if c != interaction.moderator]
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
    if interaction is not None:
        indicator = (frame[interaction.moderator] == interaction.comparison_level).to_numpy(dtype=float)
        values += [indicator, frame[exposure].to_numpy(dtype=float) * indicator]
        terms += list(moderator_terms(exposure, interaction))
    return np.column_stack(values), terms


def _slope(estimate, se, df):
    return SlopeEstimate(estimate=float(estimate), standard_error=float(se), interval=interval(estimate, se, df))


def _interaction_result(frame, d, spec, outcome, variant, columns, beta, covariance, terms, w, df, n):
    """Interaction coefficient, both group slopes (comparison slope via the full covariance) and counts."""
    inter = spec.interaction
    moderator_term, interaction_term = moderator_terms(spec.exposure, inter)
    e, m, i = 1, terms.index(moderator_term), terms.index(interaction_term)
    # Var(b_e + b_i) = V_ee + V_ii + 2 V_ei: the covariance term is required, intervals are never added.
    comparison_variance = covariance[e, e] + covariance[i, i] + 2 * covariance[e, i]
    require(comparison_variance >= 0, "NONFINITE_RESULT", "Negative variance for the comparison-group slope")
    se_e, se_m, se_i = (float(np.sqrt(covariance[k, k])) for k in (e, m, i))
    interaction = _slope(beta[i], se_i, df)
    excludes_zero = interaction.interval.lower > 0 or interaction.interval.upper < 0
    others = [c for c in columns if c != inter.moderator]  # this model's own variables
    groups = []
    for role, level in (("reference", inter.reference_level), ("comparison", inter.comparison_level)):
        mask = (d[inter.moderator] == level).to_numpy(dtype=bool)
        groups.append(ModeratorGroup(role=role, level=level, n=int(mask.sum()), weighted_population=float(w[mask].sum())))
    return InteractionResult(
        model_id=f"{variant}:{outcome}", variant=variant, outcome=outcome, exposure=spec.exposure,
        moderator=inter.moderator, reference_level=inter.reference_level, comparison_level=inter.comparison_level,
        coding=(f"{moderator_term} = 1 if {inter.moderator} == {_level_label(inter.comparison_level)}, "
                f"0 if {_level_label(inter.reference_level)} (reference)"),
        moderator_term=moderator_term, interaction_term=interaction_term,
        reference_group_slope=_slope(beta[e], se_e, df),
        comparison_group_slope=_slope(beta[e] + beta[i], np.sqrt(comparison_variance), df),
        comparison_slope_method="b_exposure + b_interaction; variance V_ee + V_ii + 2 V_ei from the CR1 covariance",
        moderator_main_effect=_slope(beta[m], se_m, df), interaction=interaction,
        interpretation_status="INTERVAL_EXCLUDES_ZERO" if excludes_zero else "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO",
        interpretation=("The 95% interval of the interaction excludes zero: compatible with a difference in the "
                        "exposure association between the moderator groups (observational, not causal)."
                        if excludes_zero else
                        "The 95% interval of the interaction includes zero: inconclusive about a difference in the "
                        "exposure association between the moderator groups; not evidence of no difference."),
        equivalence_assessed=False, input_n=len(frame), analysis_n=n, excluded_n=len(frame) - n,
        missing_moderator_n=int(frame[inter.moderator].isna().sum()),
        excluded_only_for_missing_moderator_n=int((frame[others].notna().all(axis=1)
                                                    & frame[inter.moderator].isna()).sum()),
        groups=groups, limitations=INTERACTION_LIMITATIONS)


def weighted_linear_regression(frame, spec, outcome, covariates, variant, provenance):
    inter = spec.interaction
    moderator = [inter.moderator] if inter is not None else []
    columns = list(dict.fromkeys([outcome, spec.exposure, *covariates, *moderator,
                                 spec.survey_weight, spec.cluster, spec.stratum]))
    missing = {c: int(frame[c].isna().sum()) for c in columns}
    # Only model variables participate in complete-case selection, never unrelated features.
    # A missing moderator excludes the row; it is never assigned to a group (no fill).
    d = frame.loc[frame[columns].notna().all(axis=1)].sort_values("person_id").copy()
    if inter is not None:
        levels = [inter.reference_level, inter.comparison_level]
        require(d[inter.moderator].isin(levels).all(), "INVALID_MODERATOR_LEVEL",
                f"{inter.moderator} has values outside {levels}")
        for level in levels:
            require((d[inter.moderator] == level).any(), "EMPTY_MODERATOR_GROUP",
                    f"No complete-case rows with {inter.moderator} == {level!r}")
    x, terms = design_matrix(d, spec.exposure, covariates, inter)
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
    model_covariates = [c for c in covariates if inter is None or c != inter.moderator]
    formula_terms = [spec.exposure, *model_covariates] + (terms[-2:] if inter is not None else [])
    model_provenance = {**provenance, "source_variables": columns,
                        "formula": f"{outcome} ~ " + " + ".join(formula_terms),
                        "terms": terms, "categorical_references": {
                            c: CATEGORIES[c][0] for c in model_covariates if c in CATEGORIES},
                        "sample_ids_sha256": hashlib.sha256("\n".join(ids).encode()).hexdigest(),
                        "covariance_method": "PSU cluster CR1, t(G-1), no stratum centering"}
    if inter is not None:
        model_provenance["interaction"] = {
            "type": inter.type, "moderator": inter.moderator, "reference_level": inter.reference_level,
            "comparison_level": inter.comparison_level, "moderator_term": terms[-2], "interaction_term": terms[-1],
            "moderator_removed_from_covariates": inter.moderator in covariates}
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
    result = None
    if inter is not None:
        result = _interaction_result(frame, d, spec, outcome, variant, columns, beta, covariance, terms, w, df, n)
        diagnostics["interaction_groups"] = [g.model_dump() for g in result.groups]
    return ModelFit(estimate, diagnostics, dict(zip(groups, influence[:, 1].tolist())), ids, df, result)
