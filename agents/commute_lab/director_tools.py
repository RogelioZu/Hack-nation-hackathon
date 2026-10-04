"""Local tools for the Discovery Director (agents/discovery_director.yaml).

Standard library only. The Director reads persisted artifacts (Shared Research State, EXP-001, the
critique, human reviews, ExperimentProposal artifacts) and the engine's live capability audit, and
stores a DiscoveryDecision as reports/discovery/local/decisions/DEC-NNN.json (research-state kind
"decisions"). It decides; it never runs an experiment, writes a spec or assigns an experiment id.

Executability is recomputed on every call from the committed ExperimentSpec schema and method
registry (planner_tools.capability_audit), so rerunning the Director after an engine extension can
change the decision. Decisions are append-only: a rerun creates a new DEC-NNN, never an overwrite.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from commute_lab.critic_tools import _code_version, _numbers
from commute_lab.experiment_views import _compact
from commute_lab.hypothesis_tools import CAUSAL, _source, _untraceable, _untraceable_integers
from commute_lab.planner_tools import (
    EXPLORATORY_DISCLAIMER, LEVELS, MAIN_EFFECT, OVERCLAIM_RESULT, capability_audit,
)
from commute_lab.research_state import ROOT, build_state, save_artifact, sha256

DISCOVERY = ROOT / "reports" / "discovery" / "local"
PROPOSAL_DIR = DISCOVERY / "candidates"
REVIEW_DIR = DISCOVERY / "reviews"
HYPOTHESIS_DIR = DISCOVERY / "hypotheses"
CRITIQUE_DIR = DISCOVERY / "critiques"
DECISION_DIR = DISCOVERY / "decisions"
AGENT_SPEC = ROOT / "agents" / "discovery_director.yaml"
ENGINE_CAPABILITIES = ROOT / "metadata" / "experiment_engine_capabilities.json"

STATUSES = ("READY_TO_EXECUTE", "WAITING_FOR_ENGINE_CAPABILITY", "HUMAN_REVIEW_REQUIRED", "NO_VALID_NEXT_EXPERIMENT")
DECISION_FIELDS = ("candidate_proposal_ids", "preferred_proposal_id", "best_executable_proposal_id",
                   "decision_status", "scientific_rationale", "expected_learning", "alternatives",
                   "capability_check", "uncertainties", "human_constraints_respected", "next_action")
# Keys that would mean running or scheduling an experiment: the Director only decides.
FORBIDDEN_KEYS = {"experiment_id", "spec", "experiment_spec", "run_id", "run", "executed", "execution_result",
                  "result", "results"}

SIGNIFICANCE = re.compile(r"\bsignifican\w*|\bp[- ]?values?\b|\bp\s*[<=]|\bpower to (detect|find)\b|"
                          r"\blikely to (find|detect|show) (an? )?(effect|difference|association)", re.IGNORECASE)
EXECUTION_CLAIM = re.compile(r"\b(was|were|has been|have been|is being) (run|executed)\b|\b(i|we) (ran|executed)\b",
                             re.IGNORECASE)
# EXP-001's ranking is INCONCLUSIVE: sleep has the most negative POINT ESTIMATE, not the "strongest association"
# (AGENTS.md §7.5). "strongest negative point estimate" is the accepted wording; "point association" is not.
RANKING_OVERCLAIM = re.compile(r"\b(strongest|largest|biggest|most negative)\b[^.;]{0,40}?\bassociation|"
                               r"\bpoint associations?\b|\bmost (displaced|affected|sacrificed)\b", re.IGNORECASE)
# An interval that includes zero is INCONCLUSIVE: never evidence of no difference / no heterogeneity.
INCLUDES_ZERO = re.compile(r"\b(includ\w*|cross\w*|span\w*|contain\w*|overlap\w*)\b[^.;]{0,20}\bzero\b",
                           re.IGNORECASE)
INCONCLUSIVE = re.compile(r"\binconclusive\b|\bunresolved\b|\b(leav\w*|remain\w*|stay\w*)\b[^.;]{0,20}\bopen\b|"
                          r"\bundetermined\b|\bcannot (tell|distinguish|determine)\b", re.IGNORECASE)
NO_DIFFERENCE = re.compile(r"\bno (clear |evident |meaningful |real |apparent |obvious |sex |group )*(difference|"
                           r"heterogeneity|moderation|interaction|variation)s?\b|\b(does|do|did) not (differ|vary)\b|"
                           r"\bsame (association|slope|pattern)\b|\b(is|are|be|were|was) (the same|identical|equal)\b|"
                           r"\b(absence|lack) of (a |any )?(difference|"
                           r"heterogeneity|moderation)\b|\bevidence of no\b|\bhomogeneous\b|\bequivalen\w*\b",
                           re.IGNORECASE)
NEGATED = re.compile(r"\bnot (as |taken as |read as )?(evidence|proof) (of|for)\b|\b(does|do|would|should) not "
                     r"(show|mean|imply|establish|indicate|demonstrate)\b|\bcannot (show|establish|indicate)\b|"
                     r"\bnor\b", re.IGNORECASE)
# Alternatives are rejected on scientific grounds, never on convenience.
NON_SCIENTIFIC_REASON = re.compile(r"\b(complex\w*|complicat\w*|simpl(e|er|est|icity)|easier|harder|"
                                   r"not used elsewhere|used elsewhere|unfamiliar|less familiar|extra (work|effort)|"
                                   r"more work)\b", re.IGNORECASE)
SCIENTIFIC_CRITERIA = re.compile(r"\binformati\w*|\bdirect\w*|\bhypothes\w*|\b(un)?certain\w*|\bEXP-\d{3}|"
                                 r"\b(left|leaves|remain\w*) open\b|\brigo\w*|\bformal\w*|\bexplorator\w*|"
                                 r"\bfeasib\w*|\bexecutab\w*|\bengine\b|\binterval\w*|\b(primary|secondary)\b|"
                                 r"\bestablish\w*|\bevidence\b", re.IGNORECASE)
# One moderator test on one outcome cannot settle the ranking across outcomes, and no test "will" settle anything.
RANKING_RESOLUTION = re.compile(r"\b(resolv\w*|clarif\w*|settl\w*|determin\w*|establish\w*)\b[^.;]{0,40}\branking\b",
                                re.IGNORECASE)
CERTAINTY = re.compile(r"\bwill (resolve|establish|confirm|prove|determine|settle|show)\b|\bdefinitive\w*|"
                       r"\bconclusive(ly)?\b", re.IGNORECASE)
HUMAN_APPROVAL = re.compile(r"\b(human|approv\w*|review\w*)\b", re.IGNORECASE)
REGRESSION_TERMS = re.compile(r"\binteraction (term|coefficient|effect)s?\b", re.IGNORECASE)
IDS = re.compile(r"\b(EXP|PROP|HYP|CRIT|REV|DEC)-\d{3,}(?:-\d{3,})?\b")
SENTENCE = re.compile(r"(?<=[.;!?])\s+")


def _ok(**data: Any) -> str:
    return json.dumps({"ok": True, **data}, ensure_ascii=False, default=str)


def _err(message: str, **data: Any) -> str:
    return json.dumps({"ok": False, "error": message, **data}, ensure_ascii=False, default=str)


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --- Inputs ------------------------------------------------------------------------------------

def _proposals() -> dict[str, dict]:
    """Active proposals (withdrawn ones live in candidates/superseded/ and are not candidates)."""
    return {p["proposal_id"]: p for p in map(_load, sorted(PROPOSAL_DIR.glob("PROP-*.json")))}


def _reviews() -> dict[str, dict]:
    return {r["review_id"]: r for r in map(_load, sorted(REVIEW_DIR.glob("REV-*.json")))}


def _approvals(reviews: dict[str, dict]) -> dict[str, dict]:
    """hypothesis_id -> approving review, only if the hypothesis bytes still match the reviewed bytes."""
    approved = {}
    for review in reviews.values():
        recorded = {a["path"]: a["sha256"] for a in review.get("reviewed_artifacts", [])}
        for item in review.get("approved_hypotheses", []):
            path = HYPOTHESIS_DIR / f"{item['hypothesis_id']}.json"
            intact = path.exists() and recorded.get(_rel(path)) == sha256(path)
            approved[item["hypothesis_id"]] = {"review_id": review["review_id"], "intact": intact,
                                               "decision": review.get("decision")}
    return approved


def _engine_capabilities() -> dict:
    """The engine's own capability export (kept equal to src/experiments/capabilities.py by the engine
    validator); {} for an engine that predates it, which then relies on the schema audit alone."""
    return _load(ENGINE_CAPABILITIES) if ENGINE_CAPABILITIES.exists() else {}


def _moderators(proposal: dict, engine: dict) -> list[str]:
    """Binary moderators named in the proposal's estimand or test (e.g. sex, has_child_u15)."""
    if "interaction_terms" not in proposal.get("required_engine_capabilities", []):
        return []
    names = (engine.get("interaction") or {}).get("binary_moderators") or {}
    text = " ".join(str(proposal.get(k) or "") for k in ("comparison_or_estimand", "experimental_test"))
    return sorted(m for m in names if re.search(rf"(?<![a-z0-9_]){re.escape(m)}(?![a-z0-9]|_u)", text))


