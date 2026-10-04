"""Local tools for the Scientific Critic on a committed ExperimentResult (agents/scientific_critic.yaml).

Standard library only: no Supabase, embeddings or PDF parsing. The critic reads the published engine
artifacts under reports/experiments/<id>/ (never writes there) and stores its ScientificCritique as
reports/discovery/local/critiques/<critique_id>.json. Numbers only come from the engine artifact:
save_scientific_critique rejects decimal numbers that do not appear in it.

Experiments produced by the discovery loop carry experiments/<id>/provenance.json (decision, approval,
proposal, hypotheses, source experiment). For them the critic view adds the verified lineage and the
status each tested hypothesis had before this experiment, and the critique must add a structured
hypothesis assessment, point-estimate observations kept apart from formal inference, and a scientific
update. Interpretation rules (interval including zero, heterogeneity, ranking, interventions, next
experiments) are enforced deterministically before saving.
"""

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from commute_lab.experiment_views import _compact

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "experiments"
SPEC_DIR = ROOT / "experiments"
PROTOCOL = ROOT / "docs" / "EXPERIMENT_PROTOCOL.md"
CRITIQUE_DIR = ROOT / "reports" / "discovery" / "local" / "critiques"
CRITIC_SPEC = ROOT / "agents" / "scientific_critic.yaml"
CRITIC_CODE = ("agents/commute_lab/critic_tools.py", "agents/commute_lab/experiment_views.py",
               "agents/scientific_critic.yaml")

STATUSES = ("VALID", "UNCERTAIN", "REQUIRES_REVISION", "REQUIRES_HUMAN_REVIEW")  # EXPERIMENT_PROTOCOL.md
EVIDENCE_KINDS = ("OBSERVED_EVIDENCE", "INFERENCE")
# Hypothesis status as recorded by the engine's assessment groups; UNTESTED when no experiment assessed it.
ENGINE_HYPOTHESIS_STATUS = {"supported_hypotheses": "SUPPORTED", "unsupported_hypotheses": "NOT_SUPPORTED",
                            "inconclusive_hypotheses": "INCONCLUSIVE"}
UNTESTED = "UNTESTED"
UPDATE_FIELDS = ("what_was_known_before", "what_was_tested", "what_changed", "what_remains_unresolved")
# Causal or definitive-ranking wording is not allowed in evidence statements (AGENTS.md §2).
CAUSAL = re.compile(r"\b(causes?|caused|causing|leads? to|results? in|reduces?|reduced|sacrific\w*|"
                    r"definitively|the most sacrificed|effect of commut\w*)\b", re.IGNORECASE)
DECIMAL = re.compile(r"[-−]?\d+\.\d+")
# Broader causal verbs, checked sentence by sentence in every assertive text (questions included).
CAUSAL_WIDE = re.compile(CAUSAL.pattern[:-3] + r"|affect(s|ed|ing)?|impact(s|ed|ing)?|influenc\w*)\b", re.IGNORECASE)
COMMUTING = re.compile(r"\bcommut\w*", re.IGNORECASE)
FULL_SENTENCE = re.compile(r"(?<=[.!?])\s+")
# Plain-language names of moderator levels, so "men" names the male reference group.
LEVEL_WORDS = {"male": ("men", "man", "males"), "female": ("women", "woman", "females")}
# "reduced uncertainty about X" describes learning, not a causal claim about commuting.
UNCERTAINTY_REDUCTION = re.compile(r"\breduc\w*[^.;]{0,40}\buncertaint\w*", re.IGNORECASE)
NEGATION = re.compile(r"\b(not|no|nor|cannot|can't|neither|without|never)\b", re.IGNORECASE)
# Saying an interval is compatible with little or no difference (or cannot exclude it) is not claiming none.
NO_DIFFERENCE_OK = re.compile(r"\bcompatible with\b|\bcannot (rule out|exclude)\b|\bnot (establish|show|demonstrate|"
                              r"imply|mean)\b|\bnot (as |taken as )?(evidence|proof)\b", re.IGNORECASE)
# Statements about power or what a test could detect are hedged, not claims of a detected difference.
HEDGE = re.compile(r"\b(power|could|may|might|would|whether|if)\b", re.IGNORECASE)
POINT_QUALIFIER = re.compile(r"\bpoint[- ]estimates?\b|\bpoint level\b|\bdescriptiv\w*", re.IGNORECASE)
GROUP = re.compile(r"\b(women|woman|female|females|men|man|male|males|sex|sexes)\b", re.IGNORECASE)
GROUP_COMPARATIVE = re.compile(r"\b(more|less) negative\b|\b(stronger|weaker|steeper|flatter|larger|smaller)\b",
                               re.IGNORECASE)
