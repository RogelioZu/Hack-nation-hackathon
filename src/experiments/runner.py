"""Read-only deterministic orchestration over the approved canonical dataset."""
import hashlib
import itertools
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import pydantic
import pyarrow
import scipy
from pydantic import ValidationError

from .methods import METHODS
from .methods.weighted_linear_regression import interval
from .models import ExperimentError, direction, require
from .schemas import ExperimentResult, ExperimentSpec

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def code_fingerprints(root):
    paths = list((root / "src/experiments").rglob("*.py"))
    paths += [root / "scripts/run_experiment.py", root / "docs/EXPERIMENT_ENGINE.md",
              root / "requirements-experiments.txt", root / "metadata/experiment_contract.schema.json"]
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths)}


def load_approved(root):
    path = root / "data/processed/analytic_v1.parquet"
    manifest_path = root / "metadata/analytic_v1_manifest.json"
    approval_path = root / "metadata/analytic_v1_experiment_approval.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    digest = sha(path)
    require(approval["status"] == "APPROVED_FOR_EXPERIMENTS"
            and approval["dataset_version"] == manifest["dataset_version"] == "analytic_v1"
            and digest == manifest["dataset_sha256"] == approval["dataset_sha256"],
            "UNAPPROVED_DATASET", "Dataset approval/version/hash mismatch")
    require(all(v is True for v in manifest["validations"].values()),
            "FAILED_DATA_QUALITY", "Historical dataset validation did not pass")
    # First table only: the lower contract section describes historical staging aliases.
    contract = (root / "docs/DATA_CONTRACT.md").read_text(encoding="utf-8")
    table = contract.split("## Canonical columns", 1)[1].split("## Leisure components", 1)[0]
    approved_variables = {line.split("|")[1].strip() for line in table.splitlines()
                          if line.startswith("| ") and not line.startswith("| Variable ")}
    require(approved_variables == set(manifest["canonical_variables"]),
            "CONTRACT_DRIFT", "DATA_CONTRACT canonical variables differ from manifest")
    data = pd.read_parquet(path).sort_values("person_id").reset_index(drop=True)
    require(len(data) == manifest["row_count"] == 2563 and data.person_id.is_unique
            and data.person_id.notna().all(), "INVALID_IDENTIFIERS", "Person count/uniqueness mismatch")
    require(data.state.isin(["09", "15"]).all() and data.age.between(18, 65).all()
            and data.active_worker.all() and not data.employment_reference_week_absent.any()
            and data.commute_weekday_min.notna().all(), "INVALID_POPULATION", "Domain mismatch")
    for alias, raw in [("weight", "FAC_PER"), ("stratum", "EST_DIS"), ("cluster", "UPM_DIS")]:
        require(data[alias].notna().all(), "INVALID_DESIGN", f"Missing {alias}")
        source = pd.to_numeric(data[raw], errors="raise") if alias == "weight" else data[raw]
        require((data[alias] == source).all(), "INVALID_DESIGN", f"Survey alias drift: {alias}")
    require(np.isfinite(data.weight.to_numpy(dtype=float)).all() and (data.weight > 0).all(),
            "INVALID_WEIGHTS", "Weights must be positive and finite")
    require((data.stratum.str.len() > 0).all() and (data.cluster.str.len() > 0).all(),
            "INVALID_DESIGN", "Empty PSU or stratum")
    for variable in manifest["canonical_variables"]:
        require(variable in data and variable in manifest["feature_definitions"],
                "MISSING_VARIABLE", variable)
        require(int(data[variable].isna().sum()) == manifest["missingness"][variable]["missing"],
                "MISSINGNESS_DRIFT", variable)
        if variable.endswith("_min") or variable == "commute_5h":
            observed = data[variable].dropna().to_numpy(dtype=float)
            require(np.isfinite(observed).all() and (observed >= 0).all(), "INVALID_TIME", variable)
    require(np.allclose(data.commute_5h.to_numpy(dtype=float),
                        data.commute_weekday_min.to_numpy(dtype=float)/300, rtol=0, atol=1e-12),
            "EXPOSURE_DRIFT", "commute_5h must equal weekday commute / 300")
    return data, manifest, digest, approved_variables