def _executability(proposal: dict, audit: dict) -> dict:
    """Can the engine run this proposal today? Recomputed from the live schema audit and the engine's
    capability export. Planner capability names map onto what the engine declares it supports."""
    supported, values = audit["supported"], audit["spec_values"]
    engine = _engine_capabilities()
    declared = engine.get("supported") or {}
    interaction = engine.get("interaction") or {}
    moderators = _moderators(proposal, engine)
    interactions_ok = bool(supported.get("interaction_terms")) and \
        bool(declared.get("exposure_x_binary_moderator_interaction", True))
    covariates = set(proposal.get("covariates", []))
    # A binary moderator's main effect enters through the interaction itself (engine contract), so it
    # does not need to be a schema covariate.
    outside = covariates - set(values["covariates"]) - (set(moderators) if interactions_ok else set())
    available = {
        "interaction_terms": interactions_ok and (bool(moderators) or not interaction),
        "formal_between_group_comparison": bool(supported.get("formal_between_group_comparison")) or
        (interactions_ok and bool(declared.get("formal_interaction_coefficient_inference"))),
        "covariates_outside_schema": not outside,
        "nonlinear_terms": bool(supported.get("nonlinear_terms") or declared.get("nonlinear_terms")),
    }
    missing = []
    for cap in proposal.get("required_engine_capabilities", []):
        if not available.get(cap, bool(supported.get(cap, False))):
            missing.append(cap)
    if outside and "covariates_outside_schema" not in missing:
        missing.append("covariates_outside_schema")
    if len(moderators) > 1 and not declared.get("multiple_moderators", False):
        missing.append("multiple_moderators")
    checks = {
        "exposure_supported": proposal.get("exposure") in values["exposure"],
        "outcome_supported": proposal.get("outcome") in values["outcomes"],
        "method_in_registry": proposal.get("method") in audit["registry_methods"],
        "covariates_supported": not outside,
        "binary_moderators": moderators,
    }
    for name in ("exposure_supported", "outcome_supported", "method_in_registry"):
        if not checks[name]:
            missing.append(name.removesuffix("_supported").removesuffix("_in_registry") + "_not_supported")
    return {"currently_executable": not missing, "missing_capabilities": sorted(set(missing)), "checks": checks}