HETEROGENEITY_CLAIM = re.compile(
    r"\b(establish\w*|confirm\w*|demonstrat\w*|prov(?:e|es|ed|en)|reveal\w*|detect\w*)\b[^.;]{0,50}"
    r"\b(difference|heterogeneity|moderation|gap)\b|\b(difference|heterogeneity|moderation)\b[^.;]{0,30}"
    r"\b(is|was|has been) (established|confirmed|demonstrated|detected|found)\b", re.IGNORECASE)
SIGNIFICANCE = re.compile(r"\bsignifican\w*|\bp[- ]?values?\b|\bp\s*[<=]", re.IGNORECASE)
INTERVENTION = re.compile(
    r"\brecommend\w*|\bshould (reduce|shorten|cut|limit|implement|adopt|prioriti[sz]e|invest|target)\b|"
    r"\bpolic(y|ies) (should|makers?|recommendations?)\b|\binterventions? (should|to reduce|that reduce|targeting)\b|"
    r"\b(employers|governments?|planners|authorities) should\b", re.IGNORECASE)
NEXT_EXPERIMENT = re.compile(
    r"\b(next|follow[- ]up|subsequent|future|new) (experiment|study|analysis|model|test)s? (should|will|would|could|to)\b|"
    r"\b(we|i) (propose|suggest|plan)\b|\bshould (next )?(be )?(run|tested|conducted|executed|prioriti[sz]ed)\b|"
    r"\bselect\w* (the )?next\b|\bEXP-\d{3,}\b[^.;]{0,20}\b(should|will) (test|run)\b", re.IGNORECASE)
LINEAGE_IDS = re.compile(r"\b(?:EXP|PROP|HYP|CRIT|REV|DEC|CAND)-[A-Z0-9]*\d[\w-]*", re.IGNORECASE)


def _ok(**data: Any) -> str:
    return json.dumps({"ok": True, **data}, ensure_ascii=False, default=str)


def _err(message: str, **data: Any) -> str:
    return json.dumps({"ok": False, "error": message, **data}, ensure_ascii=False, default=str)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def _exp_number(experiment_id: str) -> int:
    return int(experiment_id.split("-")[1])


def _source(experiment_id: str) -> tuple[Path, dict, dict]:
    """Published result + spec of an experiment, after checking result bytes against validation.json."""
    if not re.fullmatch(r"EXP-\d{3,}", experiment_id):
        raise ValueError("experiment_id must look like EXP-001")
    out = REPORT_DIR / experiment_id
    result_path = out / "result.json"
    recorded = json.loads((out / "validation.json").read_text(encoding="utf-8"))
    if recorded.get("status") != "PASS" or recorded.get("result_sha256") != _sha256(result_path):
        raise ValueError(f"{result_path.relative_to(ROOT).as_posix()} does not match its validation.json")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    spec = json.loads((out / "spec.json").read_text(encoding="utf-8"))
    return result_path, result, spec


def _protocol_hypotheses() -> list[dict]:
    """Pre-registered H1-H4 from docs/EXPERIMENT_PROTOCOL.md (heading + statement)."""
    text = PROTOCOL.read_text(encoding="utf-8")
    found = re.findall(r"^### (H\d) — (.+?)\n\n(.+?)(?=\n### |\n---)", text, re.MULTILINE | re.DOTALL)
    return [{"id": h, "name": name.strip(), "statement": " ".join(body.split())} for h, name, body in found]


