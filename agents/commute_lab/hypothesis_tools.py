"""Local tools for the Hypothesis Agent (agents/hypothesis_agent.yaml).

Standard library only: no Supabase, embeddings, PDF parsing or engine runs. The agent reads a
committed ExperimentResult and its ScientificCritique, and stores 2-4 falsifiable hypotheses as
reports/discovery/local/hypotheses/HYP-NNN.json (same convention as the critiques). It never
chooses what to test next: that is the Experiment Planner's job, after human review.

Every variable must exist in the approved contract (metadata/analytic_v1_manifest.json) and every
engine statement is checked against metadata/experiment_contract.schema.json.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from commute_lab.critic_tools import _code_version, _numbers, _protocol_hypotheses, _untraceable
from commute_lab.experiment_views import _compact

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "experiments"
DISCOVERY = ROOT / "reports" / "discovery" / "local"
CRITIQUE_DIR = DISCOVERY / "critiques"
HYPOTHESIS_DIR = DISCOVERY / "hypotheses"  # active artifacts; withdrawn ones live in hypotheses/superseded/
MANIFEST = ROOT / "metadata" / "analytic_v1_manifest.json"
SCHEMA = ROOT / "metadata" / "experiment_contract.schema.json"
DATA_CONTRACT = ROOT / "docs" / "DATA_CONTRACT.md"
AGENT_SPEC = ROOT / "agents" / "hypothesis_agent.yaml"

MAX_PER_CRITIQUE = 4
DIRECTIONS = ("more_negative", "less_negative", "negative", "positive", "difference_either_direction", None)
EVIDENCE_SOURCES = ("estimates", "ranking", "sensitivity", "population_counts", "diagnostics_adjusted",
                    "limitations", "quality_flags", "supported_hypotheses", "inconclusive_hypotheses",
                    "unsupported_hypotheses", "sample_size", "critique")

# Observational language only (AGENTS.md §2). "increase" as a noun ("a 300-minute increase") is allowed.
CAUSAL = re.compile(r"\b(causes?|caused|causing|causal effect|leads? to|led to|results? in|produces?|"
                    r"reduces?|reduced|increases|increased|drives?|driven by|impacts?|effects?|"
                    r"due to|because of|sacrific\w*)\b", re.IGNORECASE)
# The EXP-001 ranking is unresolved: sleep has the strongest negative POINT ESTIMATE, not association.
RANKING_OVERCLAIM = re.compile(r"strongest(\s+negative)?\s+association|most\s+(displaced|affected|sacrificed)",
                               re.IGNORECASE)
VAGUE = re.compile(r"\b(may|might|could|possibly|perhaps|somehow|affects?|matters?|is important|"
                   r"is bad|is good|some people|various)\b", re.IGNORECASE)
COMPARATIVE = re.compile(r"\b(more|less|larger|smaller|stronger|weaker|greater|higher|lower|below|above|steeper|flatter|"
                         r"differ\w*|exceed\w*|negative|positive|excludes? zero|nonzero|non-zero|opposite)\b",
                         re.IGNORECASE)
NON_LINEAR_METHODS = re.compile(r"\b(interaction|non-?linear|spline|threshold|quadratic|polynomial|two-part|"
                                r"quantile|categor\w*|piecewise)\b", re.IGNORECASE)
# A decision criterion must use the engine's uncertainty, not a bare point-estimate order.
UNCERTAINTY = re.compile(r"\b(interval|excludes? zero|includes? zero|confidence|bonferroni|overlap\w*|"
                         r"statistically distinguishable|indistinguishable|uncertainty)\b", re.IGNORECASE)
# Between-group comparisons: separate subgroup runs are descriptive, not a formal test (engine contract).
GROUP_COMPARISON = re.compile(r"\bamong\b.+\bthan (among|for|in)\b|\bdiffer\w*\s+(by|between|across)\b|"
                              r"\bbetween (women|men|female|male)|\bwith(out)? (a )?child", re.IGNORECASE)
# Something the source experiment did not estimate: a subgroup / between-group comparison or a
# different functional form (new approved variables are checked separately).
SUBGROUP = re.compile(r"\b(among|within|subgroup\w*|women|men|female\w*|male\w*|state 09|state 15|"
                      r"mexico city|estado de m[eé]xico|aged?)\b", re.IGNORECASE)
CHOOSING = re.compile(r"\b(test(ed)? next|next experiment|should be (tested|prioriti[sz]ed|selected)|"
                      r"we (will|should) (test|run)|selected for testing)\b", re.IGNORECASE)
SNAKE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
WORD = re.compile(r"[a-z0-9_]+")
STOP = set("a an the of in on at to for and or by with as is are be than that this those these among "
           "between within across per from into their its it whether which who when".split())


def _ok(**data: Any) -> str:
    return json.dumps({"ok": True, **data}, ensure_ascii=False, default=str)


def _err(message: str, **data: Any) -> str:
    return json.dumps({"ok": False, "error": message, **data}, ensure_ascii=False, default=str)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _source(experiment_id: str) -> tuple[Path, dict, dict]:
    """Published result + spec, after checking result.json against validation.json.

    EXP-001's result.json was validated with CRLF line endings, but git stores it with LF (commit
    2d00fda), so an LF checkout differs only in line endings. Accept the file if its bytes match
    the recorded hash, or if its CRLF reconstruction does (identical content); anything else fails.
    """
    if not re.fullmatch(r"EXP-\d{3,}", experiment_id):
        raise ValueError("experiment_id must look like EXP-001")
    out = REPORT_DIR / experiment_id
    path = out / "result.json"
    recorded = json.loads((out / "validation.json").read_text(encoding="utf-8"))
    raw = path.read_bytes()
    crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if recorded.get("status") != "PASS" or recorded.get("result_sha256") not in (
            hashlib.sha256(raw).hexdigest(), hashlib.sha256(crlf).hexdigest()):
        raise ValueError(f"{_rel(path)} does not match its validation.json")
    return path, json.loads(raw.decode("utf-8")), json.loads((out / "spec.json").read_text(encoding="utf-8"))


def _integrity(path: Path) -> str:
    recorded = json.loads((path.parent / "validation.json").read_text(encoding="utf-8")).get("result_sha256")
    return "exact bytes" if _sha256(path) == recorded else "content identical; LF checkout of CRLF-validated bytes"


def _experiment_provenance(path: Path) -> dict:
    """Experiment result reference: bytes observed in this run vs the certified hash (validation.json)."""
    certified = json.loads((path.parent / "validation.json").read_text(encoding="utf-8")).get("result_sha256")
    return {"path": _rel(path), "observed_sha256": _sha256(path), "certified_sha256": certified,
            "integrity": _integrity(path)}


def _approved_variables() -> dict[str, dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {v: manifest["feature_definitions"].get(v, {}) for v in manifest["canonical_variables"]}


def _engine_contract() -> dict:
    """What the deterministic engine accepts today, read from the committed JSON Schema."""
    defs = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]
    spec, population = defs["ExperimentSpec"]["properties"], defs["Population"]["properties"]

    def values(field: dict) -> list:
        return [field["const"]] if "const" in field else field.get("items", {}).get("enum") or \
            ([field["items"]["const"]] if "const" in field.get("items", {}) else [])
    return {
        "exposure": values(spec["exposure"]), "outcomes": values(spec["outcomes"]),
        "covariates": values(spec["covariates"]), "method": values(spec["method"]),
        "sensitivity_analyses": values(spec["sensitivity_analyses"]),
        "population_filters": {"states": values(population["states"]), "sexes": values(population["sexes"]),
                               "age_range": [population["age_min"]["minimum"], population["age_max"]["maximum"]]},
        "not_in_schema": ("Interaction terms, non-linear terms (splines, polynomials, thresholds, categories), "
                          "two-part or quantile models, and any covariate outside the list above are not part "
                          "of the current ExperimentSpec (docs/EXPERIMENT_ENGINE.md). Separate subgroup runs "
                          "via population filters are descriptive comparisons, not a formal interaction test."),
    }


def _critique(critique_id: str) -> tuple[Path, dict]:
    if not re.fullmatch(r"CRIT-EXP-\d{3,}-\d{3}", critique_id):
        raise ValueError("critique_id must look like CRIT-EXP-001-001")
    path = CRITIQUE_DIR / f"{critique_id}.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def _saved(source_critique: str | None = None) -> list[dict]:
    if not HYPOTHESIS_DIR.exists():
        return []
    found = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(HYPOTHESIS_DIR.glob("HYP-*.json"))]
    return [h for h in found if source_critique is None or source_critique in h.get("source_critique_ids", [])]


def _declared_executor() -> dict:
    text = AGENT_SPEC.read_text(encoding="utf-8") if AGENT_SPEC.exists() else ""
    return {key: (m.group(1) if (m := re.search(rf"^\s+{key}:\s*(\S+)", text, re.MULTILINE)) else None)
            for key in ("harness", "model")}


def _untraceable_integers(texts: list[str], allowed: set[float]) -> list[str]:
    """Integers (e.g. thresholds like -30) that appear in no source; ignores ids such as EXP-001 or H3."""
    bad = []
    for text in texts:
        cleaned = re.sub(r"\b(EXP|CRIT|HYP)-[\d-]+|\bH\d\b|[a-z_]*_[a-z0-9_]*|\d+\.\d+", " ", text)
        for token in re.findall(r"[-−]?\b\d+\b", cleaned):
            if abs(float(token.replace("−", "-"))) not in {abs(x) for x in allowed}:
                bad.append(token)
    return bad


def _keys(value: Any) -> set[str]:
    """All dict keys in a JSON value, lowercased (field names of the source artifacts)."""
    if isinstance(value, dict):
        return {str(k).lower() for k in value} | set().union(*(_keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(v) for v in value)) if value else set()
    return set()


def _words(text: str) -> set[str]:
    return {w for w in WORD.findall(text.lower()) if w not in STOP and len(w) > 2}


def read_hypothesis_context(experiment_id: str = "EXP-001", critique_id: str = "CRIT-EXP-001-001") -> str:
    """Evidence (compact ExperimentResult), the critique, approved variables, H1-H4 and the engine contract."""
    try:
        result_path, result, spec = _source(experiment_id)
        critique_path, critique = _critique(critique_id)
    except (OSError, ValueError) as exc:
        return _err(str(exc))
    if critique.get("experiment_id") != experiment_id:
        return _err(f"{critique_id} critiques {critique.get('experiment_id')}, not {experiment_id}")
    variables = _approved_variables()
    return _ok(
        experiment={"id": experiment_id, "artifact": _rel(result_path), "sha256": _sha256(result_path),
                    "integrity": _integrity(result_path), "dataset_version": result["dataset_version"],
                    "result": _compact(result, spec)},
        critique={"id": critique_id, "artifact": _rel(critique_path), "sha256": _sha256(critique_path),
                  **{k: critique[k] for k in ("scientific_status", "status_rationale", "evidence_summary",
                                              "uncertainties", "limitations", "unsupported_claims",
                                              "untested_questions")}},
        approved_variables={v: {k: d.get(k) for k in ("units", "transformation", "missing")}
                            for v, d in variables.items()},
        protocol_hypotheses=_protocol_hypotheses(),
        engine_contract=_engine_contract(),
        existing_hypotheses=[{"hypothesis_id": h["hypothesis_id"], "scientific_question": h["scientific_question"],
                              "falsifiable_claim": h["falsifiable_claim"]} for h in _saved(critique_id)],
        limits={"max_hypotheses_per_critique": MAX_PER_CRITIQUE, "expected_direction": list(DIRECTIONS),
                "observed_evidence_sources": list(EVIDENCE_SOURCES)},
    )


def _check(h: dict) -> tuple[list[str], dict]:
    """All validation errors for one hypothesis (empty list = valid) plus resolved sources."""
    errors: list[str] = []
    required = ("source_experiment_ids", "source_critique_ids", "scientific_question", "falsifiable_claim",
                "motivation", "required_variables", "expected_direction", "supporting_observation",
                "contradicting_observation", "current_evidence_status", "engine_capability_assessment",
                "limitations")
    missing = [k for k in required if k not in h]
    if missing:
        return [f"missing fields: {missing}"], {}

    # Sources must exist and match.
    sources: dict = {"experiments": {}, "critiques": {}}
    for eid in h["source_experiment_ids"] or ["<none>"]:
        try:
            path, result, spec = _source(eid)
            sources["experiments"][eid] = (path, result, spec)
        except (OSError, ValueError) as exc:
            errors.append(f"source experiment {eid}: {exc}")
    for cid in h["source_critique_ids"] or ["<none>"]:
        try:
            path, critique = _critique(cid)
            sources["critiques"][cid] = (path, critique)
            if critique.get("experiment_id") not in h["source_experiment_ids"]:
                errors.append(f"{cid} critiques {critique.get('experiment_id')}, not a listed source experiment")
        except (OSError, ValueError) as exc:
            errors.append(f"source critique {cid}: {exc}")
    if errors:
        return errors, sources

    m = h["motivation"] if isinstance(h["motivation"], dict) else {}
    observed, inference, unresolved = (m.get(k) or [] for k in ("observed_evidence", "scientific_inference",
                                                                  "unresolved_uncertainty"))
    if not observed or not inference or not unresolved:
        errors.append("motivation needs non-empty observed_evidence, scientific_inference and unresolved_uncertainty")
    if not all(isinstance(o, dict) and str(o.get("statement", "")).strip()
               and str(o.get("source", "")).split(".")[0].split("[")[0] in EVIDENCE_SOURCES for o in observed):
        errors.append(f"each observed_evidence item needs a statement and a source field starting with one of "
                      f"{EVIDENCE_SOURCES} (use 'critique.<field>' for the critique)")
    if not all(isinstance(s, str) and s.strip() for s in [*inference, *unresolved]):
        errors.append("scientific_inference and unresolved_uncertainty must be lists of non-empty strings")
    if h["current_evidence_status"] != "UNTESTED":
        errors.append("current_evidence_status must be UNTESTED: a new hypothesis is not evidence")
    if h["expected_direction"] not in DIRECTIONS:
        errors.append(f"expected_direction must be one of {list(DIRECTIONS)}")

    question, claim = str(h["scientific_question"]).strip(), str(h["falsifiable_claim"]).strip()
    support, contra = str(h["supporting_observation"]).strip(), str(h["contradicting_observation"]).strip()
    if not question.endswith("?"):
        errors.append("scientific_question must be a question ending with '?'")
    if not support or not contra or _words(support) == _words(contra):
        errors.append("supporting_observation and contradicting_observation must be distinct and specific")
    if not UNCERTAINTY.search(support) or not UNCERTAINTY.search(contra):
        errors.append("supporting_observation and contradicting_observation must each state a decision criterion "
                      "based on uncertainty (e.g. an interval that excludes / includes zero), not only which "
                      "point estimate is larger: point estimates alone cannot falsify the claim")

    # Variables: declared list and every snake_case token used must be approved.
    approved = set(_approved_variables())
    contract = _engine_contract()
    variables = h["required_variables"] if isinstance(h["required_variables"], list) else []
    unknown = sorted(set(variables) - approved)
    if not variables or unknown:
        errors.append(f"required_variables must be non-empty and approved; unknown: {unknown}")
    observed_text = [str(o.get("statement", "")) for o in observed if isinstance(o, dict)]
    texts = [question, claim, support, contra, *observed_text, *map(str, inference), *map(str, unresolved),
             *map(str, h["limitations"]), str((h["engine_capability_assessment"] or {}).get("reason", ""))]
    # Field names of the source artifacts (e.g. point_estimate_order) are references, not variables.
    field_names = set().union(*(_keys(_compact(r, s)) for _, r, s in sources["experiments"].values()),
                              *(_keys(c) for _, c in sources["critiques"].values()))
    known_tokens = approved | field_names | {*contract["method"], *contract["sensitivity_analyses"],
                                             "psu_cluster_cr1_t", "approved_analytic_v1", "analytic_v1",
                                             "model_specific_complete_case"}
    stray = sorted({t for text in texts for t in SNAKE.findall(text)} - known_tokens)
    if stray:
        errors.append(f"unknown variable-like names (not in the approved contract): {stray}")
    named_in_claim = {t for t in SNAKE.findall(claim)} & approved
    if not named_in_claim:
        errors.append("falsifiable_claim must name at least one approved variable explicitly")

    # Observed evidence may only concern what EXP-001 actually estimated.
    for eid, (_, _, spec) in sources["experiments"].items():
        estimated = {spec["exposure"], *spec["outcomes"], *spec["covariates"]}
        for text in observed_text:
            outside = {t for t in SNAKE.findall(text)} & approved - estimated
            if outside:
                errors.append(f"observed_evidence mentions {sorted(outside)}, which {eid} did not estimate: "
                              f"that is an inference or a new hypothesis, not observed evidence")

    # Novelty: re-estimating the source model on the same population is not a new hypothesis.
    for eid, (_, _, spec) in sources["experiments"].items():
        estimated = {spec["exposure"], *spec["outcomes"], *spec["covariates"]}
        new_variables = set(variables) - estimated - {"commute_weekday_min", "weight", "stratum", "cluster"}
        text = " ".join([question, claim])
        if not new_variables and not SUBGROUP.search(text) and not GROUP_COMPARISON.search(text) \
                and not NON_LINEAR_METHODS.search(text):
            errors.append(f"not a new hypothesis: {eid} already estimated these variables on the same population "
                          f"with the same model, and its result is in the evidence. Add a subgroup or "
                          f"between-group comparison, an approved variable {eid} did not use, or a different "
                          f"functional form")

    # Language: observational, no ranking overclaim, testable, no experiment choice.
    for text in texts:
        if CAUSAL.search(text):
            errors.append(f"causal wording ('{CAUSAL.search(text).group(0)}'): use association language")
        if RANKING_OVERCLAIM.search(text):
            errors.append("ranking overclaim: say 'strongest negative point estimate', not strongest association")
        if CHOOSING.search(text):
            errors.append("the Hypothesis Agent does not choose or schedule what to test next")
    if VAGUE.search(claim):
        errors.append(f"falsifiable_claim is hedged or vague ('{VAGUE.search(claim).group(0)}'): state a "
                      f"pattern that a future analysis can contradict")
    if not COMPARATIVE.search(claim):
        errors.append("falsifiable_claim needs a testable comparison or direction (e.g. more negative, differs, "
                      "excludes zero)")
    ids = {i for text in texts for i in re.findall(r"EXP-\d{3,}", text)} - set(h["source_experiment_ids"])
    if ids:
        errors.append(f"references experiments that are not sources: {sorted(ids)}")

    # Numbers must come from the sources.
    allowed = set()
    for _, result, spec in sources["experiments"].values():
        allowed |= _numbers(_compact(result, spec)) | _numbers(spec)
    for _, critique in sources["critiques"].values():
        allowed |= _numbers({k: v for k, v in critique.items() if k != "provenance"})
    allowed |= {round(x * 100, 4) for x in allowed if 0 < abs(x) < 1}  # 0.95 written as 95%
    allowed |= _numbers(list(_approved_variables())) | _numbers(_protocol_hypotheses())  # e.g. u15, H3
    bad = _untraceable(texts, allowed) + _untraceable_integers(texts, allowed)
    if bad:
        errors.append(f"numbers not found in the source artifacts: {sorted(set(bad))}")

    # Engine capability: null/false are always allowed; true must be consistent with the schema.
    ecap = h["engine_capability_assessment"] if isinstance(h["engine_capability_assessment"], dict) else {}
    if ecap.get("known_executable") not in (True, False, None) or not str(ecap.get("reason", "")).strip():
        errors.append("engine_capability_assessment needs known_executable true/false/null and a reason")
    elif ecap.get("known_executable") is True:
        usable = {*contract["exposure"], *contract["outcomes"], *contract["covariates"],
                  "commute_weekday_min", "weight", "stratum", "cluster"}
        beyond = sorted(set(variables) - usable)
        if beyond or NON_LINEAR_METHODS.search(" ".join([claim, str(ecap.get("reason", ""))])):
            errors.append(f"known_executable=true contradicts the engine contract (variables outside the "
                          f"schema: {beyond}, or a method the schema does not include); use null or false")
        elif GROUP_COMPARISON.search(" ".join([question, claim])):
            errors.append("known_executable=true overstates the engine: a between-group difference needs a formal "
                          "comparison the schema does not include (separate subgroup runs are descriptive); "
                          "use null or false")
    return errors, sources


def validate_hypothesis(hypothesis: dict) -> str:
    """Dry run: every validation error for one hypothesis, without saving."""
    errors, _ = _check(hypothesis)
    duplicate = _duplicate_of(hypothesis)
    if duplicate:
        errors.append(f"semantic duplicate of {duplicate}")
    return _ok(valid=not errors, errors=errors)


def _duplicate_of(h: dict) -> str | None:
    text = _words(f"{h.get('scientific_question', '')} {h.get('falsifiable_claim', '')}")
    for other in _saved():
        other_text = _words(f"{other['scientific_question']} {other['falsifiable_claim']}")
        if text and other_text and len(text & other_text) / len(text | other_text) >= 0.6:
            return other["hypothesis_id"]
    return None


def save_hypothesis(hypothesis: dict) -> str:
    """Validate and store one hypothesis as HYP-NNN (IDs assigned here, sequential); never overwrites."""
    errors, sources = _check(hypothesis)
    duplicate = _duplicate_of(hypothesis)
    if duplicate:
        errors.append(f"semantic duplicate of {duplicate}")
    for cid in hypothesis.get("source_critique_ids") or []:
        if len(_saved(cid)) >= MAX_PER_CRITIQUE:
            errors.append(f"{cid} already has {MAX_PER_CRITIQUE} hypotheses")
    if errors:
        return _err("hypothesis rejected", errors=errors)

    HYPOTHESIS_DIR.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.stem.split("-")[1]) for p in HYPOTHESIS_DIR.rglob("HYP-*.json")]  # incl. superseded/
    hypothesis_id = f"HYP-{max(numbers, default=0) + 1:03d}"
    experiments, critiques = sources["experiments"], sources["critiques"]
    dataset_versions = sorted({r["dataset_version"] for _, r, _ in experiments.values()})
    record = {
        "hypothesis_id": hypothesis_id,
        "source_experiment_ids": list(hypothesis["source_experiment_ids"]),
        "source_critique_ids": list(hypothesis["source_critique_ids"]),
        "scientific_question": hypothesis["scientific_question"],
        "falsifiable_claim": hypothesis["falsifiable_claim"],
        "motivation": {
            "observed_evidence": [{"kind": "OBSERVED_EVIDENCE", "statement": o["statement"], "source": o["source"]}
                                  for o in hypothesis["motivation"]["observed_evidence"]],
            "scientific_inference": [{"kind": "INFERENCE", "statement": s}
                                     for s in hypothesis["motivation"]["scientific_inference"]],
            "unresolved_uncertainty": hypothesis["motivation"]["unresolved_uncertainty"],
        },
        "required_variables": hypothesis["required_variables"],
        "expected_direction": hypothesis["expected_direction"],
        "supporting_observation": hypothesis["supporting_observation"],
        "contradicting_observation": hypothesis["contradicting_observation"],
        "current_evidence_status": "UNTESTED",
        "kind": "NEW_HYPOTHESIS",
        "engine_capability_assessment": {
            "known_executable": hypothesis["engine_capability_assessment"]["known_executable"],
            "reason": hypothesis["engine_capability_assessment"]["reason"],
            "assessed_by": "hypothesis_agent (provisional; the Experiment Planner decides feasibility)",
        },
        "limitations": hypothesis["limitations"],
        "review_status": "REQUIRES_HUMAN_REVIEW",
        "provenance": {
            "dataset_version": dataset_versions[0] if len(dataset_versions) == 1 else dataset_versions,
            "agent": "hypothesis_agent",
            "model": _declared_executor()["model"],
            "harness": _declared_executor()["harness"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "code_version": _code_version(),
            "source_artifacts": [
                *[_experiment_provenance(p) for p, _, _ in experiments.values()],
                *[{"path": _rel(p), "sha256": _sha256(p)} for p, _ in critiques.values()],
                {"path": _rel(MANIFEST), "sha256": _sha256(MANIFEST)},
                {"path": _rel(SCHEMA), "sha256": _sha256(SCHEMA)},
            ],
            "validation": "contract, approved variables, observational language, numbers traceable to sources",
        },
    }
    path = HYPOTHESIS_DIR / f"{hypothesis_id}.json"
    with path.open("x", encoding="utf-8", newline="\n") as f:  # "x": never overwrite
        f.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return _ok(hypothesis_id=hypothesis_id, artifact=_rel(path))