def _context() -> dict:
    """Everything the Director may use, from persisted artifacts and the live capability audit."""
    audit = capability_audit()
    proposals = _proposals()
    reviews = _reviews()
    approvals = _approvals(reviews)
    state, _ = build_state()
    view = {}
    for pid, p in proposals.items():
        hyps = p.get("hypothesis_ids", [])
        view[pid] = {
            "executability": _executability(p, audit),
            "hypotheses_approved": all(approvals.get(h, {}).get("intact") for h in hyps),
            "approving_reviews": sorted({approvals[h]["review_id"] for h in hyps if h in approvals}),
            "information_gain": (p.get("expected_information_gain") or {}).get("level"),
            "analysis_role": p.get("analysis_role"),
        }
    return {"audit": audit, "proposals": proposals, "reviews": reviews, "approvals": approvals,
            "state": state, "view": view}


def read_research_state() -> str:
    """Research question, next_action, EXP-001 (compact), the critique, approved hypotheses and human reviews."""
    try:
        ctx = _context()
        result_path, result, spec = _source("EXP-001")
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    state = ctx["state"]
    critiques = [_load(CRITIQUE_DIR / f"{c['critique_id']}.json") for c in state["critiques"]]
    hypotheses = []
    for hid in sorted(ctx["approvals"]):
        h = _load(HYPOTHESIS_DIR / f"{hid}.json")
        hypotheses.append({**{k: h.get(k) for k in ("hypothesis_id", "scientific_question", "falsifiable_claim",
                                                    "expected_direction", "limitations")},
                           "approved_in": ctx["approvals"][hid]["review_id"],
                           "approval_intact": ctx["approvals"][hid]["intact"]})
    return _ok(
        research_question=state["research_question"], dataset=state["dataset"],
        state_valid=state["validation"]["valid"], state_next_action=state["next_action"],
        experiments=[{"experiment_id": "EXP-001", "artifact": _rel(result_path), "review_status": result["review_status"],
                      "result": _compact(result, spec)}],
        critiques=[{k: c.get(k) for k in ("critique_id", "scientific_status", "status_rationale", "uncertainties",
                                          "limitations", "unsupported_claims", "untested_questions")}
                   for c in critiques],
        approved_hypotheses=hypotheses,
        human_reviews=[{k: r.get(k) for k in ("review_id", "review_type", "decision", "constraints", "scope")}
                       for r in ctx["reviews"].values()],
    )


