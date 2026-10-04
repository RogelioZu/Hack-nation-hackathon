"""Local tools for the Experiment Planner (agents/experiment_planner.yaml).

Standard library only: no Supabase, embeddings or engine runs. The planner reads human-approved
hypotheses (reports/discovery/local/reviews/REV-*.json), their sources and the engine's real
capabilities (metadata/experiment_contract.schema.json + src/experiments/methods/__init__.py), and
stores candidate ExperimentProposal objects as reports/discovery/local/candidates/PROP-NNN.json
(the research-state "candidates" kind, docs/RESEARCH_STATE.md; ID field proposal_id).
It proposes; it never selects a proposal, assigns an experiment id or runs anything.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from commute_lab.critic_tools import _code_version, _numbers, _protocol_hypotheses
from commute_lab.experiment_views import _compact
from commute_lab.hypothesis_tools import (
    CAUSAL, CHOOSING, GROUP_COMPARISON, _approved_variables, _experiment_provenance, _source, _untraceable,
    _untraceable_integers, _words,
)

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY = ROOT / "reports" / "discovery" / "local"
REVIEW_DIR = DISCOVERY / "reviews"
HYPOTHESIS_DIR = DISCOVERY / "hypotheses"
CRITIQUE_DIR = DISCOVERY / "critiques"
PROPOSAL_DIR = DISCOVERY / "candidates"  # research-state kind; withdrawn ones live in candidates/superseded/
SCHEMA = ROOT / "metadata" / "experiment_contract.schema.json"
REGISTRY = ROOT / "src" / "experiments" / "methods" / "__init__.py"
ENGINE_DOC = ROOT / "docs" / "EXPERIMENT_ENGINE.md"
MANIFEST = ROOT / "metadata" / "analytic_v1_manifest.json"
AGENT_SPEC = ROOT / "agents" / "experiment_planner.yaml"
# The engine's own capability export, kept equal to src/experiments/capabilities.py by the engine validator.
ENGINE_CAPABILITIES = ROOT / "metadata" / "experiment_engine_capabilities.json"

MAX_ACTIVE = 8
LEVELS = ("LOW", "MEDIUM", "HIGH")
STATUSES = ("EXECUTABLE_NOW", "REQUIRES_ENGINE_EXTENSION", "NOT_FEASIBLE")
ROLES = ("FORMAL_HETEROGENEITY_TEST", "EXPLORATORY_SUBGROUP", "OTHER")
PROVENANCE_FILES = (SCHEMA, REGISTRY, MANIFEST)

SIGNIFICANCE_AS_GAIN = re.compile(r"\b(likely|expected|sure|bound) to be (statistically )?significant|"
                                  r"\bp[- ]?values?\b|\bp\s*<", re.IGNORECASE)
SELECTION = re.compile(r"\b(is|was|gets?) (selected|chosen)\b|\bwinn(ing|er)\b|\brecommended (as|for) (the )?next\b|"
                       r"\b(we|i) (will|should) (run|execute)\b|\brun (it|this) now\b", re.IGNORECASE)
EXPLORATORY_DISCLAIMER = re.compile(r"\b(not|cannot|insufficient|does not|do not)\b.{0,60}"
                                    r"\b(establish\w*|formal\w*|test\w* (whether|for)|demonstrat\w*)", re.IGNORECASE)
OVERCLAIM_RESULT = re.compile(r"\b(establish\w*|confirm\w*|demonstrat\w*|prov\w+)\b.{0,40}"
                              r"\b(heterogeneity|differ\w*|interaction)|\bsignificantly differ", re.IGNORECASE)
# An interval that includes zero is inconclusive, not evidence against the hypothesis.
INCLUDES_ZERO = re.compile(r"\b(includ\w*|cross\w*|span\w*|contain\w*|overlap\w*)\b.{0,15}\bzero\b", re.IGNORECASE)
# A subgroup coefficient compared with the pooled estimate is not a between-group contrast.
VERSUS_POOLED = re.compile(r"\b(overall|pooled|full[- ]sample)\s+(estimate|coefficient|association)", re.IGNORECASE)
EXCLUDES_ZERO = re.compile(r"\bexclud\w*\b.{0,10}\bzero\b", re.IGNORECASE)
EITHER_DIRECTION = re.compile(r"\b(either|any|both)\s+(direction|side)s?\b|\bpositive or negative\b|"
                              r"\bnegative or positive\b|\bregardless of (sign|direction)\b", re.IGNORECASE)
# "main effect" is standard non-causal regression terminology (the moderator's main term).
MAIN_EFFECT = re.compile(r"\bmain[- ]effects?\b", re.IGNORECASE)
OVERSTATEMENT = re.compile(r"\bdefinitive\w*|\bconclusive(ly)?\s+(evidence|proof|answer)|\bprov(e|es|en|ing)\b|"
                           r"\bproof\b", re.IGNORECASE)
EQUIVALENCE = re.compile(r"\b(equivalence|negligible|margin)\b", re.IGNORECASE)
MENTIONS_INTERACTION = re.compile(r"\binteraction", re.IGNORECASE)
MENTIONS_NONLINEAR = re.compile(r"\b(non-?linear|spline|polynomial|quadratic|threshold|piecewise|categor\w*)",
                                re.IGNORECASE)


def _ok(**data: Any) -> str:
    return json.dumps({"ok": True, **data}, ensure_ascii=False, default=str)


def _err(message: str, **data: Any) -> str:
    return json.dumps({"ok": False, "error": message, **data}, ensure_ascii=False, default=str)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


# --- Engine capability audit (derived from the committed schema and method registry) ---------

def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]


def _enum(field: dict) -> list:
    if "const" in field:
        return [field["const"]]
    items = field.get("items", {})
    return items.get("enum") or ([items["const"]] if "const" in items else [])


def _registry_methods() -> list[str]:
    """Method names in the closed registry (read as text: importing it would need numpy/pandas)."""
    text = REGISTRY.read_text(encoding="utf-8")
    block = re.search(r"METHODS\s*=\s*MappingProxyType\(\{(.*?)\}\)", text, re.DOTALL)
    return re.findall(r"[\"']([a-z_]+)[\"']\s*:", block.group(1)) if block else []


def _engine_export() -> dict:
    """Declared engine capabilities ({} for an engine that predates the export: schema audit only)."""
    return json.loads(ENGINE_CAPABILITIES.read_text(encoding="utf-8")) if ENGINE_CAPABILITIES.exists() else {}


def capability_audit() -> dict:
    """What the deterministic engine can execute today, with the evidence each answer comes from.

    Combines the schema/registry inspection with what the engine itself declares in
    metadata/experiment_engine_capabilities.json, so an approved engine extension is recognised
    without hard-coding proposals or variables.
    """
    defs = _schema()
    spec, population = defs["ExperimentSpec"]["properties"], defs["Population"]["properties"]
    spec_fields, population_fields = list(spec), list(population)

    def any_field(pattern: str) -> list[str]:
        return [f for f in spec_fields if re.search(pattern, f, re.IGNORECASE)]

    interaction_fields = any_field(r"interaction|formula|terms")
    contrast_fields = any_field(r"contrast|group_comparison|by_group|difference")
    nonlinear_fields = any_field(r"spline|polynomial|nonlinear|transform|categor|knot")
    uncertainty = _enum(spec["uncertainty"])
    methods = _registry_methods()
    engine = _engine_export()
    declared = engine.get("supported") or {}
    interactions = bool(interaction_fields) and bool(declared.get("exposure_x_binary_moderator_interaction", True))
    supported = {
        "population_filter_sex": "sexes" in population_fields,
        "population_filter_state": "states" in population_fields,
        "population_filter_age": "age_min" in population_fields and "age_max" in population_fields,
        "population_filter_has_child_u15": "has_child_u15" in population_fields,
        "population_filter_has_minor_u18": "has_minor_u18" in population_fields,
        "stratified_subgroup_models": bool({"sexes", "states", "age_min"} & set(population_fields)),
        "approved_covariates": bool(_enum(spec["covariates"])),
        "covariates_outside_schema": False,
        "interaction_terms": interactions,
        # A formal interaction coefficient with its own interval IS the between-group comparison.
        "formal_between_group_comparison": bool(contrast_fields) or
        (interactions and bool(declared.get("formal_interaction_coefficient_inference"))),
        "nonlinear_terms": bool(nonlinear_fields) or bool(declared.get("nonlinear_terms")),
        "cr1_cluster_uncertainty": "psu_cluster_CR1_t" in uncertainty,
        "full_survey_design_variance": any(u != "psu_cluster_CR1_t" for u in uncertainty) or
        bool(declared.get("full_complex_survey_variance")),
    }
    # Binary moderators whose main effect the engine adds through the interaction itself.
    moderators = sorted((engine.get("interaction") or {}).get("binary_moderators") or {}) if interactions else []
    return {
        "supported": supported,
        "spec_values": {"exposure": _enum(spec["exposure"]), "outcomes": _enum(spec["outcomes"]),
                        "covariates": _enum(spec["covariates"]), "method": _enum(spec["method"]),
                        "uncertainty": uncertainty, "sensitivity_analyses": _enum(spec["sensitivity_analyses"]),
                        "population": {"states": _enum(population["states"]), "sexes": _enum(population["sexes"]),
                                       "age_min": population["age_min"]["minimum"],
                                       "age_max": population["age_max"]["maximum"]}},
        "registry_methods": methods,
        "engine_binary_moderators": moderators,
        "evidence": {
            "engine_capabilities": _rel(ENGINE_CAPABILITIES) if engine else None,
            "engine_capabilities_sha256": _sha256(ENGINE_CAPABILITIES) if engine else None,
            "engine_declared": declared,
            "schema": _rel(SCHEMA), "schema_sha256": _sha256(SCHEMA),
            "registry": _rel(REGISTRY), "registry_sha256": _sha256(REGISTRY),
            "experiment_spec_fields": spec_fields, "population_fields": population_fields,
            "fields_matching_interaction": interaction_fields, "fields_matching_group_contrast": contrast_fields,
            "fields_matching_nonlinear": nonlinear_fields,
            "engine_doc_statement": "No interactions, education, marital status or other controls are inferred "
                                    "(docs/EXPERIMENT_ENGINE.md, 'Statistical method fixed before execution').",
            "ranking_note": "EXP-001 paired comparisons contrast OUTCOMES within the same sample; they are not "
                            "comparisons between population groups.",
            "subgroup_note": "Separate runs with a population filter give separate coefficients; the engine does "
                             "not compute their difference or its uncertainty (a formal interaction does).",
            "rank_deficiency": "Restricting to one sex while keeping 'sex' as covariate (or one state with "
                               "'state') makes the design rank-deficient: drop that covariate.",
        },
    }


# --- Inputs ------------------------------------------------------------------------------------

def _review(review_id: str) -> tuple[Path, dict]:
    if not re.fullmatch(r"REV-\d{3,}", review_id):
        raise ValueError("review_id must look like REV-001")
    path = REVIEW_DIR / f"{review_id}.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def _approved_hypotheses(review: dict) -> dict[str, tuple[Path, dict]]:
    """Approved hypotheses, refusing any whose bytes changed after the review."""
    recorded = {a["path"]: a["sha256"] for a in review.get("reviewed_artifacts", [])}
    found = {}
    for item in review.get("approved_hypotheses", []):
        path = HYPOTHESIS_DIR / f"{item['hypothesis_id']}.json"
        if recorded.get(_rel(path)) != _sha256(path):
            raise ValueError(f"{_rel(path)} changed after {review['review_id']}")
        found[item["hypothesis_id"]] = (path, json.loads(path.read_text(encoding="utf-8")))
    return found


def _inputs(review_id: str) -> dict:
    review_path, review = _review(review_id)
    hypotheses = _approved_hypotheses(review)
    experiment_ids = sorted({e for _, h in hypotheses.values() for e in h["source_experiment_ids"]})
    critique_ids = sorted({c for _, h in hypotheses.values() for c in h["source_critique_ids"]})
    experiments = {e: _source(e) for e in experiment_ids}
    critiques = {c: (CRITIQUE_DIR / f"{c}.json") for c in critique_ids}
    return {"review": (review_path, review), "hypotheses": hypotheses, "experiments": experiments,
            "critiques": {c: (p, json.loads(p.read_text(encoding="utf-8"))) for c, p in critiques.items()}}


def _active_proposals() -> list[dict]:
    if not PROPOSAL_DIR.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(PROPOSAL_DIR.glob("PROP-*.json"))]


def read_planning_context(review_id: str = "REV-001") -> str:
    """Approved hypotheses (with the human review), their evidence, approved variables and the engine audit."""
    try:
        data = _inputs(review_id)
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    review_path, review = data["review"]
    return _ok(
        human_review={"review_id": review["review_id"], "artifact": _rel(review_path), "decision": review["decision"],
                      "approved_hypotheses": review["approved_hypotheses"], "constraints": review["constraints"],
                      "scope": review["scope"]},
        hypotheses=[{k: h[k] for k in ("hypothesis_id", "scientific_question", "falsifiable_claim", "motivation",
                                       "required_variables", "expected_direction", "supporting_observation",
                                       "contradicting_observation", "engine_capability_assessment", "limitations",
                                       "source_experiment_ids", "source_critique_ids")}
                    for _, h in data["hypotheses"].values()],
        critiques=[{"critique_id": c["critique_id"], "scientific_status": c["scientific_status"],
                    "uncertainties": c["uncertainties"], "untested_questions": c["untested_questions"]}
                   for _, c in data["critiques"].values()],
        experiments=[{"experiment_id": e, "population": s.get("population"), "outcomes": s.get("outcomes"),
                      "covariates": s.get("covariates"), "result": _compact(r, s)}
                     for e, (_, r, s) in data["experiments"].items()],
        approved_variables={v: {k: d.get(k) for k in ("units", "missing")} for v, d in _approved_variables().items()},
        engine_capabilities=capability_audit(),
        existing_proposals=[{"proposal_id": p["proposal_id"], "hypothesis_ids": p["hypothesis_ids"],
                             "analysis_role": p["analysis_role"], "experimental_test": p["experimental_test"]}
                            for p in _active_proposals()],
        contract={"analysis_role": list(ROLES), "feasibility_status": list(STATUSES),
                  "information_gain_level": list(LEVELS),
                  "required_engine_capabilities_vocabulary": list(capability_audit()["supported"])},
    )


# --- Validation --------------------------------------------------------------------------------

def _check(p: dict, review_id: str) -> tuple[list[str], dict]:
    errors: list[str] = []
    required = ("hypothesis_ids", "scientific_question", "experimental_test", "analysis_role", "population",
                "exposure", "outcome", "covariates", "method", "required_variables", "comparison_or_estimand",
                "expected_information_gain", "scientific_value", "feasibility", "required_engine_capabilities",
                "limitations", "result_interpretation_plan")
    missing = [k for k in required if k not in p]
    if missing:
        return [f"missing fields: {missing}"], {}
    try:
        data = _inputs(review_id)
    except (OSError, ValueError, KeyError) as exc:
        return [f"inputs: {exc}"], {}
    audit = capability_audit()
    supported, values = audit["supported"], audit["spec_values"]
    approved_vars = set(_approved_variables())

    # Links to human-approved hypotheses only.
    ids = p["hypothesis_ids"] if isinstance(p["hypothesis_ids"], list) else []
    unknown = sorted(set(ids) - set(data["hypotheses"]))
    if not ids or unknown:
        errors.append(f"hypothesis_ids must be non-empty and approved in {review_id}; not approved: {unknown}")
    hypotheses = [data["hypotheses"][i][1] for i in ids if i in data["hypotheses"]]

    # Variables.
    variables = p["required_variables"] if isinstance(p["required_variables"], list) else []
    covariates = p["covariates"] if isinstance(p["covariates"], list) else []
    population = p["population"] if isinstance(p["population"], dict) else {}
    named = {p["exposure"], p["outcome"], *variables, *covariates}
    bad_vars = sorted(v for v in named if v not in approved_vars)
    if bad_vars:
        errors.append(f"variables not in the approved contract: {bad_vars}")
    population_fields = set(audit["evidence"]["population_fields"])
    extra_population = sorted(set(population) - population_fields - approved_vars)
    if extra_population:
        errors.append(f"population keys must be ExperimentSpec population fields or approved variables: {extra_population}")

    # Capabilities: vocabulary, truthful listing, and feasibility consistent with the audit.
    caps = p["required_engine_capabilities"] if isinstance(p["required_engine_capabilities"], list) else []
    unknown_caps = sorted(set(caps) - set(supported))
    if not caps or unknown_caps:
        errors.append(f"required_engine_capabilities must use the audit vocabulary {sorted(supported)}; "
                      f"unknown: {unknown_caps}")
    text_test = " ".join([str(p["experimental_test"]), str(p["comparison_or_estimand"]), str(p["method"])])
    implied = set()
    if MENTIONS_INTERACTION.search(text_test):
        implied.add("interaction_terms")
    if MENTIONS_NONLINEAR.search(text_test):
        implied.add("nonlinear_terms")
    for key, cap in (("has_child_u15", "population_filter_has_child_u15"),
                     ("has_minor_u18", "population_filter_has_minor_u18")):
        if key in population:
            implied.add(cap)
    if isinstance(population.get("sexes"), list) and len(population["sexes"]) == 1:
        implied.add("population_filter_sex")
    missing_caps = sorted(implied - set(caps))
    if missing_caps:
        errors.append(f"the proposal needs capabilities it does not list: {missing_caps}")
    outside = set(covariates) - set(values["covariates"]) - set(audit["engine_binary_moderators"])
    if outside and "covariates_outside_schema" not in caps:
        errors.append("covariates outside the schema require 'covariates_outside_schema' in required_engine_capabilities")
    unsupported = sorted(c for c in set(caps) | implied if not supported.get(c, False))
    if outside:
        unsupported.append("covariates_outside_schema")

    feasibility = p["feasibility"] if isinstance(p["feasibility"], dict) else {}
    status = feasibility.get("status")
    if status not in STATUSES or not str(feasibility.get("reason", "")).strip():
        errors.append(f"feasibility needs status in {STATUSES} and a reason")
    elif unsupported and status == "EXECUTABLE_NOW":
        errors.append(f"EXECUTABLE_NOW contradicts the engine audit: unsupported {sorted(set(unsupported))}; "
                      f"use REQUIRES_ENGINE_EXTENSION")
    elif not unsupported and status == "REQUIRES_ENGINE_EXTENSION":
        errors.append("every listed capability is supported today: status should be EXECUTABLE_NOW (or list the "
                      "missing capability)")
    if status == "EXECUTABLE_NOW":
        if p["method"] not in audit["registry_methods"] or p["method"] not in values["method"]:
            errors.append(f"EXECUTABLE_NOW needs a registered method {audit['registry_methods']}")
        if p["exposure"] not in values["exposure"] or p["outcome"] not in values["outcomes"]:
            errors.append("EXECUTABLE_NOW needs the schema exposure and one of the schema outcomes")
        bad_population = {k: v for k, v in population.items() if k not in population_fields}
        allowed_values = values["population"]
        if bad_population or not set(population.get("sexes", [])) <= set(allowed_values["sexes"]) \
                or not set(population.get("states", [])) <= set(allowed_values["states"]):
            errors.append("EXECUTABLE_NOW needs a population expressible with the schema (states, sexes, age_min, "
                          "age_max)")
        if len(population.get("sexes", [])) == 1 and "sex" in covariates:
            errors.append("restricting to one sex while keeping 'sex' as covariate is rank-deficient: drop 'sex'")
        if len(population.get("states", [])) == 1 and "state" in covariates:
            errors.append("restricting to one state while keeping 'state' as covariate is rank-deficient: drop 'state'")

    # Heterogeneity: formal test vs exploratory subgroup models (human-review constraint).
    role = p["analysis_role"]
    if role not in ROLES:
        errors.append(f"analysis_role must be one of {ROLES}")
    between_group = any(GROUP_COMPARISON.search(f"{h['scientific_question']} {h['falsifiable_claim']}")
                        for h in hypotheses)
    if between_group and role == "OTHER":
        errors.append("these hypotheses ask whether groups differ: analysis_role must be FORMAL_HETEROGENEITY_TEST "
                      "or EXPLORATORY_SUBGROUP")
    formal_caps = {"interaction_terms", "formal_between_group_comparison"}
    plan = p["result_interpretation_plan"] if isinstance(p["result_interpretation_plan"], dict) else {}
    if role == "FORMAL_HETEROGENEITY_TEST" and not formal_caps & set(caps):
        errors.append("a formal heterogeneity test needs 'interaction_terms' or 'formal_between_group_comparison': "
                      "separate subgroup coefficients do not test the difference")
    if role == "EXPLORATORY_SUBGROUP":
        if formal_caps & set(caps):
            errors.append("an exploratory subgroup analysis must not list formal comparison capabilities")
        disclaimer = " ".join([*map(str, p["limitations"]), str(p["experimental_test"])])
        if not EXPLORATORY_DISCLAIMER.search(disclaimer):
            errors.append("an exploratory subgroup proposal must state explicitly (limitations or experimental_test) "
                          "that separate subgroup estimates cannot establish heterogeneity")
        if OVERCLAIM_RESULT.search(str(plan.get("supporting_result", ""))):
            errors.append("supporting_result of an exploratory subgroup analysis cannot claim heterogeneity is "
                          "established")

    # Interaction terms need the moderator's main effect (a missing main effect misspecifies the model).
    if role == "FORMAL_HETEROGENEITY_TEST" and "interaction_terms" in caps:
        estimand = f"{p['comparison_or_estimand']} {p['experimental_test']}"
        moderators = sorted(v for v in approved_vars - {p["exposure"], p["outcome"], "commute_weekday_min"}
                            if re.search(rf"(?<![A-Za-z0-9]){re.escape(v)}(?![A-Za-z0-9])", estimand))
        if not moderators:
            errors.append("name the moderator (an approved variable, e.g. sex or has_child_u15) in the interaction "
                          "estimand")
        for m in moderators:
            if m not in covariates or m not in variables:
                errors.append(f"interaction with {m}: include {m} as a main effect in covariates and in "
                              f"required_variables")
            if m not in values["covariates"] and m not in audit["engine_binary_moderators"] \
                    and "covariates_outside_schema" not in caps:
                errors.append(f"{m} is not a schema covariate: add 'covariates_outside_schema' to "
                              f"required_engine_capabilities")

    # Two-sided hypotheses: any interval that excludes zero supports them.
    if hypotheses and all(h.get("expected_direction") == "difference_either_direction" for h in hypotheses):
        if not EITHER_DIRECTION.search(str(plan.get("supporting_result", ""))):
            errors.append("the hypothesis predicts a difference in either direction: supporting_result must accept "
                          "an interval that excludes zero in either direction")
        contradicting = str(plan.get("contradicting_result", ""))
        if EXCLUDES_ZERO.search(contradicting) or not EQUIVALENCE.search(contradicting):
            errors.append("for a two-sided hypothesis any interval excluding zero supports it, and an interval that "
                          "merely includes zero is inconclusive. The only contradicting result is equivalence: the "
                          "whole interval of the difference lies within a negligible margin around zero, a margin "
                          "to be fixed by human review before analysis (do not invent its value). Write "
                          "contradicting_result that way, using the words 'equivalence' or 'negligible margin'")

    # Not a repeat of the source experiment.
    for eid, (_, _, spec) in data["experiments"].items():
        src = spec["population"]
        same_population = set(population.get("sexes", src["sexes"])) == set(src["sexes"]) \
            and set(population.get("states", src["states"])) == set(src["states"]) \
            and population.get("age_min", src["age_min"]) == src["age_min"] \
            and population.get("age_max", src["age_max"]) == src["age_max"] \
            and not (set(population) - population_fields)
        adds = (set(caps) | implied) & {"interaction_terms", "formal_between_group_comparison", "nonlinear_terms",
                                        "covariates_outside_schema", "full_survey_design_variance"}
        if same_population and not adds and p["outcome"] in spec["outcomes"] \
                and set(covariates) <= set(spec["covariates"]):
            errors.append(f"repeats {eid}: same population, outcome and model; it adds no information")

    # Contract fields.
    gain = p["expected_information_gain"] if isinstance(p["expected_information_gain"], dict) else {}
    if gain.get("level") not in LEVELS or len(str(gain.get("reason", "")).strip()) < 40:
        errors.append(f"expected_information_gain needs level in {LEVELS} and a substantive reason")
    if SIGNIFICANCE_AS_GAIN.search(str(gain.get("reason", ""))):
        errors.append("information gain must not rely on expected statistical significance")
    for key in ("supporting_result", "contradicting_result", "inconclusive_result"):
        if not str(plan.get(key, "")).strip():
            errors.append(f"result_interpretation_plan needs {key}")
    if INCLUDES_ZERO.search(str(plan.get("contradicting_result", ""))):
        errors.append("contradicting_result cannot be an interval that includes zero: that is inconclusive (absence "
                      "of evidence is not evidence against). Contradicting = the interval excludes zero in the "
                      "opposite direction; put 'includes zero' under inconclusive_result")
    if role == "EXPLORATORY_SUBGROUP" and VERSUS_POOLED.search(" ".join(map(str, plan.values()))):
        errors.append("do not compare a subgroup coefficient with the overall/pooled estimate: that is not a "
                      "between-group contrast. Describe each subgroup estimate and its interval on its own")
    if not str(p["scientific_value"]).strip() or not p["limitations"]:
        errors.append("scientific_value and limitations are required")

    # Language, experiment ids, selection and numbers.
    texts = [str(p["scientific_question"]), str(p["experimental_test"]), str(p["comparison_or_estimand"]),
             str(p["scientific_value"]), str(gain.get("reason", "")), str(feasibility.get("reason", "")),
             *map(str, p["limitations"]), *map(str, plan.values())]
    for text in texts:
        if OVERSTATEMENT.search(text):
            errors.append(f"overstated evidence ('{OVERSTATEMENT.search(text).group(0)}'): an observational test "
                          f"gives an association estimate with uncertainty, never definitive evidence or proof")
        text = MAIN_EFFECT.sub("main term", text)
        if CAUSAL.search(text):
            errors.append(f"causal wording ('{CAUSAL.search(text).group(0)}'): use association language "
                          f"(e.g. 'interaction term', 'coefficient difference')")
        if CHOOSING.search(text) or SELECTION.search(text):
            errors.append("the planner proposes; it does not select, schedule or run an experiment")
    ids_used = {i for t in texts for i in re.findall(r"EXP-\d{3,}", t)} - set(data["experiments"])
    if ids_used:
        errors.append(f"references experiments that are not sources (no EXP id may be assigned): {sorted(ids_used)}")
    allowed = set()
    for _, r, s in data["experiments"].values():
        allowed |= _numbers(_compact(r, s)) | _numbers(s)
    for _, h in data["hypotheses"].values():
        allowed |= _numbers({k: v for k, v in h.items() if k != "provenance"})
    for _, c in data["critiques"].values():
        allowed |= _numbers({k: v for k, v in c.items() if k != "provenance"})
    allowed |= _numbers(data["review"][1]["approved_hypotheses"]) | _numbers(values) \
        | _numbers(list(approved_vars)) | _numbers(_protocol_hypotheses())
    allowed |= {round(x * 100, 4) for x in allowed if 0 < abs(x) < 1}
    bad = _untraceable(texts, allowed) + _untraceable_integers(texts, allowed)
    if bad:
        errors.append(f"numbers not found in the sources (no invented results): {sorted(set(bad))}")
    return errors, data


def _duplicate_of(p: dict) -> str | None:
    signature = (tuple(sorted(p.get("hypothesis_ids", []))), p.get("analysis_role"), p.get("outcome"),
                 json.dumps(p.get("population"), sort_keys=True))
    text = _words(f"{p.get('experimental_test', '')} {p.get('comparison_or_estimand', '')}")
    for other in _active_proposals():
        other_signature = (tuple(sorted(other["hypothesis_ids"])), other["analysis_role"], other["outcome"],
                           json.dumps(other["population"], sort_keys=True))
        other_text = _words(f"{other['experimental_test']} {other['comparison_or_estimand']}")
        same_target = signature[0] == other_signature[0] and signature[2] == other_signature[2]
        if signature == other_signature or (same_target and text and other_text and
                                            len(text & other_text) / len(text | other_text) >= 0.7):
            return other["proposal_id"]
    return None


def validate_proposal(proposal: dict, review_id: str = "REV-001") -> str:
    """Dry run: every validation error for one ExperimentProposal, without saving."""
    errors, _ = _check(proposal, review_id)
    if (duplicate := _duplicate_of(proposal)):
        errors.append(f"duplicate of {duplicate}")
    return _ok(valid=not errors, errors=errors)


def _declared_model() -> str | None:
    text = AGENT_SPEC.read_text(encoding="utf-8") if AGENT_SPEC.exists() else ""
    m = re.search(r"^\s+model:\s*(\S+)", text, re.MULTILINE)
    return m.group(1) if m else None


def save_proposal(proposal: dict, review_id: str = "REV-001") -> str:
    """Validate and store one ExperimentProposal as PROP-NNN; never overwrites, never selects or runs it."""
    errors, data = _check(proposal, review_id)
    if (duplicate := _duplicate_of(proposal)):
        errors.append(f"duplicate of {duplicate}")
    if len(_active_proposals()) >= MAX_ACTIVE:
        errors.append(f"already {MAX_ACTIVE} active proposals")
    if errors:
        return _err("proposal rejected", errors=errors)

    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
    numbers = [int(x.stem.split("-")[1]) for x in PROPOSAL_DIR.rglob("PROP-*.json")]
    proposal_id = f"PROP-{max(numbers, default=0) + 1:03d}"
    review_path, review = data["review"]
    hypotheses = {i: data["hypotheses"][i] for i in proposal["hypothesis_ids"]}
    critique_ids = sorted({c for _, h in hypotheses.values() for c in h["source_critique_ids"]})
    experiment_ids = sorted({e for _, h in hypotheses.values() for e in h["source_experiment_ids"]})
    record = {
        "proposal_id": proposal_id,
        "hypothesis_ids": proposal["hypothesis_ids"],
        "scientific_question": proposal["scientific_question"],
        "experimental_test": proposal["experimental_test"],
        "analysis_role": proposal["analysis_role"],
        "population": proposal["population"],
        "exposure": proposal["exposure"],
        "outcome": proposal["outcome"],
        "covariates": proposal["covariates"],
        "method": proposal["method"],
        "required_variables": proposal["required_variables"],
        "comparison_or_estimand": proposal["comparison_or_estimand"],
        "expected_information_gain": proposal["expected_information_gain"],
        "scientific_value": proposal["scientific_value"],
        "feasibility": {**proposal["feasibility"], "checked_against": "engine capability audit (schema + registry)"},
        "required_engine_capabilities": proposal["required_engine_capabilities"],
        "limitations": proposal["limitations"],
        "result_interpretation_plan": proposal["result_interpretation_plan"],
        "selected": False,
        "experiment_id": None,
        "review_status": "REQUIRES_HUMAN_REVIEW",
        "provenance": {
            "hypothesis_ids": proposal["hypothesis_ids"],
            "critique_ids": critique_ids,
            "experiment_ids": experiment_ids,
            "human_review_id": review["review_id"],
            "dataset_version": sorted({r["dataset_version"] for _, r, _ in data["experiments"].values()}),
            "agent": "experiment_planner",
            "model": _declared_model(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "code_version": _code_version(),
            "engine_capability_audit": {k: capability_audit()["evidence"][k]
                                        for k in ("schema_sha256", "registry_sha256")},
            "source_artifacts": [
                {"path": _rel(review_path), "sha256": _sha256(review_path)},
                *[{"path": _rel(path), "sha256": _sha256(path)} for path, _ in hypotheses.values()],
                *[{"path": _rel(CRITIQUE_DIR / f"{c}.json"), "sha256": _sha256(CRITIQUE_DIR / f"{c}.json")}
                  for c in critique_ids],
                *[_experiment_provenance(path) for path, _, _ in data["experiments"].values()],
                *[{"path": _rel(f), "sha256": _sha256(f)} for f in PROVENANCE_FILES],
            ],
        },
    }
    path = PROPOSAL_DIR / f"{proposal_id}.json"
    with path.open("x", encoding="utf-8", newline="\n") as f:  # "x": never overwrite
        f.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return _ok(proposal_id=proposal_id, artifact=_rel(path))
