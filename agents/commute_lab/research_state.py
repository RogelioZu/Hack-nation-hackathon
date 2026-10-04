"""Shared Research State: the structured scientific memory of the discovery loop (docs/RESEARCH_STATE.md).

Rebuilt deterministically from committed artifacts, never from LLM conversation memory:

    reports/experiments/EXP-NNN/{spec,result,validation}.json     engine output (source of truth)
    reports/discovery/<workspace>/<kind>/<ID>.json                  agent artifacts, one file per object
        kind in: evidence, critiques, hypotheses, candidates, decisions, reviews

The state stores IDs, references and JSON pointers into those artifacts. Scientific numbers are never
copied: a reviewer resolves them from the pointed artifact. Standard library only, no database.
The generated snapshot (reports/discovery/<workspace>/research_state.json) is not a source and is
never read back as one; it is only used to detect artifacts that changed after they were indexed.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = Path("reports/experiments")
DISCOVERY = Path("reports/discovery")
MANIFEST = Path("metadata/analytic_v1_manifest.json")
APPROVAL = Path("metadata/analytic_v1_experiment_approval.json")
PROTOCOL = Path("docs/EXPERIMENT_PROTOCOL.md")
INITIAL_STATE = Path("initial_state.json")
SNAPSHOT_NAME = "research_state.json"
STATE_VERSION = "1.0"

EXPERIMENT_ID = re.compile(r"EXP-\d{3,}")
CRITIQUE_ID = re.compile(r"CRIT-(EXP-\d{3,})-\d{3,}")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# Discovery artifact kinds: directory -> (registry kind, state section, accepted ID fields).
KINDS = {
    "evidence": ("evidence", "evidence", ("evidence_id",)),
    "critiques": ("critique", "critiques", ("critique_id",)),
    "hypotheses": ("hypothesis", "hypotheses", ("hypothesis_id",)),
    "candidates": ("candidate", "candidate_experiments", ("candidate_id", "proposal_id")),
    "decisions": ("decision", "decisions", ("decision_id",)),
    "reviews": ("review", "reviews", ("review_id",)),
}
# State entries always use the first (canonical) ID field name: a candidate is "candidate_id" in the state
# even when its artifact calls it "proposal_id" (tools.py, Supabase loop).
ID_FIELD = {kind: id_fields[0] for kind, _, id_fields in KINDS.values()}
EVIDENCE = frozenset({"experiment", "experiment_evidence", "critique", "critique_evidence", "evidence"})

# Reference fields per kind: (field path, accepted target kinds, relation). "a.b" walks dicts, "a[]" walks
# a list; list items may be IDs or objects carrying one of ITEM_ID_FIELDS. Unknown fields are ignored, so
# new artifact shapes only need to use one of these names to become traceable.
_CRITIQUE_REFS = ("motivated_by_critique_id", "source_critique_id", "critique_id", "source_critique_ids[]",
                  "critique_ids[]", "provenance.source_critique_id")
_EVIDENCE_REFS = ("evidence_ids[]", "supporting_evidence_ids[]", "opposing_evidence_ids[]", "evidence_refs[]",
                  "existing_evidence[].evidence_id", "existing_evidence[].ref")
REFS: dict[str, list[tuple[str, frozenset, str]]] = {
    "evidence": [("experiment_id", frozenset({"experiment"}), "derived_from")],
    "critique": [("experiment_id", frozenset({"experiment"}), "interprets"),
                 ("provenance.source_experiment_id", frozenset({"experiment"}), "interprets")],
    "hypothesis": [(p, frozenset({"critique"}), "motivated_by") for p in _CRITIQUE_REFS]
                  + [(p, EVIDENCE, "cites") for p in _EVIDENCE_REFS]
                  + [(p, frozenset({"hypothesis"}), "refines")
                     for p in ("protocol_hypothesis", "protocol_hypothesis_ids[]", "parent_hypothesis_ids[]")],
    "candidate": [(p, frozenset({"hypothesis"}), "tests")
                  for p in ("hypothesis_id", "hypothesis_ids[]", "tests_hypothesis_ids[]")]
                 + [(p, frozenset({"critique"}), "motivated_by") for p in _CRITIQUE_REFS]
                 + [(p, EVIDENCE, "cites") for p in _EVIDENCE_REFS],
    "decision": [(p, frozenset({"candidate"}), "selects")
                 for p in ("proposal_id", "candidate_id", "selected_candidate_id", "selected_proposal_id",
                           "preferred_proposal_id")]
                + [(p, frozenset({"candidate"}), "considers")
                   for p in ("considered_candidate_ids[]", "rejected_candidate_ids[]", "alternative_candidate_ids[]",
                             "candidate_proposal_ids[]", "alternatives[].proposal_id", "best_executable_proposal_id")]
                + [(p, EVIDENCE | {"hypothesis"}, "based_on")
                   for p in ("based_on_experiment_id", "based_on_critique_id", "based_on_ids[]", "evidence_ids[]")],
}
# Human reviews approve hypotheses for planning (REV-NNN) or a decision for execution (approved_decision_id).
REFS["review"] = [("approved_hypotheses[].hypothesis_id", frozenset({"hypothesis"}), "approves"),
                  ("approved_decision_id", frozenset({"decision"}), "approves")]
EXECUTION_APPROVAL = "APPROVED_FOR_EXECUTION"
# A decision may name the experiment it will produce before that experiment exists.
FUTURE_REFS = {"decision": [("experiment_id", "executed_as"), ("resulting_experiment_id", "executed_as")],
               # A decision approval names the experiment id it authorizes (pending until that experiment runs).
               "review": [("approved_experiment.experiment_id_to_assign", "authorizes")]}
ITEM_ID_FIELDS = ("evidence_id", "id", "ref", "critique_id", "hypothesis_id", "candidate_id", "proposal_id")
# DiscoveryDecision status (agents/commute_lab/director_tools.py) -> pipeline stage it leads to.
DECISION_STAGES = {"READY_TO_EXECUTE": ("run_experiment", "experiment_runner"),
                   "WAITING_FOR_ENGINE_CAPABILITY": ("engine_extension", "human"),
                   "HUMAN_REVIEW_REQUIRED": ("human_review", "human"),
                   "NO_VALID_NEXT_EXPERIMENT": ("hypotheses", "hypothesis_agent")}
# Short non-numeric fields copied into the state for readability (statements stay in the artifact).
DISPLAY = ("code", "title", "label", "status", "scientific_status", "type", "generated_by", "agent",
           "protocol_hypothesis", "contract_feasible", "rule_applied", "analysis_role", "review_type", "decision",
           "decision_status", "preferred_proposal_id", "best_executable_proposal_id")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _exp_number(experiment_id: str) -> int:
    return int(experiment_id.split("-")[1])


@dataclass
class Issue:
    level: str  # "error" | "warning"
    code: str
    message: str
    artifact: str | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class _Build:
    root: Path
    workspace: str
    issues: list[Issue] = field(default_factory=list)
    registry: dict[str, dict] = field(default_factory=dict)  # id -> {"kind", "artifact"}
    inputs: dict[str, str] = field(default_factory=dict)  # repo path -> sha256
    links: list[dict] = field(default_factory=list)

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def error(self, code: str, message: str, artifact: str | None = None) -> None:
        self.issues.append(Issue("error", code, message, artifact))

    def warn(self, code: str, message: str, artifact: str | None = None) -> None:
        self.issues.append(Issue("warning", code, message, artifact))

    def read(self, path: Path) -> Any:
        rel = self.rel(path)
        self.inputs[rel] = sha256(path)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            self.error("UNREADABLE_ARTIFACT", f"cannot parse JSON: {exc}", rel)
            return None

    def register(self, object_id: str, kind: str, artifact: str) -> bool:
        if object_id in self.registry:
            other = self.registry[object_id]["artifact"]
            self.error("DUPLICATE_ID", f"{object_id} is defined in {other} and {artifact}", artifact)
            return False
        self.registry[object_id] = {"kind": kind, "artifact": artifact}
        return True


# --- Sources ----------------------------------------------------------------------------------------

def _dataset(b: _Build) -> dict:
    manifest = b.read(b.root / MANIFEST) or {}
    approval = b.read(b.root / APPROVAL) or {}
    if manifest.get("dataset_version") != approval.get("dataset_version") or \
            manifest.get("dataset_sha256") != approval.get("dataset_sha256"):
        b.error("DATASET_VERSION_MISMATCH", "manifest and experiment approval disagree on dataset version or hash",
                APPROVAL.as_posix())
    return {"version": manifest.get("dataset_version"), "population_n": manifest.get("row_count"),
            "dataset_sha256": manifest.get("dataset_sha256"), "approval_status": approval.get("status"),
            "manifest": MANIFEST.as_posix(), "approval": APPROVAL.as_posix(),
            "contract": "docs/DATA_CONTRACT.md"}


def _protocol_hypotheses(b: _Build) -> list[dict]:
    """Pre-registered H1-H4 (heading of each '### Hn — name' block in the experiment protocol)."""
    path = b.root / PROTOCOL
    b.inputs[PROTOCOL.as_posix()] = sha256(path)
    found = re.findall(r"^### (H\d+) — (.+?)$", path.read_text(encoding="utf-8"), re.MULTILINE)
    hypotheses = []
    for code, name in found:
        if b.register(code, "hypothesis", PROTOCOL.as_posix()):
            hypotheses.append({"hypothesis_id": code, "source": "protocol", "title": name.strip(),
                               "artifact": PROTOCOL.as_posix(), "pointer": f"#{code}", "evaluated_in": [],
                               "references": []})
    return hypotheses


def _experiments(b: _Build, dataset: dict) -> tuple[list[dict], list[dict], list[dict]]:
    experiments, evidence, limitations = [], [], []
    base = b.root / EXPERIMENTS
    for folder in sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []:
        exp_id, rel_dir = folder.name, b.rel(folder)
        if not EXPERIMENT_ID.fullmatch(exp_id):
            b.error("INVALID_EXPERIMENT_ID", f"experiment folder {exp_id!r} is not EXP-NNN", rel_dir)
            continue
        paths = {name: folder / f"{name}.json" for name in ("spec", "result", "validation")}
        missing = [n for n, p in paths.items() if not p.exists()]
        if missing:
            b.error("MISSING_ARTIFACT", f"{exp_id} lacks {', '.join(missing)}.json", rel_dir)
            continue
        spec, result, validation = (b.read(paths[n]) for n in ("spec", "result", "validation"))
        if not (spec and result and validation):
            continue
        result_rel = b.rel(paths["result"])
        if validation.get("status") != "PASS" or validation.get("result_sha256") != b.inputs[result_rel]:
            b.error("UNVALIDATED_RESULT", f"{exp_id} result.json does not match a PASS validation.json", result_rel)
            continue
        if {spec.get("experiment_id"), result.get("experiment_id")} != {exp_id}:
            b.error("INVALID_EXPERIMENT_ID", f"spec/result experiment_id differ from folder {exp_id}", result_rel)
        if {spec.get("dataset_version"), result.get("dataset_version")} != {dataset["version"]} or \
                result.get("provenance", {}).get("dataset_sha256") != dataset["dataset_sha256"]:
            b.error("DATASET_VERSION_MISMATCH", f"{exp_id} does not use {dataset['version']} with the approved hash",
                    result_rel)
        source_spec = b.root / "experiments" / exp_id / "spec.json"
        if source_spec.exists() and canonical(b.read(source_spec)) != canonical(spec):
            b.error("SPEC_MISMATCH", f"experiments/{exp_id}/spec.json differs from the published spec", result_rel)
        if not b.register(exp_id, "experiment", result_rel):
            continue

        experiments.append({
            "experiment_id": exp_id, "status": result.get("status"), "review_status": result.get("review_status"),
            "dataset_version": result.get("dataset_version"), "method": spec.get("method"),
            "hypothesis_ids": spec.get("hypothesis_ids", []), "ranking_status": result.get("ranking", {}).get("status"),
            "quality_flags": result.get("quality_flags", []),
            "artifacts": {n: b.rel(p) for n, p in paths.items()}, "result_sha256": b.inputs[result_rel],
            "selected_by": [], "critiques": [],
        })
        # Evidence objects point into result.json; numbers stay there.
        for i, est in enumerate(result.get("estimates", [])):
            evidence.append({"evidence_id": f"{exp_id}/estimates/{est['model_id']}", "kind": "experiment_estimate",
                             "experiment_id": exp_id, "variant": est.get("variant"), "outcome": est.get("outcome"),
                             "exposure": est.get("exposure"), "artifact": result_rel, "pointer": f"/estimates/{i}"})
        evidence.append({"evidence_id": f"{exp_id}/ranking", "kind": "experiment_ranking", "experiment_id": exp_id,
                         "status": result.get("ranking", {}).get("status"), "artifact": result_rel,
                         "pointer": "/ranking"})
        for i, sens in enumerate(result.get("sensitivity_results", [])):
            evidence.append({"evidence_id": f"{exp_id}/sensitivity/{sens['name']}", "kind": "experiment_sensitivity",
                             "experiment_id": exp_id, "status": sens.get("ranking", {}).get("status"),
                             "artifact": result_rel, "pointer": f"/sensitivity_results/{i}"})
        for group in ("supported_hypotheses", "unsupported_hypotheses", "inconclusive_hypotheses"):
            for i, h in enumerate(result.get(group, [])):
                evidence.append({"evidence_id": f"{exp_id}/hypotheses/{h['id']}", "kind": "engine_hypothesis_assessment",
                                 "experiment_id": exp_id, "hypothesis_id": h["id"],
                                 "assessment": group.removesuffix("_hypotheses"),
                                 "artifact": result_rel, "pointer": f"/{group}/{i}"})
        for i, text in enumerate(result.get("limitations", [])):
            limitations.append({"source_id": exp_id, "artifact": result_rel, "pointer": f"/limitations/{i}",
                                "text": text})
        for ev in evidence:
            if ev["experiment_id"] == exp_id and ev["evidence_id"] not in b.registry:
                b.register(ev["evidence_id"], "experiment_evidence", result_rel)
    return experiments, evidence, limitations


def _discovery(b: _Build) -> dict[str, list[tuple[str, str, dict]]]:
    """(artifact path, object id, payload) per kind, after ID, filename and duplicate checks."""
    found: dict[str, list[tuple[str, str, dict]]] = {kind: [] for kind, _, _ in KINDS.values()}
    base = b.root / DISCOVERY / b.workspace
    if not base.exists():
        b.warn("EMPTY_WORKSPACE", f"{b.rel(base)} does not exist yet")
        return found
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        if folder.name not in KINDS:
            b.warn("UNKNOWN_KIND", f"ignored folder {folder.name!r}; known kinds: {sorted(KINDS)}", b.rel(folder))
            continue
        kind, _, id_fields = KINDS[folder.name]
        for path in sorted(folder.glob("*.json")):
            rel, payload = b.rel(path), b.read(path)
            if not isinstance(payload, dict):
                continue
            object_id = next((payload[f] for f in id_fields if isinstance(payload.get(f), str)), None)
            if not object_id:
                b.error("MISSING_ID", f"{kind} artifact has none of {id_fields}", rel)
                continue
            if object_id != path.stem:
                b.error("ID_FILENAME_MISMATCH", f"{kind} id {object_id!r} stored as {path.name}", rel)
                continue
            if b.register(object_id, kind, rel):
                found[kind].append((rel, object_id, payload))
    return found


# --- References --------------------------------------------------------------------------------------

def _values(obj: Any, path: str) -> list[str]:
    """IDs at a field path ("a.b", "a[]", "a[].b"); list items may be IDs or objects with an ID field."""
    current = [obj]
    for part in path.split("."):
        is_list, key = part.endswith("[]"), part.removesuffix("[]")
        nxt = []
        for item in current:
            value = item.get(key) if isinstance(item, dict) else None
            if value is None:
                continue
            nxt.extend(value if is_list and isinstance(value, list) else [] if is_list else [value])
        current = nxt
    ids = []
    for value in current:
        if isinstance(value, dict):
            value = next((value[f] for f in ITEM_ID_FIELDS if isinstance(value.get(f), str)), None)
        if isinstance(value, str) and value:
            ids.append(value)
    return ids


def _link(b: _Build, kind: str, source_id: str, payload: dict, artifact: str) -> list[dict]:
    refs, seen = [], set()
    for path, targets, relation in REFS.get(kind, []):
        for target in _values(payload, path):
            if (target, relation) in seen or target == source_id:
                continue
            seen.add((target, relation))
            entry = b.registry.get(target)
            if entry is None:
                if UUID.fullmatch(target):
                    b.warn("EXTERNAL_REFERENCE", f"{source_id}.{path} -> {target} (Supabase id, not a file artifact)",
                           artifact)
                    continue
                code = "MISSING_EVIDENCE" if relation == "cites" else "MISSING_REFERENCE"
                b.error(code, f"{source_id}.{path} -> {target} does not exist", artifact)
                continue
            if entry["kind"] not in targets:
                b.error("WRONG_REFERENCE_KIND", f"{source_id}.{path} -> {target} is a {entry['kind']}, "
                        f"expected {sorted(targets)}", artifact)
                continue
            refs.append({"to": target, "relation": relation, "field": path})
    for path, relation in FUTURE_REFS.get(kind, []):
        for target in _values(payload, path):
            if not EXPERIMENT_ID.fullmatch(target):
                b.error("INVALID_EXPERIMENT_ID", f"{source_id}.{path} = {target!r} is not EXP-NNN", artifact)
            elif target not in b.registry:
                b.warn("PENDING_EXPERIMENT", f"{source_id}.{path} -> {target} has not been run yet", artifact)
                refs.append({"to": target, "relation": relation, "field": path, "pending": True})
            else:
                refs.append({"to": target, "relation": relation, "field": path})
    b.links.extend({"from": source_id, **r} for r in refs)
    return refs


def _summary(kind: str, object_id: str, artifact: str, payload: dict, refs: list[dict], b: _Build) -> dict:
    entry = {ID_FIELD[kind]: object_id, "artifact": artifact, "sha256": b.inputs[artifact]}
    entry.update({k: payload[k] for k in DISPLAY if isinstance(payload.get(k), (str, bool))})
    entry["references"] = refs
    return entry


def _critique_checks(b: _Build, critique_id: str, payload: dict, artifact: str, dataset: dict) -> None:
    match = CRITIQUE_ID.fullmatch(critique_id)
    exp_id = payload.get("experiment_id")
    if not match or match.group(1) != exp_id:
        b.error("INVALID_CRITIQUE_ID", f"{critique_id} must be CRIT-<experiment_id>-NNN for {exp_id}", artifact)
    prov = payload.get("provenance", {})
    exp = b.registry.get(exp_id or "")
    if exp and exp["kind"] == "experiment" and prov.get("source_sha256") not in (None, b.inputs[exp["artifact"]]):
        b.error("SOURCE_CHANGED", f"{critique_id} was written for a different {exp_id} result.json "
                "(source_sha256 no longer matches)", artifact)
    if prov.get("dataset_version", dataset["version"]) != dataset["version"] or \
            prov.get("dataset_sha256", dataset["dataset_sha256"]) != dataset["dataset_sha256"]:
        b.error("DATASET_VERSION_MISMATCH", f"{critique_id} provenance names another dataset", artifact)


# --- State -------------------------------------------------------------------------------------------

def _next_action(experiments: list[dict], state: dict) -> dict | None:
    """Pipeline stage still missing for the latest experiment. Bookkeeping only: never picks a scientific option."""
    if not experiments:
        return None
    latest = max(experiments, key=lambda e: _exp_number(e["experiment_id"]))
    exp_id = latest["experiment_id"]
    reviews = [e["experiment_id"] for e in experiments if e.get("review_status") == "REQUIRES_HUMAN_REVIEW"]

    def from_refs(items: list[dict], id_field: str, relation: str, targets: set[str]) -> list[str]:
        return sorted(i[id_field] for i in items
                      if any(r["relation"] == relation and r["to"] in targets for r in i["references"]))

    action = {"derived": True, "latest_experiment_id": exp_id, "pending_human_review": reviews}
    critiques = from_refs(state["critiques"], "critique_id", "interprets", {exp_id})
    if not critiques:
        return {**action, "stage": "critique", "agent": "scientific_critic", "inputs": [exp_id]}
    hypotheses = from_refs(state["hypotheses"], "hypothesis_id", "motivated_by", set(critiques))
    if not hypotheses:
        return {**action, "stage": "hypotheses", "agent": "hypothesis_agent", "inputs": critiques}
    candidates = from_refs(state["candidate_experiments"], "candidate_id", "tests", set(hypotheses))
    if not candidates:
        return {**action, "stage": "candidate_experiments", "agent": "experiment_planner", "inputs": hypotheses}
    decisions = from_refs(state["decisions"], "decision_id", "selects", set(candidates))
    if not decisions:
        return {**action, "stage": "decision", "agent": "discovery_director", "inputs": candidates}
    # The latest decision governs (decisions are append-only; a rerun adds a new one).
    latest_decision = next(d for d in state["decisions"] if d["decision_id"] == max(decisions, key=_natural))
    stage, agent = DECISION_STAGES.get(latest_decision.get("decision_status"), ("run_experiment", "experiment_runner"))
    action = {**action, "stage": stage, "agent": agent, "inputs": [latest_decision["decision_id"]],
              "decision_status": latest_decision.get("decision_status")}
    if stage == "engine_extension":
        action["then"] = "rerun discovery_director: it recomputes executability from the engine"
    if stage == "run_experiment":
        approved_in = sorted((r["review_id"] for r in state.get("reviews", [])
                              if r.get("decision") == EXECUTION_APPROVAL and
                              any(x["relation"] == "approves" and x["to"] == latest_decision["decision_id"]
                                  for x in r["references"])), key=_natural)
        if approved_in:
            action["approved_in"] = approved_in
            action["requires"] = "assign the next experiment id and build its ExperimentSpec from the approved proposal"
        else:
            action["requires"] = "human approval of the decision before execution"
    return action


def _natural(text: str) -> list:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def build_state(root: Path = ROOT, workspace: str = "local", previous: dict | None = None,
                allow_changed: frozenset[str] = frozenset()) -> tuple[dict, list[Issue]]:
    """Index artifacts and build the SharedResearchState. Returns (state, issues); errors make it invalid."""
    b = _Build(root=root, workspace=workspace)
    initial = b.read(root / INITIAL_STATE) or {}
    dataset = _dataset(b)
    hypotheses = _protocol_hypotheses(b)
    experiments, evidence, limitations = _experiments(b, dataset)
    found = _discovery(b)

    # Critique evidence items get stable positional IDs (critiques are append-only, never rewritten).
    for artifact, cid, payload in found["critique"]:
        for i, item in enumerate(payload.get("evidence_summary", []), start=1):
            evidence.append({"evidence_id": f"{cid}/evidence/{i}", "kind": f"critique_{str(item.get('kind')).lower()}",
                             "critique_id": cid, "source_field": item.get("source"), "artifact": artifact,
                             "pointer": f"/evidence_summary/{i - 1}"})
            b.register(f"{cid}/evidence/{i}", "critique_evidence", artifact)

    sections: dict[str, list[dict]] = {"evidence": [], "critiques": [], "hypotheses": [],
                                       "candidate_experiments": [], "decisions": [], "reviews": []}
    order = ["evidence", "critique", "hypothesis", "review", "candidate", "decision"]  # upstream first
    section_of = {kind: section for kind, section, _ in KINDS.values()}
    for kind in order:
        for artifact, object_id, payload in found[kind]:
            if kind == "critique":
                _critique_checks(b, object_id, payload, artifact, dataset)
            refs = _link(b, kind, object_id, payload, artifact)
            entry = _summary(kind, object_id, artifact, payload, refs, b)
            if kind == "hypothesis":
                entry["source"] = "agent"
                if not any(r["relation"] == "motivated_by" for r in refs):
                    b.warn("UNLINKED_HYPOTHESIS", f"{object_id} names no critique", artifact)
            if kind == "critique":
                for group in ("limitations", "uncertainties"):
                    for i, text in enumerate(payload.get(group, [])):
                        limitations.append({"source_id": object_id, "artifact": artifact,
                                            "pointer": f"/{group}/{i}", "text": text})
            sections[section_of[kind]].append(entry)

    # Back-references so each object answers "who used me".
    by_id = {e["experiment_id"]: e for e in experiments}
    for link in b.links:
        if link["relation"] == "interprets" and link["to"] in by_id:
            by_id[link["to"]]["critiques"].append(link["from"])
        if link["relation"] == "executed_as" and link["to"] in by_id:
            by_id[link["to"]]["selected_by"].append(link["from"])
        if link["relation"] == "authorizes" and link["to"] in by_id:
            by_id[link["to"]].setdefault("authorized_by", []).append(link["from"])
    approvals = {}
    for link in b.links:
        if link["relation"] == "approves":
            approvals.setdefault(link["to"], []).append(link["from"])
    for h in sections["hypotheses"]:
        h["approved_in"] = sorted(approvals.get(h["hypothesis_id"], []), key=_natural)
    for h in hypotheses:
        h["evaluated_in"] = sorted(e["evidence_id"] for e in evidence
                                   if e.get("kind") == "engine_hypothesis_assessment" and e["hypothesis_id"] == h["hypothesis_id"])
    for e in experiments:
        e["critiques"], e["selected_by"] = sorted(set(e["critiques"])), sorted(set(e["selected_by"]))
        if "authorized_by" in e:
            e["authorized_by"] = sorted(set(e["authorized_by"]), key=_natural)

    # Artifacts indexed in the previous snapshot must keep their bytes (append-only sources).
    if previous:
        for path, digest in sorted(previous.get("provenance", {}).get("inputs", {}).items()):
            now = b.inputs.get(path)
            if path in allow_changed:
                continue
            if now is None and not (root / path).exists():
                b.error("ARTIFACT_REMOVED", "indexed in the previous snapshot but no longer exists", path)
            elif now is not None and now != digest:
                b.error("ACCIDENTAL_OVERWRITE", "bytes changed since the previous snapshot "
                        "(sources are append-only; pass --allow-changed if intended)", path)

    seen_text, unique_limitations = set(), []
    for item in limitations:
        key = (item["source_id"], item["text"])
        if key not in seen_text:
            seen_text.add(key)
            unique_limitations.append(item)

    state = {
        "_generated": {
            "note": "GENERATED SNAPSHOT - do not edit. Rebuild with: python scripts/build_research_state.py. "
                    "Sources of truth are the artifacts in provenance.inputs.",
            "state_version": STATE_VERSION,
            "generator": "agents/commute_lab/research_state.py",
        },
        "research_id": f"time-poverty-lab/{workspace}",
        "research_question": initial.get("research_question"),
        "research_question_source": INITIAL_STATE.as_posix(),
        "dataset": dataset,
        "evidence": sorted(evidence + sections["evidence"], key=lambda e: e["evidence_id"]),
        "critiques": sorted(sections["critiques"], key=lambda e: e["critique_id"]),
        "hypotheses": hypotheses + sorted(sections["hypotheses"], key=lambda e: e["hypothesis_id"]),
        "candidate_experiments": sorted(sections["candidate_experiments"], key=lambda e: e["candidate_id"]),
        "experiments": sorted(experiments, key=lambda e: _exp_number(e["experiment_id"])),
        "decisions": sorted(sections["decisions"], key=lambda e: _natural(e["decision_id"])),
        "reviews": sorted(sections["reviews"], key=lambda e: _natural(e["review_id"])),
        "limitations": unique_limitations,
        "links": sorted(b.links, key=lambda l: (l["from"], l["relation"], l["to"], l["field"])),
        "next_action": None,
        "provenance": {},
    }
    state["next_action"] = _next_action(state["experiments"], state)
    inputs = dict(sorted(b.inputs.items()))
    state["provenance"] = {
        "workspace": (DISCOVERY / workspace).as_posix(),
        "inputs": inputs,
        "inputs_sha256": hashlib.sha256(canonical(inputs).encode()).hexdigest(),
        "generator_sha256": sha256(Path(__file__)),
        "numbers_policy": "no scientific numbers are copied; resolve evidence pointers in the source artifact",
    }
    issues = sorted(b.issues, key=lambda i: (i.level, i.code, i.artifact or "", i.message))
    state["validation"] = {
        "valid": not any(i.level == "error" for i in issues),
        "errors": [i.as_dict() for i in issues if i.level == "error"],
        "warnings": [i.as_dict() for i in issues if i.level == "warning"],
    }
    return state, issues


def resolve(state: dict, evidence_id: str, root: Path = ROOT) -> Any:
    """Value behind an evidence pointer, read from its source artifact (for reviewers and the UI)."""
    entry = next(e for e in state["evidence"] if e["evidence_id"] == evidence_id)
    value = json.loads((root / entry["artifact"]).read_text(encoding="utf-8"))
    for part in entry["pointer"].strip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def trace(state: dict, object_id: str) -> dict:
    """Upstream chain (what this object relies on) and downstream users of an object."""
    up, down = {}, {}
    for link in state["links"]:
        up.setdefault(link["from"], []).append(link)
        down.setdefault(link["to"], []).append(link)
    for e in state["evidence"]:  # evidence objects belong to their experiment or critique
        parent = e.get("critique_id") or e.get("experiment_id")
        if parent and e["evidence_id"] != parent:
            up.setdefault(e["evidence_id"], []).append({"from": e["evidence_id"], "to": parent, "relation": "part_of"})

    def walk(node: str, graph: dict, key: str, seen: set) -> list[dict]:
        out = []
        for link in sorted(graph.get(node, []), key=lambda l: (l["relation"], l[key])):
            nxt = link[key]
            item = {"relation": link["relation"], "id": nxt}
            if nxt not in seen:
                item["chain"] = walk(nxt, graph, key, seen | {nxt})
            out.append(item)
        return out

    return {"id": object_id, "relies_on": walk(object_id, up, "to", {object_id}),
            "used_by": walk(object_id, down, "from", {object_id})}


def save_artifact(kind_dir: str, payload: dict, root: Path = ROOT, workspace: str = "local") -> str:
    """Write one discovery artifact as reports/discovery/<workspace>/<kind_dir>/<ID>.json; never overwrites.

    The ID is read from the payload (KINDS id fields) and becomes the file name, so the loader's
    ID/filename and duplicate checks hold by construction. Returns the repo-relative path.
    """
    if kind_dir not in KINDS:
        raise ValueError(f"unknown artifact kind {kind_dir!r}; known: {sorted(KINDS)}")
    id_fields = KINDS[kind_dir][2]
    object_id = next((payload[f] for f in id_fields if isinstance(payload.get(f), str)), None)
    if not object_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", object_id):
        raise ValueError(f"{kind_dir} payload needs a file-safe id in one of {id_fields}")
    path = root / DISCOVERY / workspace / kind_dir / f"{object_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:  # "x": an existing artifact is never replaced
        f.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return path.relative_to(root).as_posix()


def snapshot_path(root: Path = ROOT, workspace: str = "local") -> Path:
    return root / DISCOVERY / workspace / SNAPSHOT_NAME


def dumps(state: dict) -> str:
    return json.dumps(state, indent=2, ensure_ascii=False) + "\n"