def read_candidate_proposals() -> str:
    """Every active ExperimentProposal, with its hypotheses' approval status (proposals are not yet selected)."""
    try:
        ctx = _context()
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    items = []
    for pid, p in ctx["proposals"].items():
        items.append({**{k: v for k, v in p.items() if k != "provenance"},
                      "hypotheses_approved": ctx["view"][pid]["hypotheses_approved"],
                      "approving_reviews": ctx["view"][pid]["approving_reviews"]})
    return _ok(proposals=items, information_gain_levels=list(LEVELS),
               note="feasibility.status was recorded by the Planner at planning time; read_engine_capabilities "
                    "gives the CURRENT executability, which is what the decision must use.")


def read_engine_capabilities() -> str:
    """Live engine capability audit (schema + method registry) and the current executability of each proposal."""
    try:
        ctx = _context()
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    audit = ctx["audit"]
    engine = _engine_capabilities()
    return _ok(supported=audit["supported"], spec_values=audit["spec_values"], registry_methods=audit["registry_methods"],
               engine_capabilities={k: engine.get(k) for k in ("supported", "interaction", "limitations")} or None,
               evidence={k: audit["evidence"][k] for k in ("schema", "schema_sha256", "registry", "registry_sha256",
                                                           "fields_matching_interaction", "fields_matching_group_contrast")},
               proposals={pid: v["executability"] for pid, v in ctx["view"].items()})


# --- Validation --------------------------------------------------------------------------------

def _expected_status(view: dict | None) -> str:
    if view is None:
        return "NO_VALID_NEXT_EXPERIMENT"
    if not view["hypotheses_approved"]:
        return "HUMAN_REVIEW_REQUIRED"
    return "READY_TO_EXECUTE" if view["executability"]["currently_executable"] else "WAITING_FOR_ENGINE_CAPABILITY"


def _texts(d: dict) -> dict[str, list[str]]:
    """Free text of a decision: 'selection' fields carry the reasoning; 'all' adds uncertainties and constraints."""
    selection = [str(d.get("scientific_rationale") or ""), str(d.get("expected_learning") or ""),
                 str(d.get("next_action") or "")]
    selection += [str(a.get("reason_not_selected") or "") for a in d.get("alternatives") or [] if isinstance(a, dict)]
    rest = [str(s) for s in (d.get("uncertainties") or []) + (d.get("human_constraints_respected") or [])]
    return {"selection": selection, "all": selection + rest}


