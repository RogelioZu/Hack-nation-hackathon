"""Compact, critic-ready views of a deterministic ExperimentResult (standard library only).

Shared by the Supabase-backed tools (tools.py) and the local critic tools (critic_tools.py),
so reading a result never needs the database, embedding or PDF dependencies.
"""


def _interval(i: dict) -> list[float]:
    return [round(i["lower"], 3), round(i["upper"], 3)]


def _ranking_view(ranking: dict) -> dict:
    return {
        "status": ranking.get("status"),
        "point_estimate_order": [r["outcome"] for r in ranking.get("point_estimate_order", [])],
        "paired_comparisons": [{
            "a_minus_b": f'{c["outcome_a"]} - {c["outcome_b"]}',
            "difference": round(c["difference_a_minus_b"], 3),
            "interval": _interval(c["interval"]),
            "adjustment": c["interval"].get("adjustment"),
            "excludes_zero": c["interval"]["lower"] > 0 or c["interval"]["upper"] < 0,
        } for c in ranking.get("paired_comparisons", [])],
    }


def _slope_view(s: dict) -> dict:
    return {"estimate": round(s["estimate"], 3), "standard_error": round(s["standard_error"], 3),
            "ci95": _interval(s["interval"])}


def _interactions_view(interactions: list[dict]) -> list[dict]:
    """Binary-moderator interactions: group slopes are descriptive; the interaction is the formal test."""
    return [{
        "model_id": r["model_id"], "variant": r["variant"], "outcome": r["outcome"], "exposure": r["exposure"],
        "moderator": r["moderator"], "reference_level": r["reference_level"], "comparison_level": r["comparison_level"],
        "coding": r["coding"],
        "groups": [{"role": g["role"], "level": g["level"], "n": g["n"],
                    "weighted_population": g["weighted_population"]} for g in r["groups"]],
        "reference_group_slope": _slope_view(r["reference_group_slope"]),
        "comparison_group_slope": _slope_view(r["comparison_group_slope"]),
        "interaction_comparison_minus_reference": _slope_view(r["interaction"]),
        "moderator_main_effect": _slope_view(r["moderator_main_effect"]),
        "interpretation_status": r["interpretation_status"],
        "equivalence_assessed": r["equivalence_assessed"],
        "input_n": r["input_n"], "analysis_n": r["analysis_n"], "excluded_n": r["excluded_n"],
        "missing_moderator_n": r["missing_moderator_n"],
    } for r in interactions]


def _compact(result: dict, spec: dict) -> dict:
    """Everything the critic needs from an ExperimentResult, without covariance matrices."""
    diagnostics = {}
    for model_id, d in result["model_diagnostics"].items():
        if not isinstance(d, dict) or not model_id.startswith("adjusted:"):
            continue
        diagnostics[model_id] = {k: d.get(k) for k in (
            "n_model", "n_missing_excluded", "clusters", "strata", "singleton_strata", "inference_df",
            "weighted_r_squared", "high_leverage_count_above_2p_over_n", "negative_fitted_count",
            "kish_weight_effective_n", "warnings")}
    view = {
        "experiment_id": result["experiment_id"],
        "status": result["status"],
        "review_status": result["review_status"],
        "research_question": spec.get("research_question"),
        "population": spec.get("population"),
        "outcomes": spec.get("outcomes"),
        "covariates": spec.get("covariates"),
        "sample_size": result["sample_size"],
        "weighted_population": result["weighted_population"],
        "units": result["estimates"][0]["units"] if result["estimates"] else None,
        "estimates": [{
            "model_id": e["model_id"], "variant": e["variant"], "outcome": e["outcome"],
            "coefficient": round(e["coefficient"], 3), "standard_error": round(e["standard_error"], 3),
            "ci95_pointwise": _interval(e["interval"]),
            "bonferroni_outcome_interval": _interval(e["simultaneous_outcome_interval"]),
            "n": e["n"],
        } for e in result["estimates"]],
        "ranking": _ranking_view(result["ranking"]),
        "sensitivity": [{
            "name": s.get("name"), "rule": s.get("rule"), "n_before": s.get("n_before"),
            "n_excluded": s.get("n_excluded"), "n_after": s.get("n_after"),
            "ranking": _ranking_view(s.get("ranking") or {}),
        } for s in result["sensitivity_results"]],
        "population_counts": result["population_counts"],
        "diagnostics_adjusted": diagnostics,
        "quality_flags": result["quality_flags"],
        "limitations": result["limitations"],
        "supported_hypotheses": result["supported_hypotheses"],
        "unsupported_hypotheses": result["unsupported_hypotheses"],
        "inconclusive_hypotheses": result["inconclusive_hypotheses"],
        "engine_candidate_next_experiments": result["candidate_next_experiments"],
    }
    if result.get("interactions"):  # absent for results without a moderator (EXP-001 view unchanged)
        view["interactions"] = _interactions_view(result["interactions"])
    return view