def ranking(fits):
    ordered = sorted(fits, key=lambda f: (f.estimate.coefficient, f.estimate.outcome))
    order = [{"rank": i+1, "outcome": f.estimate.outcome, "coefficient": f.estimate.coefficient,
              "direction": f.estimate.direction, "interval": f.estimate.interval.model_dump()}
             for i, f in enumerate(ordered)]
    pairs = list(itertools.combinations(ordered, 2))
    comparable = all(a.sample_ids == b.sample_ids for a, b in pairs)
    contrasts = []
    if comparable:
        for a, b in pairs:
            keys = sorted(set(a.cluster_influence) | set(b.cluster_influence))
            se = float(np.sqrt(sum((a.cluster_influence.get(k, 0)-b.cluster_influence.get(k, 0))**2 for k in keys)))
            difference = a.estimate.coefficient-b.estimate.coefficient
            ci = interval(difference, se, min(a.df, b.df), len(pairs))
            contrasts.append({"outcome_a": a.estimate.outcome, "outcome_b": b.estimate.outcome,
                              "difference_a_minus_b": difference, "standard_error": se,
                              "interval": ci.model_dump(), "method": "paired PSU influence contrast"})
    full_order = bool(pairs) and comparable and all(c["interval"]["upper"] < 0 for c in contrasts)
    return {"status": "DISTINGUISHABLE_RANKING" if full_order else "INCONCLUSIVE_RANKING",
            "point_estimate_order": order, "paired_comparisons": contrasts,
            "comparison_count": len(contrasts), "same_complete_case_persons": comparable,
            "rule": "All ordered pairs must have negative Bonferroni simultaneous intervals; point ordering alone is descriptive",
            "limitation": "Cluster approximation; ranking uncertainty does not establish equivalence"}