def _check(d: dict, ctx: dict) -> list[str]:
    errors: list[str] = []
    missing = [f for f in DECISION_FIELDS if f not in d]
    if missing:
        return [f"missing fields: {missing}"]
    forbidden = sorted(FORBIDDEN_KEYS & set(d))
    if forbidden:
        errors.append(f"the Director decides only: remove {forbidden} (no experiment id, spec or execution)")

    proposals, view = ctx["proposals"], ctx["view"]
    candidates = d["candidate_proposal_ids"]
    if not isinstance(candidates, list) or sorted(candidates) != sorted(proposals):
        errors.append(f"candidate_proposal_ids must list exactly the active proposals {sorted(proposals)}")
    preferred, best_exec = d["preferred_proposal_id"], d["best_executable_proposal_id"]
    for name, pid in (("preferred_proposal_id", preferred), ("best_executable_proposal_id", best_exec)):
        if pid is not None and pid not in proposals:
            errors.append(f"{name} {pid!r} is not an active proposal")
    if errors:
        return errors

    # Status and capability claims must match the live audit and the human reviews.
    if d["decision_status"] not in STATUSES:
        errors.append(f"decision_status must be one of {STATUSES}")
    expected = _expected_status(view.get(preferred))
    if d["decision_status"] != expected:
        errors.append(f"decision_status {d['decision_status']} contradicts the artifacts for {preferred}: expected "
                      f"{expected} (hypotheses approved and current executability from the engine audit)")
    cap = d["capability_check"] if isinstance(d["capability_check"], dict) else {}
    if preferred is not None:
        actual = view[preferred]["executability"]
        if cap.get("currently_executable") is not actual["currently_executable"] or \
                sorted(cap.get("missing_capabilities") or []) != actual["missing_capabilities"]:
            errors.append(f"capability_check must match the engine audit for {preferred}: "
                          f"currently_executable={actual['currently_executable']}, "
                          f"missing_capabilities={actual['missing_capabilities']}")

    # Scientific value first: feasibility must not override information gain.
    approved = [pid for pid in proposals if view[pid]["hypotheses_approved"]]
    rank = {lvl: i for i, lvl in enumerate(LEVELS)}
    if preferred is not None and approved:
        best_level = max(rank.get(view[p]["information_gain"], -1) for p in approved)
        if rank.get(view[preferred]["information_gain"], -1) < best_level:
            errors.append(f"{preferred} has {view[preferred]['information_gain']} expected information gain while "
                          f"{LEVELS[best_level]} proposals exist: feasibility must not override scientific value")
    if preferred is None and approved:
        errors.append("NO_VALID_NEXT_EXPERIMENT needs no proposal with approved hypotheses")
    executable = [p for p in approved if view[p]["executability"]["currently_executable"]]
    if best_exec is None and executable:
        errors.append(f"best_executable_proposal_id is null but {executable} can run today")
    if best_exec is not None:
        if best_exec not in executable:
            errors.append(f"{best_exec} is not currently executable with approved hypotheses")
        elif rank.get(view[best_exec]["information_gain"], -1) < max(rank.get(view[p]["information_gain"], -1)
                                                                     for p in executable):
            errors.append(f"best_executable_proposal_id must be among the most informative executable proposals")

    # Every other candidate is evaluated with a reason.
    alternatives = d["alternatives"] if isinstance(d["alternatives"], list) else []
    alt_ids = [a.get("proposal_id") for a in alternatives if isinstance(a, dict)]
    expected_alts = sorted(set(proposals) - {preferred})
    if sorted(alt_ids) != expected_alts:
        errors.append(f"alternatives must cover each non-preferred proposal exactly once: {expected_alts}")
    for a in alternatives:
        if isinstance(a, dict) and len(str(a.get("reason_not_selected") or "").split()) < 8:
            errors.append(f"explain why {a.get('proposal_id')} was not selected (at least one full sentence)")
        reason = str(a.get("reason_not_selected") or "") if isinstance(a, dict) else ""
        if NON_SCIENTIFIC_REASON.search(reason):
            errors.append(f"reject {a.get('proposal_id')} on scientific criteria (information gain, directness of the "
                          f"hypothesis test, uncertainty left by EXP-001, rigor, current feasibility), not on "
                          f"convenience: {NON_SCIENTIFIC_REASON.search(reason).group(0)!r}")
        elif reason and not SCIENTIFIC_CRITERIA.search(reason):
            errors.append(f"the reason for not selecting {a.get('proposal_id')} must name a scientific criterion "
                          f"(information gain, directness, uncertainty left by EXP-001, rigor or feasibility)")
    for name in ("scientific_rationale", "expected_learning", "next_action"):
        if len(str(d[name]).split()) < 8:
            errors.append(f"{name} needs at least one full sentence")
    for name in ("uncertainties", "human_constraints_respected"):
        if not isinstance(d[name], list) or not d[name] or not all(str(s).strip() for s in d[name]):
            errors.append(f"{name} must be a non-empty list of strings")

    texts = _texts(d)
    # Human constraints: cite the reviews that approved the preferred proposal's hypotheses.
    if preferred is not None:
        cited = " ".join(str(s) for s in d["human_constraints_respected"])
        absent = [r for r in view[preferred]["approving_reviews"] if r not in cited]
        if absent:
            errors.append(f"human_constraints_respected must cite {absent} and state how its constraints are kept")
    # Selection by expected learning, never by expected significance.
    hits = [s for s in texts["selection"] if SIGNIFICANCE.search(s)]
    if hits:
        errors.append("selection reasoning must not rely on expected statistical significance or p-values")
    # Association language only.
    causal = [s for s in texts["selection"] if CAUSAL.search(REGRESSION_TERMS.sub(" ", MAIN_EFFECT.sub(" ", s)))]
    if causal:
        errors.append(f"causal wording in the decision; use association language: {causal[:2]}")
    # An interval that includes zero is inconclusive, never evidence of no difference.
    for sentence in (s for text in texts["all"] for s in SENTENCE.split(text)):
        if INCLUDES_ZERO.search(sentence) and not INCONCLUSIVE.search(sentence):
            errors.append(f"an interval that includes zero is inconclusive; say so explicitly: {sentence!r}")
        if NO_DIFFERENCE.search(sentence) and not NEGATED.search(sentence):
            errors.append(f"an interval that includes zero is inconclusive, never evidence of no difference / no "
                          f"heterogeneity: {NO_DIFFERENCE.search(sentence).group(0)!r}")
    # The EXP-001 ranking stays inconclusive; outcomes are possibilities, not promises.
    for text in texts["all"]:
        for pattern, message in ((RANKING_OVERCLAIM, "EXP-001 gives sleep the most negative POINT estimate with an "
                                  "INCONCLUSIVE ranking: say 'strongest negative point estimate', never the "
                                  "strongest association or a 'point association'"),
                                 (RANKING_RESOLUTION, "a single moderator test does not resolve or clarify the ranking "
                                  "across outcomes"),
                                 (CERTAINTY, "state what each result would indicate, not what the test will establish")):
            match = pattern.search(text)
            if match:
                errors.append(f"{message}: {match.group(0)!r}")
    if d["decision_status"] == "READY_TO_EXECUTE" and not HUMAN_APPROVAL.search(str(d["next_action"])):
        errors.append("READY_TO_EXECUTE: next_action must say that human approval of this decision comes before "
                      "any execution")
    # An exploratory subgroup model cannot establish heterogeneity.
    exploratory = [pid for pid in proposals if view[pid]["analysis_role"] == "EXPLORATORY_SUBGROUP"]
    for text in texts["all"]:
        for sentence in SENTENCE.split(text):
            if any(pid in sentence for pid in exploratory) and OVERCLAIM_RESULT.search(sentence) \
                    and not EXPLORATORY_DISCLAIMER.search(sentence):
                errors.append(f"treats an exploratory subgroup proposal as a formal heterogeneity test: {sentence!r}")
    if preferred in exploratory and not any(EXPLORATORY_DISCLAIMER.search(t) for t in texts["selection"][:2]):
        errors.append(f"{preferred} is exploratory: say explicitly that it cannot establish a between-group difference")
    # No new experiment ids, no execution, no invented evidence.
    known = set(proposals) | set(ctx["reviews"]) | set(ctx["approvals"]) | \
        {e["experiment_id"] for e in ctx["state"]["experiments"]} | {c["critique_id"] for c in ctx["state"]["critiques"]}
    for text in texts["all"]:
        for match in IDS.finditer(text):
            ident = match.group(0)
            if ident.startswith("EXP-") and ident not in known:
                errors.append(f"do not assign or name a new experiment id ({ident}): the Director only decides")
            elif ident.startswith("DEC-"):
                errors.append(f"do not name decision ids ({ident}); the tool assigns them")
            elif ident not in known:
                errors.append(f"{ident} does not exist in the persisted artifacts")
    if any(EXECUTION_CLAIM.search(t) for t in texts["selection"]):
        errors.append("the decision must not claim that an experiment was run or executed")
    allowed = _numbers({pid: p for pid, p in proposals.items()}) | _numbers(ctx["source_numbers"])
    stripped = [IDS.sub(" ", t) for t in texts["all"]]
    bad = sorted(set(_untraceable(stripped, allowed)) | set(_untraceable_integers(stripped, allowed)))
    if bad:
        errors.append(f"numbers not found in the source artifacts (do not invent evidence): {bad}")
    return sorted(set(errors), key=errors.index)