def _numbers(value: Any) -> set[float]:
    """Every number in a JSON value, including numbers written inside strings."""
    if isinstance(value, bool):
        return set()
    if isinstance(value, (int, float)):
        return {float(value)}
    if isinstance(value, str):
        return {float(t.replace("−", "-")) for t in re.findall(r"[-−]?\d+(?:\.\d+)?", value)}
    if isinstance(value, dict):
        return set().union(*(_numbers(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(_numbers(v) for v in value)) if value else set()
    return set()


def _untraceable(texts: list[str], allowed: set[float], signed: bool = False) -> list[str]:
    """Decimal numbers in the critique that match no artifact value (rounded to the digits written).

    With signed=True the sign must match too, so an estimate cannot be quoted with its sign flipped.
    """
    bad = []
    for text in texts:
        for token in DECIMAL.findall(text):
            number = float(token.replace("−", "-"))
            tolerance = 0.5 * 10 ** -len(token.split(".")[1])
            if signed:
                ok = any(abs(number - x) <= tolerance + 1e-12 for x in allowed)
            else:
                ok = any(abs(abs(number) - abs(x)) <= tolerance + 1e-12 for x in allowed)
            if not ok:
                bad.append(token)
    return bad


def _declared_executor() -> dict:
    """harness/model declared in the critic spec (read as text: no YAML dependency)."""
    text = CRITIC_SPEC.read_text(encoding="utf-8") if CRITIC_SPEC.exists() else ""
    return {key: (m.group(1) if (m := re.search(rf"^\s+{key}:\s*(\S+)", text, re.MULTILINE)) else None)
            for key in ("harness", "model")}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def _code_version() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _engine_status(result: dict, hypothesis_id: str) -> str | None:
    for group, status in ENGINE_HYPOTHESIS_STATUS.items():
        if any(h.get("id") == hypothesis_id for h in result.get(group, [])):
            return status
    return None


# --- Lineage and prior scientific state ------------------------------------------------------------

def _lineage(experiment_id: str, result_path: Path, spec: dict) -> dict | None:
    """Verified discovery lineage from experiments/<id>/provenance.json; None when the file is absent.

    Raises ValueError when any recorded hash, ID or code version does not validate: the critic must stop.
    """
    path = SPEC_DIR / experiment_id / "provenance.json"
    if not path.exists():
        return None
    prov = _load(path)
    problems = []
    if prov.get("experiment_id") != experiment_id:
        problems.append(f"provenance experiment_id {prov.get('experiment_id')!r} != {experiment_id}")
    spec_path = ROOT / prov.get("spec", "")
    if not spec_path.is_file() or _sha256(spec_path) != prov.get("spec_sha256"):
        problems.append("spec bytes differ from provenance spec_sha256")
    elif _load(spec_path) != spec:
        problems.append("experiments spec differs from the published reports spec")
    for name, artifact in sorted(prov.get("source_artifacts", {}).items()):
        source = ROOT / artifact["path"]
        if not source.is_file() or _sha256(source) != artifact["sha256"]:
            problems.append(f"source artifact {name} ({artifact['path']}) changed or is missing")
    execution = prov.get("execution") or {}
    if execution.get("result_sha256") != _sha256(result_path):
        problems.append("result.json bytes differ from provenance execution.result_sha256")
    code = prov.get("code_version") or ""
    if not re.fullmatch(r"[0-9a-f]{40}", code) or _git("cat-file", "-e", f"{code}^{{commit}}").returncode != 0:
        problems.append(f"code_version {code!r} is not a commit in this repository")
    elif _git("merge-base", "--is-ancestor", code, "HEAD").returncode != 0:
        problems.append(f"code_version {code} is not an ancestor of HEAD")
    if problems:
        raise ValueError("experiment provenance does not validate: " + "; ".join(problems))

    sources = {name: _load(ROOT / a["path"]) for name, a in prov["source_artifacts"].items()
               if a["path"].endswith(".json") and name in ("decision", "decision_approval", "proposal", "hypothesis",
                                                            "hypothesis_approval", "critique")}
    hypothesis, proposal = sources.get("hypothesis", {}), sources.get("proposal", {})
    decision, approval = sources.get("decision", {}), sources.get("decision_approval", {})
    critique, hyp_review = sources.get("critique", {}), sources.get("hypothesis_approval", {})
    ids = {"decision_id": prov.get("decision_id"), "decision_approval_id": prov.get("decision_approval_id"),
           "proposal_id": prov.get("proposal_id"), "hypothesis_ids": prov.get("hypothesis_ids"),
           "hypothesis_approval_id": hyp_review.get("review_id"),
           "source_experiment_id": prov.get("source_experiment_id"),
           "source_critique_id": critique.get("critique_id")}
    return {
        "provenance_artifact": path.relative_to(ROOT).as_posix(), "provenance_sha256": _sha256(path),
        "verified": True, "code_version": code, **ids,
        "artifacts": {name: {"path": a["path"], "sha256": a["sha256"]} for name, a in prov["source_artifacts"].items()},
        "hypothesis": {k: hypothesis.get(k) for k in ("hypothesis_id", "scientific_question", "falsifiable_claim",
                                                       "expected_direction", "current_evidence_status")},
        "proposal": {k: proposal.get(k) for k in ("proposal_id", "scientific_question", "analysis_role")},
        "decision": {k: decision.get(k) for k in ("decision_id", "decision_status", "preferred_proposal_id")},
        "decision_approval": {k: approval.get(k) for k in ("review_id", "decision", "constraints", "not_endorsed")},
        "source_critique": {k: critique.get(k) for k in ("critique_id", "experiment_id", "scientific_status")},
        "interpretation_constraints": prov.get("interpretation_constraints"),
        "interpretation_coding": prov.get("interpretation_coding"),
    }


def _prior_state(experiment_id: str, spec: dict) -> dict:
    """Earlier committed experiments (no numbers) and the status each tested hypothesis had before this one."""
    prior = []
    for out in sorted(REPORT_DIR.glob("EXP-*"), key=lambda p: p.name):
        if not (out.is_dir() and re.fullmatch(r"EXP-\d{3,}", out.name)) or _exp_number(out.name) >= _exp_number(experiment_id):
            continue
        _, result, prior_spec = _source(out.name)  # an unvalidated earlier result stops the critic too
        prior.append((out.name, result, prior_spec))
    statuses = {}
    for hid in spec.get("hypothesis_ids", []):
        statuses[hid] = {"previous_status": UNTESTED, "assessed_in": None}
        for eid, result, _ in prior:
            if (status := _engine_status(result, hid)) is not None:
                statuses[hid] = {"previous_status": status, "assessed_in": eid}
    experiments = [{
        "experiment_id": eid, "outcomes": s.get("outcomes"), "hypothesis_ids": s.get("hypothesis_ids"),
        "ranking_status": r["ranking"]["status"],
        "point_estimate_order": [x["outcome"] for x in r["ranking"].get("point_estimate_order", [])],
        "hypotheses_evaluated": {h["id"]: status for group, status in ENGINE_HYPOTHESIS_STATUS.items()
                                 for h in r.get(group, [])},
        "critiques": [{"critique_id": c["critique_id"], "scientific_status": c.get("scientific_status")}
                      for c in (_load(p) for p in sorted(CRITIQUE_DIR.glob(f"CRIT-{eid}-*.json")))],
    } for eid, r, s in prior]
    return {"experiments": experiments, "hypothesis_status_before": statuses}


def _expected_assessments(result: dict, spec: dict, lineage: dict | None, prior: dict) -> dict[str, dict]:
    """hypothesis_id -> required previous/new status (agent hypotheses map to the protocol hypothesis tested)."""
    protocol = list(spec.get("hypothesis_ids", []))
    expected = {}
    for hid in protocol:
        expected[hid] = {"protocol_hypothesis_id": hid,
                         "previous_status": prior["hypothesis_status_before"][hid]["previous_status"],
                         "new_status": _engine_status(result, hid) or UNTESTED}
    agent = (lineage or {}).get("hypothesis_ids", {}).get("agent", []) if lineage else []
    if agent and len(protocol) == 1:
        return {aid: {**expected[protocol[0]]} for aid in agent}
    return expected


def read_experiment_artifact(experiment_id: str = "EXP-001") -> str:
    """Critic-ready view of a committed ExperimentResult plus the pre-registered hypotheses H1-H4."""
    try:
        result_path, result, spec = _source(experiment_id)
        lineage = _lineage(experiment_id, result_path, spec)
        prior = _prior_state(experiment_id, spec) if lineage else None
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    evaluated = {h["id"] for group in ("supported_hypotheses", "unsupported_hypotheses", "inconclusive_hypotheses")
                 for h in result.get(group, [])}
    view = dict(source_artifact=result_path.relative_to(ROOT).as_posix(), source_sha256=_sha256(result_path),
                dataset_version=result["dataset_version"],
                dataset_sha256=result["provenance"]["dataset_sha256"],
                result=_compact(result, spec),
                protocol_hypotheses=_protocol_hypotheses(),
                hypotheses_evaluated_by_engine=sorted(evaluated),
                note=("engine_candidate_next_experiments are unselected alternatives recorded by the engine; "
                      "the critic lists open questions but does not propose or choose the next experiment."))
    if lineage:
        view.update(lineage=lineage, prior_scientific_state=prior,
                    required_hypothesis_assessments=_expected_assessments(result, spec, lineage, prior),
                    critique_contract=(
                        "Also pass hypothesis_assessments (one per required hypothesis, statuses exactly as "
                        "required_hypothesis_assessments), point_estimate_observations, formal_inference and "
                        "scientific_update {" + ", ".join(UPDATE_FIELDS) + "}. Numbers only from result."))
    return _ok(**view)


# --- Interpretation rules ---------------------------------------------------------------------------

def _sentences(texts: list[str]) -> list[str]:
    from commute_lab.director_tools import SENTENCE  # deferred: director_tools imports this module
    return [s for t in texts for s in SENTENCE.split(t) if s.strip()]


def _interpretation_errors(assertive: list[str], result: dict, tested: list[str]) -> list[str]:
    """Rules for every text except unsupported_claims (which lists what must NOT be claimed)."""
    from commute_lab.director_tools import INCLUDES_ZERO, INCONCLUSIVE, NEGATED, NO_DIFFERENCE, RANKING_RESOLUTION

    inconclusive = any(r.get("interpretation_status") == "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO"
                       for r in result.get("interactions") or [])
    untested = (re.compile(r"\b(" + "|".join(map(re.escape, tested)) + r")\b[^.;]{0,60}\b(not (?:been |yet )?"
                           r"(?:evaluated|tested|assessed)|untested|unevaluated)\b", re.IGNORECASE) if tested else None)
    errors = []
    slope_labels = _slope_labels(result)
    # Clauses (split also at ';') for local claims; the full sentence (split at . ! ?) for qualifiers.
    full = {}
    for sentence in (p for t in assertive for p in FULL_SENTENCE.split(t) if p.strip()):
        for clause in _sentences([sentence]):
            full.setdefault(clause, sentence)
    for s in full:
        negated = bool(NEGATION.search(s) or NEGATED.search(s))
        claim = NO_DIFFERENCE.search(s)
        # "no equivalence margin" / "equivalence was not assessed" deny equivalence rather than claim it.
        denied_equivalence = bool(claim) and claim.group(0).lower().startswith("equivalen") and negated
        if claim and not (NEGATED.search(s) or NO_DIFFERENCE_OK.search(s) or denied_equivalence):
            errors.append(f"claims no difference / equality ({NO_DIFFERENCE.search(s).group(0)!r}); an interval "
                          f"including zero is inconclusive, not evidence of no difference: {s!r}")
        if INCLUDES_ZERO.search(s) and not (INCONCLUSIVE.search(full[s]) or negated):
            errors.append(f"a sentence saying the interval includes zero must also call it inconclusive (e.g. "
                          f"'The interval includes zero, so the interaction is inconclusive.'): {full[s]!r}")
        if inconclusive and HETEROGENEITY_CLAIM.search(s) and not (negated or HEDGE.search(s)):
            errors.append(f"claims an established difference while the interaction is inconclusive: {s!r}")
        if GROUP.search(s) and GROUP_COMPARATIVE.search(s) and not (POINT_QUALIFIER.search(s) or negated):
            errors.append(f"group-slope comparisons are point-estimate observations; say so in the sentence: {s!r}")
        if untested and untested.search(s) and not re.search(r"\b(before|prior|previously|until|had|from)\b", s, re.I):
            errors.append(f"says a hypothesis this experiment tested was not evaluated: {s!r}")
        if RANKING_RESOLUTION.search(s) and not negated:
            errors.append(f"this experiment does not resolve a cross-outcome ranking: {s!r}")
        if SIGNIFICANCE.search(s):
            errors.append(f"no significance testing or p-values: the engine reports intervals: {s!r}")
        if INTERVENTION.search(s):
            errors.append(f"no intervention or policy recommendations from observational evidence: {s!r}")
        if NEXT_EXPERIMENT.search(s):
            errors.append(f"the critic does not propose or select the next experiment: {s!r}")
        # Causal claims about commuting (statistical "influence" of observations on estimates is fine).
        if CAUSAL_WIDE.search(UNCERTAINTY_REDUCTION.sub(" ", s)) and COMMUTING.search(s) and not negated:
            errors.append(f"causal wording about commuting ({CAUSAL_WIDE.search(s).group(0)!r}); use association "
                          f"language, also in questions (e.g. 'Is commuting associated with ...?'): {s!r}")
        for estimate, labels, role in slope_labels:
            quoted = any(abs(float(t.replace("−", "-")) - estimate) <= 0.5 * 10 ** -len(t.split(".")[1]) + 1e-12
                         for t in DECIMAL.findall(s))
            if quoted and not labels.search(s):
                errors.append(f"{estimate:.3f} is the {role}-group slope, not a pooled association: name the "
                              f"group in the same sentence: {s!r}")
    return errors


def _slope_labels(result: dict) -> list[tuple[float, re.Pattern, str]]:
    """(group slope, words naming that group, role) for each primary interaction."""
    out = []
    for r in result.get("interactions") or []:
        if r["variant"] != "adjusted":
            continue
        for role, key, level in (("reference", "reference_group_slope", r["reference_level"]),
                                 ("comparison", "comparison_group_slope", r["comparison_level"])):
            words = [role, str(level), *LEVEL_WORDS.get(str(level), ())]
            out.append((round(r[key]["estimate"], 3),
                        re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b", re.IGNORECASE), role))
    return out


def _structured_errors(result: dict, spec: dict, lineage: dict, prior: dict, assessments: list[dict],
                       point: list[str], formal: list[str], update: dict, texts_by_field: dict) -> list[str]:
    errors = []
    expected = _expected_assessments(result, spec, lineage, prior)
    given = {a.get("hypothesis_id"): a for a in assessments if isinstance(a, dict)}
    if set(given) != set(expected):
        errors.append(f"hypothesis_assessments must cover exactly {sorted(expected)} (got {sorted(given)})")
    for hid, want in expected.items():
        a = given.get(hid)
        if not a:
            continue
        for key in ("previous_status", "new_status"):
            if a.get(key) != want[key]:
                errors.append(f"{hid} {key} must be {want[key]} (engine assessment), not {a.get(key)!r}")
        if not str(a.get("reason", "")).strip():
            errors.append(f"{hid} needs a reason")
    if not isinstance(update, dict) or any(not str(update.get(k, "")).strip() for k in UPDATE_FIELDS):
        errors.append(f"scientific_update needs non-empty {list(UPDATE_FIELDS)}")
    else:
        change = f"{update['what_was_known_before']} {update['what_changed']}"
        for want in expected.values():
            for status in {want["previous_status"], want["new_status"]}:
                if status.lower() not in change.lower():
                    errors.append(f"scientific_update must state the status change ({status} missing)")
    interactions = [r for r in result.get("interactions") or [] if r["variant"] == "adjusted"]
    if interactions:
        if not point or not formal:
            errors.append("point_estimate_observations and formal_inference must both be non-empty")
        joined_point = " ".join(point).replace("−", "-")
        joined_formal = " ".join(formal).replace("−", "-")
        for r in interactions:
            slopes = [f"{r['reference_group_slope']['estimate']:.3f}", f"{r['comparison_group_slope']['estimate']:.3f}"]
            if not all(x in joined_point for x in slopes):
                errors.append(f"point_estimate_observations must quote both group slopes {slopes} from the artifact")
            i = r["interaction"]
            needed = [f"{i['estimate']:.3f}", f"{i['interval']['lower']:.3f}", f"{i['interval']['upper']:.3f}",
                      r["interpretation_status"]]
            missing = [x for x in needed if x not in joined_formal]
            if missing:
                errors.append(f"formal_inference must quote the interaction, its 95% interval and status: missing {missing}")
        everything = " ".join(t for ts in texts_by_field.values() for t in ts)
        if any(r["interpretation_status"] == "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO" for r in interactions) and \
                not re.search(r"equivalen\w*", " ".join(texts_by_field["limitations"] + texts_by_field["uncertainties"]), re.I):
            errors.append("limitations/uncertainties must say an interval including zero does not establish equivalence")
        if not re.search(r"\bCR1\b", " ".join(texts_by_field["limitations"])):
            errors.append("limitations must state that CR1 is an approximation, not full ENUT complex-survey variance")
        if not re.search(r"observational|cross-sectional", " ".join(texts_by_field["limitations"]), re.I):
            errors.append("limitations must state the observational, cross-sectional design")
        # Method facts every moderated result carries; leverage and power only when they apply.
        caveats = " ".join(texts_by_field["limitations"] + texts_by_field["uncertainties"])
        required = [(r"FAC_PER", "the FAC_PER-weighted estimation"), (r"\blinear", "the linear commute specification")]
        if "HIGH_LEVERAGE_RETAINED" in result.get("quality_flags", []):
            required.append((r"leverage|influen", "that high-influence observations were retained"))
        if any(r["interpretation_status"] == "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO" for r in interactions):
            required.append((r"\bpower\b", "possibly limited power to detect an interaction"))
        for pattern, what in required:
            if not re.search(pattern, caveats, re.IGNORECASE):
                errors.append(f"limitations/uncertainties must mention {what}")
        source = lineage.get("source_experiment_id")
        prior_ranking = next((e["ranking_status"] for e in prior["experiments"] if e["experiment_id"] == source), None)
        if prior_ranking and prior_ranking not in everything:
            errors.append(f"preserve the source experiment's ranking status: {source} {prior_ranking} is not mentioned")
    if not texts_by_field["unsupported_claims"]:
        errors.append("unsupported_claims must list the interpretations this evidence does not support")
    return errors


def save_scientific_critique(experiment_id: str, scientific_status: str, status_rationale: str,
                             evidence_summary: list[dict], uncertainties: list[str], limitations: list[str],
                             unsupported_claims: list[str], untested_questions: list[str],
                             hypothesis_assessments: list[dict] | dict | None = None,
                             point_estimate_observations: list[str] | None = None,
                             formal_inference: list[str] | None = None,
                             scientific_update: dict | None = None) -> str:
    """Validate and store a ScientificCritique of a committed experiment; never overwrites."""
    try:
        result_path, result, spec = _source(experiment_id)
        lineage = _lineage(experiment_id, result_path, spec)
        prior = _prior_state(experiment_id, spec) if lineage else None
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    if scientific_status not in STATUSES:
        return _err(f"scientific_status must be one of {STATUSES}")
    for name, items in (("uncertainties", uncertainties), ("limitations", limitations),
                        ("untested_questions", untested_questions)):
        if not items or not all(isinstance(s, str) and s.strip() for s in items):
            return _err(f"{name} must be a non-empty list of strings")
    if not isinstance(unsupported_claims, list) or not all(isinstance(s, str) for s in unsupported_claims):
        return _err("unsupported_claims must be a list of strings (empty if none)")
    if not evidence_summary or not all(isinstance(e, dict) and e.get("kind") in EVIDENCE_KINDS
                                       and str(e.get("statement", "")).strip() for e in evidence_summary):
        return _err(f"evidence_summary items need a statement and kind in {EVIDENCE_KINDS}")
    if not any(e["kind"] == "OBSERVED_EVIDENCE" for e in evidence_summary):
        return _err("evidence_summary needs at least one OBSERVED_EVIDENCE item")
    if isinstance(hypothesis_assessments, dict):
        hypothesis_assessments = [hypothesis_assessments]
    hypothesis_assessments = hypothesis_assessments or []
    point = [str(s) for s in point_estimate_observations or []]
    formal = [str(s) for s in formal_inference or []]
    update = scientific_update if isinstance(scientific_update, dict) else {}
    structured = bool(lineage or result.get("interactions"))

    statements = [str(e["statement"]) for e in evidence_summary]
    reasons = [str(a.get("reason", "")) for a in hypothesis_assessments if isinstance(a, dict)]
    update_texts = [str(update.get(k, "")) for k in UPDATE_FIELDS]
    causal_scope = statements + point + formal + reasons + ([status_rationale, *update_texts] if structured else [])
    causal = [s for s in causal_scope if CAUSAL.search(UNCERTAINTY_REDUCTION.sub(" ", s))]
    if causal:
        return _err("Causal or definitive-ranking wording in evidence_summary; use association language",
                    statements=causal)
    texts = [status_rationale, *statements, *uncertainties, *limitations, *unsupported_claims, *untested_questions,
             *point, *formal, *reasons, *update_texts]
    if lineage:
        # Only the lineage and earlier experiments may be named; anything else (EXP-003, PROP-008) is a proposal.
        known = {experiment_id, *(e["experiment_id"] for e in prior["experiments"]),
                 *(str(v) for k, v in lineage.items() if k.endswith("_id") and v),
                 *lineage["hypothesis_ids"].get("agent", []),
                 *(c["critique_id"] for e in prior["experiments"] for c in e["critiques"])}
        stripped = texts
        for ident in sorted(known, key=len, reverse=True):
            stripped = [t.replace(ident, " ") for t in stripped]
        other_ids = sorted({m for t in stripped for m in LINEAGE_IDS.findall(t)})
    else:
        other_ids = sorted({i for t in texts for i in re.findall(r"EXP-\d{3,}", t)} - {experiment_id})
    if other_ids:
        return _err("The critique must not propose or reference other experiments", experiment_ids=other_ids)
    # Only what read_experiment_artifact shows (not the covariance matrices), so a made-up
    # number cannot pass by matching one of thousands of unrelated values.
    bad = _untraceable(texts, _numbers(_compact(result, spec)) | _numbers(spec) | _numbers(_protocol_hypotheses()),
                       signed=structured)
    if bad:
        return _err("Numbers not found in the engine artifact (with their sign); quote its values, never compute new ones",
                    numbers=sorted(set(bad)))
    if structured:
        texts_by_field = {"limitations": limitations, "uncertainties": uncertainties,
                          "unsupported_claims": unsupported_claims, "other": texts}
        assertive = [status_rationale, *statements, *uncertainties, *limitations, *untested_questions,
                     *point, *formal, *reasons, *update_texts]
        tested = [h for a in _expected_assessments(result, spec, lineage, prior).items() for h in (a[0], a[1]["protocol_hypothesis_id"])] \
            if lineage else list(spec.get("hypothesis_ids", []))
        errors = _interpretation_errors(assertive, result, sorted(set(tested)))
        if lineage:
            errors += _structured_errors(result, spec, lineage, prior, hypothesis_assessments, point, formal,
                                         update, texts_by_field)
        if errors:
            return _err("The critique misstates the evidence; fix each item and call again", problems=errors)

    CRITIQUE_DIR.mkdir(parents=True, exist_ok=True)
    # Retired critiques (critiques/superseded/) keep their IDs: numbering never reuses one.
    n = 1 + sum(1 for _ in CRITIQUE_DIR.rglob(f"CRIT-{experiment_id}-*.json"))
    critique_id = f"CRIT-{experiment_id}-{n:03d}"
    critique = {
        "critique_id": critique_id,
        "experiment_id": experiment_id,
        "scientific_status": scientific_status,
        "status_rationale": status_rationale,
        "evidence_summary": [{"kind": e["kind"], "statement": e["statement"], "source": e.get("source")}
                             for e in evidence_summary],
    }
    if lineage:
        expected = _expected_assessments(result, spec, lineage, prior)
        critique["hypothesis_assessments"] = [
            {"hypothesis_id": a["hypothesis_id"], "protocol_hypothesis_id": expected[a["hypothesis_id"]]["protocol_hypothesis_id"],
             "previous_status": a["previous_status"], "new_status": a["new_status"], "reason": a["reason"],
             "status_source": "engine hypothesis assessment in result.json"} for a in hypothesis_assessments]
    if structured:
        critique["point_estimate_observations"] = point
        critique["formal_inference"] = formal
    critique.update({
        "uncertainties": uncertainties,
        "limitations": limitations,
        "unsupported_claims": unsupported_claims,
        "untested_questions": [{"kind": "UNTESTED_QUESTION", "question": q} for q in untested_questions],
    })
    if lineage:
        critique["scientific_update"] = {k: update[k] for k in UPDATE_FIELDS}
    critique["provenance"] = {
        "source_experiment_id": experiment_id,
        "source_artifact": result_path.relative_to(ROOT).as_posix(),
        "source_sha256": _sha256(result_path),
        "dataset_version": result["dataset_version"],
        "dataset_sha256": result["provenance"]["dataset_sha256"],
        "engine_review_status": result["review_status"],
        "engine_ranking_status": result["ranking"]["status"],
        "agent": "scientific_critic",
        "declared_executor": _declared_executor(),
        "code_version": _code_version(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "numbers_policy": "decimal numbers checked against the source artifact before saving",
    }
    if lineage:
        out = result_path.parent
        critique["provenance"].update({
            "source_spec_sha256": _sha256(out / "spec.json"),
            "source_validation_sha256": _sha256(out / "validation.json"),
            "experiment_provenance": lineage["provenance_artifact"],
            "experiment_provenance_sha256": lineage["provenance_sha256"],
            "experiment_code_version": lineage["code_version"],
            "lineage_verified": True,
            "lineage": {k: lineage[k] for k in ("decision_id", "decision_approval_id", "proposal_id", "hypothesis_ids",
                                                 "hypothesis_approval_id", "source_experiment_id", "source_critique_id")},
            "lineage_artifacts_sha256": {a["path"]: a["sha256"] for a in lineage["artifacts"].values()},
            "hypothesis_status_before": prior["hypothesis_status_before"],
            "engine_interaction_status": {r["model_id"]: r["interpretation_status"] for r in result.get("interactions") or []},
            "critic_code_sha256": {p: _sha256(ROOT / p) for p in CRITIC_CODE},
            "critic_code_committed": _git("diff", "--quiet", "HEAD", "--", *CRITIC_CODE).returncode == 0,
            "interpretation_rules": "interval-includes-zero, heterogeneity, ranking, intervention and next-experiment "
                                    "rules checked deterministically before saving",
        })
    path = CRITIQUE_DIR / f"{critique_id}.json"
    with path.open("x", encoding="utf-8", newline="\n") as f:  # "x": never overwrite
        f.write(json.dumps(critique, indent=2, ensure_ascii=False) + "\n")
    return _ok(critique_id=critique_id,
               artifact=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix())