def _run(spec, root):
    data, manifest, digest, approved = load_approved(root)
    requested = {spec.exposure, *spec.outcomes, *spec.covariates,
                 spec.survey_weight, spec.cluster, spec.stratum}
    require(requested <= approved, "UNKNOWN_VARIABLE", str(sorted(requested-approved)))
    require(spec.method in METHODS, "UNKNOWN_METHOD", spec.method)
    fingerprints = code_fingerprints(root)
    provenance = {
        "dataset_sha256": digest, "manifest_sha256": sha(root / "metadata/analytic_v1_manifest.json"),
        "approval_sha256": sha(root / "metadata/analytic_v1_experiment_approval.json"),
        "spec_sha256": hashlib.sha256(canonical_json(spec.model_dump()).encode()).hexdigest(),
        "code_sha256": hashlib.sha256(canonical_json(fingerprints).encode()).hexdigest(),
        "code_fingerprints": fingerprints,
        "protocol_fingerprints": {p: sha(root / p) for p in ["AGENTS.md", "docs/DATA_CONTRACT.md",
            "docs/SCIENTIFIC_PROTOCOL.md", "docs/EXPERIMENT_PROTOCOL.md"]},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                    "pyarrow": pyarrow.__version__, "scipy": scipy.__version__, "pydantic": pydantic.__version__},
        "feature_definitions": {v: manifest["feature_definitions"][v] for v in sorted(requested)},
        "spec": spec.model_dump(), "dataset_path": "data/processed/analytic_v1.parquet",
    }
    model_provenance = {k: provenance[k] for k in ["dataset_sha256", "manifest_sha256", "spec_sha256", "code_sha256"]}
    counts = [{"step": "approved_analytic_v1", "n": len(data), "weighted_population": float(data.weight.sum())}]
    population = data
    filters = [("states", lambda d: d.state.isin(spec.population.states)),
               ("age_inclusive", lambda d: d.age.between(spec.population.age_min, spec.population.age_max)),
               ("sexes", lambda d: d.sex.isin(spec.population.sexes))]
    for name, selector in filters:
        before = len(population)
        population = population.loc[selector(population)].copy()
        counts.append({"step": name, "n": len(population), "excluded": before-len(population),
                       "weighted_population": float(population.weight.sum())})
    if spec.population.expected_n is not None:
        require(len(population) == spec.population.expected_n, "UNEXPECTED_SAMPLE_SIZE", str(len(population)))
    require(len(population) > 0, "EMPTY_POPULATION", "No selected persons")
    missingness = {v: int(population[v].isna().sum()) for v in manifest["canonical_variables"]}
    fit = METHODS[spec.method]
    fits = []
    for variant, controls in [("adjusted", spec.covariates)] + ([("unadjusted", [])] if spec.include_unadjusted else []):
        for outcome in spec.outcomes:
            fits.append(fit(population, spec, outcome, controls, variant, model_provenance))
    primary = [f for f in fits if f.estimate.variant == "adjusted"]
    primary_rank = ranking(primary)
    sensitivity = []
    for name in spec.sensitivity_analyses:
        subset = population.loc[population.work_weekday_min.ne(0).fillna(True)].copy()
        sensitivity_fits = []
        for variant, controls in [("adjusted", spec.covariates)] + ([("unadjusted", [])] if spec.include_unadjusted else []):
            for outcome in spec.outcomes:
                sensitivity_fits.append(fit(subset, spec, outcome, controls, f"{name}:{variant}", model_provenance))
        adjusted = [f for f in sensitivity_fits if f.estimate.variant.endswith(":adjusted")]
        srank = ranking(adjusted)
        comparison = []
        for a, b in zip(primary, adjusted):
            comparison.append({"outcome": a.estimate.outcome, "primary_coefficient": a.estimate.coefficient,
                "sensitivity_coefficient": b.estimate.coefficient,
                "coefficient_difference": b.estimate.coefficient-a.estimate.coefficient,
                "primary_direction": a.estimate.direction, "sensitivity_direction": b.estimate.direction,
                "direction_changed": a.estimate.direction != b.estimate.direction,
                "primary_interval": a.estimate.interval.model_dump(), "sensitivity_interval": b.estimate.interval.model_dump(),
                "primary_rank": next(v["rank"] for v in primary_rank["point_estimate_order"] if v["outcome"] == a.estimate.outcome),
                "sensitivity_rank": next(v["rank"] for v in srank["point_estimate_order"] if v["outcome"] == b.estimate.outcome)})
        sensitivity.append({"name": name, "rule": "Exclude work_weekday_min == 0; retain missing until model-specific handling",
            "n_before": len(population), "n_excluded": len(population)-len(subset), "n_after": len(subset),
            "weighted_population": float(subset.weight.sum()), "ranking": srank, "comparison": comparison,
            "missingness": {v: int(subset[v].isna().sum()) for v in sorted(requested)},
            "model_ids": [f.estimate.model_id for f in sensitivity_fits],
            "primary_population_redefined": False})
        fits.extend(sensitivity_fits)
    supported, unsupported, inconclusive = [], [], []
    if "H1" in spec.hypothesis_ids:
        negative = [f.estimate.outcome for f in primary if f.estimate.simultaneous_outcome_interval.upper < 0]
        if negative:
            supported.append({"id": "H1", "assessment": "Evidence consistent with a negative association under the specified model",
                              "evidence": ", ".join(negative) + "; Bonferroni outcome intervals below zero; provisional survey approximation"})
        elif all(f.estimate.simultaneous_outcome_interval.lower >= 0 for f in primary):
            unsupported.append({"id": "H1", "assessment": "Not supported for the requested outcomes under this model",
                                "evidence": "Simultaneous intervals nonnegative; not a general falsification"})
        else:
            inconclusive.append({"id": "H1", "assessment": "Uncertain", "evidence": "Negative associations not resolved by simultaneous intervals"})
    if "H2" in spec.hypothesis_ids:
        differences = [c for c in primary_rank["paired_comparisons"] if c["interval"]["upper"] < 0 or c["interval"]["lower"] > 0]
        target = supported if differences else inconclusive
        target.append({"id": "H2", "assessment": "Evidence of at least one difference" if differences else "Uncertain differences",
                       "evidence": f"{len(differences)} of {primary_rank['comparison_count']} paired simultaneous intervals exclude zero; this does not establish a full ranking"})
    limitations = [
        "Observational associations; no identification of mechanisms or intervention effects.",
        "FAC_PER-weighted point estimates; CR1 PSU-cluster sandwich is an approximation, not full ENUT complex-survey variance.",
        "EST_DIS identifies nested PSUs and is reported, but covariance does not center scores within strata or apply stratification gains.",
        "Only approved analytic persons are loaded. PSUs outside this domain are unavailable; full survey-domain variance is not reconstructed.",
        "No finite-population correction, replicate weights or calibration uncertainty adjustment. Approximate intervals may be too wide or too narrow.",
        "Linear specification, recalled time, possible temporal overlap and unmeasured differences limit interpretation. Extremes and zeros retained in primary models.",
        "Pointwise 95% intervals are descriptive. Separate Bonferroni families cover primary outcomes and pairwise differences; no joint guarantee across both families or sensitivity models.",
        "Sensitivity and unadjusted models are comparisons, not additional confirmatory findings. Absence of resolved differences is not equivalence.",
        "No domain-specific minimum sample size has been scientifically approved; computational checks enforce n > p, full rank and at least two PSUs.",
        "Numerical completion awaits human scientific review; no Scientific Critic assessment or follow-up selection has occurred.",
    ]
    interpretation = [f"Adjusted {f.estimate.outcome}: {f.estimate.coefficient:.3f} minutes associated with an additional 300 minutes of weekday commuting; 95% interval [{f.estimate.interval.lower:.3f}, {f.estimate.interval.upper:.3f}]." for f in primary]
    interpretation.append(f"Ranking status: {primary_rank['status']}; point-estimate order is descriptive.")
    for s in sensitivity:
        interpretation.append(f"Sensitivity excludes {s['n_excluded']} zero-work records; n={s['n_after']}; ranking status {s['ranking']['status']}.")
    # Alternatives are candidates only; none receives an experiment ID or execution authorization.
    candidates = [
        {"question": "Is the commuting association nonlinear?", "hypothesis": "Linear slope may conceal variation over the exposure range",
         "expected_information": "Assess adequacy of a common linear slope", "required_variables": [spec.exposure, *spec.outcomes, *spec.covariates],
         "feasibility": "Variables available; method and specification require review", "cost": "Low",
         "limitations": "Additional modeling choices and comparisons", "decision_relevance": "Could change interpretation of a single coefficient", "selected": False},
        {"question": "Does the association differ by sex?", "hypothesis": "H3, not evaluated in EXP-001",
         "expected_information": "Assess whether an overall association masks subgroup differences", "required_variables": [spec.exposure, "sex", *spec.outcomes],
         "feasibility": "Variables available; interactions require a new approved specification", "cost": "Low",
         "limitations": "Subgroup uncertainty and multiple comparisons", "decision_relevance": "Could qualify interpretation of the pooled association", "selected": False},
    ]
    flags = sorted({"REQUIRES_HUMAN_REVIEW", primary_rank["status"], "MULTIPLE_COMPARISON_FAMILIES",
                    *(warning for f in fits for warning in f.diagnostics["warnings"])})
    provenance["dataset_hash_unchanged"] = sha(root / "data/processed/analytic_v1.parquet") == digest
    require(provenance["dataset_hash_unchanged"], "DATASET_CHANGED", "Analytic hash changed during execution")
    return ExperimentResult(schema_version="1.0", experiment_id=spec.experiment_id,
        status="EXPERIMENT_COMPLETED", dataset_version=spec.dataset_version,
        sample_size=len(population), weighted_population=float(population.weight.sum()),
        estimates=[f.estimate for f in fits], confidence_intervals={f.estimate.model_id: f.estimate.interval for f in fits},
        model_diagnostics={f.estimate.model_id: f.diagnostics for f in fits}, sensitivity_results=sensitivity,
        quality_flags=flags, limitations=limitations, scientific_interpretation=interpretation,
        supported_hypotheses=supported, unsupported_hypotheses=unsupported, inconclusive_hypotheses=inconclusive,
        candidate_next_experiments=candidates, ranking=primary_rank, population_counts=counts,
        missingness=missingness, transformations=[
            "Verify approved dataset SHA256 and historical manifest; read analytic_v1 only",
            "Sort by exact person_id; apply explicit state, inclusive age and sex filters in order",
            "Retain original FAC_PER weights; use constant mean scaling only in numerical equations",
            "Add intercept; sex female dummy (male reference), state 15 dummy (09 reference) when requested",
            "Complete cases separately for each model, without zero imputation or unrelated-feature exclusions",
            "Fit requested outcomes with approved covariates and unadjusted variants if requested",
            "Group weighted scores by (stratum, cluster), apply CR1 and t(G-1) intervals",
            "Use paired cluster influences for Bonferroni outcome contrasts on identical model samples",
            "Execute only listed sensitivity rules; primary population remains unchanged"],
        provenance=provenance, review_status="REQUIRES_HUMAN_REVIEW")


def run_experiment(spec: ExperimentSpec, *, root: Path = ROOT) -> ExperimentResult:
    """No output writes. Invalid input raises an ExperimentError with structured detail."""
    try:
        # Revalidate even a previously constructed/mutated model before any computation.
        value = spec.model_dump() if isinstance(spec, ExperimentSpec) else spec
        validated = ExperimentSpec.model_validate(value)
        return _run(validated, Path(root))
    except ExperimentError:
        raise
    except ValidationError as exc:
        raise ExperimentError("INVALID_SPECIFICATION_OR_RESULT", str(exc)) from exc
    except (OSError, KeyError, TypeError, ValueError, np.linalg.LinAlgError) as exc:
        raise ExperimentError("EXECUTION_ERROR", str(exc)) from exc