def _with_sources(ctx: dict) -> dict:
    _, result, spec = _source("EXP-001")
    critiques = [_load(p) for p in sorted(CRITIQUE_DIR.glob("CRIT-*.json"))]
    hypotheses = [_load(HYPOTHESIS_DIR / f"{h}.json") for h in ctx["approvals"]]
    ctx["source_numbers"] = {"exp": _compact(result, spec), "spec": spec, "critiques": critiques,
                             "hypotheses": hypotheses, "reviews": list(ctx["reviews"].values())}
    return ctx


def validate_discovery_decision(decision: dict) -> str:
    """Dry run: check a DiscoveryDecision against the artifacts and the live engine audit. Writes nothing."""
    try:
        ctx = _with_sources(_context())
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    if not isinstance(decision, dict):
        return _err("decision must be a JSON object")
    errors = _check(decision, ctx)
    return _ok(valid=not errors, errors=errors)


def _declared_model() -> str | None:
    text = AGENT_SPEC.read_text(encoding="utf-8") if AGENT_SPEC.exists() else ""
    match = re.search(r"^\s+model:\s*(\S+)", text, re.MULTILINE)
    return match.group(1) if match else None


def save_discovery_decision(decision: dict) -> str:
    """Validate and persist a DiscoveryDecision as a NEW DEC-NNN artifact (never overwrites)."""
    try:
        ctx = _with_sources(_context())
    except (OSError, ValueError, KeyError) as exc:
        return _err(str(exc))
    if not isinstance(decision, dict):
        return _err("decision must be a JSON object")
    errors = _check(decision, ctx)
    if errors:
        return _err("DiscoveryDecision rejected; fix exactly these points and call save_discovery_decision again",
                    errors=errors)
    numbers = [int(p.stem.split("-")[1]) for p in DECISION_DIR.glob("DEC-*.json")] if DECISION_DIR.exists() else []
    decision_id = f"DEC-{max(numbers, default=0) + 1:03d}"
    preferred = decision["preferred_proposal_id"]
    audit = ctx["audit"]["evidence"]
    sources = [*(PROPOSAL_DIR / f"{p}.json" for p in ctx["proposals"]),
               *(REVIEW_DIR / f"{r}.json" for r in ctx["reviews"]),
               *(HYPOTHESIS_DIR / f"{h}.json" for h in sorted(ctx["approvals"])),
               *sorted(CRITIQUE_DIR.glob("CRIT-*.json")), ROOT / "reports/experiments/EXP-001/result.json"]
    payload = {
        "decision_id": decision_id,
        "type": "discovery_decision",
        **{k: decision[k] for k in DECISION_FIELDS},
        # Research-state references (docs/RESEARCH_STATE.md): the preferred proposal and every alternative.
        "considered_candidate_ids": sorted(ctx["proposals"]),
        "based_on_ids": sorted({e["experiment_id"] for e in ctx["state"]["experiments"]} |
                               {c["critique_id"] for c in ctx["state"]["critiques"]}),
        "decided_by": "discovery_director",
        "provenance": {
            "agent": "discovery_director",
            "model": _declared_model(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "code_version": _code_version(),
            "engine_capability_audit": {
                "schema": audit["schema"], "schema_sha256": audit["schema_sha256"],
                "registry": audit["registry"], "registry_sha256": audit["registry_sha256"],
                "supported": ctx["audit"]["supported"],
                "engine_capabilities": _rel(ENGINE_CAPABILITIES) if ENGINE_CAPABILITIES.exists() else None,
                "engine_capabilities_sha256": sha256(ENGINE_CAPABILITIES) if ENGINE_CAPABILITIES.exists() else None,
            },
            "proposal_executability": {pid: v["executability"] for pid, v in ctx["view"].items()},
            "preferred_hypotheses_approved_in": ctx["view"][preferred]["approving_reviews"] if preferred else [],
            "research_state_inputs_sha256": ctx["state"]["provenance"]["inputs_sha256"],
            "source_artifacts": [{"path": _rel(p), "sha256": sha256(p)} for p in sources],
            "policy": "decision only: no experiment executed, no ExperimentSpec written, no experiment id assigned",
        },
    }
    try:
        path = save_artifact("decisions", payload)
    except FileExistsError:
        return _err(f"{decision_id} already exists; call save_discovery_decision again")
    return _ok(decision_id=decision_id, artifact=path, decision_status=decision["decision_status"],
               preferred_proposal_id=preferred)
