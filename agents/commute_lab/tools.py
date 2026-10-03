"""Function tools for the Omnigent research agents declared in /omnigent.yaml.

Every write goes through the service_role client (analysis/db.py) and leaves an
`agent_events` row, so the web panel can rebuild the loop. Tools return JSON
strings: Omnigent passes the LLM arguments as kwargs and stringifies the result.

Requires PYTHONPATH to include `agents/` and `analysis/` (see AGENTS.md §10).
"""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from db import client

ROOT = Path(__file__).resolve().parents[2]

# Analytic dataset delivered by the ENUT pipeline (AGENTS.md §8). Its contract and metadata are the
# sibling files sharing the stem (data/processed/analytic_v1.*).
DATASET = ROOT / "data" / "processed" / "analytic_v1.parquet"
SIDECAR_CHARS = 60_000  # cap per contract/metadata file returned to the LLM

# Closed protocols accepted by run_experiment (AGENTS.md §7.4).
PROTOCOLS = ("weighted_means_by_group", "wls_commute_by_sex")

# Pre-registered next-decision rules (AGENTS.md §2), stored on every new project.
DECISION_RULES = [
    {"id": "R1", "if": "Sex difference is sufficiently supported and subgroup sizes are adequate",
     "then": "Propose a test on household composition / presence of children"},
    {"id": "R2", "if": "No sex difference appears",
     "then": "Propose sensitivity to long commutes or a non-linear relationship"},
    {"id": "R3", "if": "Data quality or sample size prevents a conclusion",
     "then": "Revise variables, cohort and measurement before continuing"},
]
RULE_IDS = tuple(r["id"] for r in DECISION_RULES)

PROJECT_STATUSES = ("draft", "evidence", "planning", "running", "critique", "decided", "archived")
EVENT_TYPES = ("started", "tool_call", "handoff", "output", "decision", "approval", "error", "note")
HYPOTHESIS_STATUSES = ("proposed", "testing", "supported", "not_supported", "inconclusive", "superseded")


def _ok(**data: Any) -> str:
    return json.dumps({"ok": True, **data}, ensure_ascii=False, default=str)


def _err(message: str) -> str:
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


def _log(project_id: str, agent_name: str, event_type: str, summary: str,
         output_refs: dict | None = None, experiment_run_id: str | None = None,
         session_id: str | None = None) -> None:
    client().table("agent_events").insert({
        "project_id": project_id,
        "agent_name": agent_name,
        "event_type": event_type,
        "summary": summary,
        "output_refs": output_refs or {},
        "experiment_run_id": experiment_run_id,
        "session_id": session_id,
    }).execute()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _code_version() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


# --- Project and timeline ---------------------------------------------------

def create_project(title: str, question: str, cohort_definition: str | None = None,
                   omnigent_session_url: str | None = None) -> str:
    """Create a research project with the pre-registered decision rules R1–R3."""
    row = client().table("projects").insert({
        "title": title,
        "question": question,
        "cohort_definition": cohort_definition,
        "decision_rules": DECISION_RULES,
        "status": "evidence",
        "omnigent_session_url": omnigent_session_url,
    }).execute().data[0]
    _log(row["id"], "discovery_director", "started", f"Research project opened: {title}")
    return _ok(project_id=row["id"], decision_rules=DECISION_RULES)


def set_project_status(project_id: str, status: str) -> str:
    if status not in PROJECT_STATUSES:
        return _err(f"status must be one of {PROJECT_STATUSES}")
    client().table("projects").update({"status": status}).eq("id", project_id).execute()
    return _ok(project_id=project_id, status=status)


def log_event(project_id: str, agent_name: str, event_type: str, summary: str,
              session_id: str | None = None) -> str:
    """Append a step (hand-off, output, note...) to the public agent timeline."""
    if event_type not in EVENT_TYPES:
        return _err(f"event_type must be one of {EVENT_TYPES}")
    _log(project_id, agent_name, event_type, summary, session_id=session_id)
    return _ok()


# --- Evidence ---------------------------------------------------------------

def search_evidence(query: str, k: int = 5, project_id: str | None = None) -> str:
    """Hybrid search over the INEGI corpus in Supabase. The corpus is Spanish: query in Spanish."""
    from rag.search import search_evidence as _search  # heavy import (torch), load on demand

    hits = _search(query, k)
    if project_id:
        _log(project_id, "literature_agent", "tool_call", f'search_evidence("{query}") → {len(hits)} passages',
             output_refs={"passage_ids": [h.passage_id for h in hits]})
    return _ok(passages=[h.model_dump() for h in hits])


def _abstract(inverted: dict[str, list[int]] | None) -> str | None:
    if not inverted:
        return None
    words = sorted((pos, word) for word, positions in inverted.items() for pos in positions)
    return " ".join(word for _, word in words)


def search_openalex(query: str, per_page: int = 5, project_id: str | None = None) -> str:
    """Search OpenAlex and register each work in `sources` (kind 'paper') so it can be cited."""
    r = httpx.get("https://api.openalex.org/works", timeout=30, params={
        "search": query,
        "per_page": max(1, min(per_page, 10)),
        "select": "id,doi,title,publication_year,abstract_inverted_index,primary_location",
    })
    r.raise_for_status()
    papers = []
    for w in r.json().get("results", []):
        url = w.get("doi") or w["id"]
        venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        row = client().table("sources").upsert({
            "kind": "paper",
            "title": w.get("title") or "(untitled)",
            "url": url,
            "doi": w.get("doi"),
            "publisher": venue,
            "year": w.get("publication_year"),
        }, on_conflict="url").execute().data[0]
        abstract = _abstract(w.get("abstract_inverted_index"))
        papers.append({"source_id": row["id"], "title": row["title"], "doi": w.get("doi"), "url": url,
                       "year": w.get("publication_year"), "abstract": abstract[:1500] if abstract else None})
    if project_id:
        _log(project_id, "literature_agent", "tool_call", f'search_openalex("{query}") → {len(papers)} works',
             output_refs={"source_ids": [p["source_id"] for p in papers]})
    return _ok(papers=papers)


# --- Hypotheses and proposals -----------------------------------------------

def save_hypothesis(project_id: str, statement: str, generated_by: str = "hypothesis_agent",
                    supporting_passage_ids: list[str] | None = None,
                    opposing_passage_ids: list[str] | None = None) -> str:
    row = client().table("hypotheses").insert({
        "project_id": project_id,
        "statement": statement,
        "generated_by": generated_by,
        "supporting_passage_ids": supporting_passage_ids or [],
        "opposing_passage_ids": opposing_passage_ids or [],
    }).execute().data[0]
    _log(project_id, generated_by, "output", f"Hypothesis proposed: {statement}",
         output_refs={"hypothesis_id": row["id"]})
    return _ok(hypothesis_id=row["id"])


def save_proposals(project_id: str, hypothesis_id: str, proposals: list[dict],
                   selected_label: str, selection_rationale: str) -> str:
    """Store ≥2 candidate tests and mark the selected one with its rationale."""
    if len(proposals) < 2:
        return _err("at least two candidate tests are required")
    labels = [p.get("label") for p in proposals]
    if len(set(labels)) != len(labels) or selected_label not in labels:
        return _err("labels must be unique and selected_label must be one of them")
    bad = [p.get("protocol") for p in proposals if p.get("protocol") not in PROTOCOLS]
    if bad:
        return _err(f"unknown protocols {bad}; allowed: {PROTOCOLS}")

    rows = client().table("experiment_proposals").insert([{
        "project_id": project_id,
        "hypothesis_id": hypothesis_id,
        "label": p["label"],
        "title": p.get("title") or p["protocol"],
        "protocol": p["protocol"],
        "description": p.get("description"),
        "learning_value": p.get("learning_value"),
        "feasibility": p.get("feasibility"),
        "cost": p.get("cost"),
        "selected": p["label"] == selected_label,
        "selection_rationale": selection_rationale if p["label"] == selected_label else None,
    } for p in proposals]).execute().data
    client().table("hypotheses").update({"status": "testing"}).eq("id", hypothesis_id).execute()
    ids = {r["label"]: r["id"] for r in rows}
    _log(project_id, "experiment_planner", "output",
         f"Proposed tests {', '.join(labels)}; selected {selected_label}: {selection_rationale}",
         output_refs={"proposal_ids": ids})
    return _ok(proposal_ids=ids, selected_proposal_id=ids[selected_label])


# --- Dataset and experiment -------------------------------------------------

def describe_dataset(project_id: str | None = None) -> str:
    """Contract and metadata of the analytic dataset (columns, units, filters, n) and its hash. Never returns rows."""
    if not DATASET.exists():
        return _err(f"{DATASET.relative_to(ROOT)} not found: the ENUT pipeline has not delivered it yet")
    files: dict[str, Any] = {}
    for path in sorted(DATASET.parent.glob(f"{DATASET.stem}.*")):
        if path == DATASET or not path.is_file():
            continue
        text = path.read_text(errors="replace")[:SIDECAR_CHARS]
        try:
            files[path.name] = json.loads(text)
        except ValueError:
            files[path.name] = text
    if project_id:
        _log(project_id, "data_steward", "tool_call",
             f"describe_dataset → {', '.join(files) or 'no contract/metadata files'}")
    return _ok(dataset=str(DATASET.relative_to(ROOT)), dataset_hash=_sha256(DATASET), files=files)


def _load_protocol(name: str):
    """Protocol function from analysis/enut/protocols.py, or None while it is not implemented."""
    if not (ROOT / "analysis" / "enut" / "protocols.py").exists():
        return None
    from enut.protocols import PROTOCOLS as implemented  # import errors inside it surface as run errors
    return implemented.get(name)


def run_experiment(project_id: str, proposal_id: str, parameters: dict | None = None) -> str:
    """Run the selected proposal's closed protocol on the analytic dataset and persist the aggregates.

    Protocols live in analysis/enut/protocols.py as
    PROTOCOLS = {name: fn(dataset_path, parameters) -> {"results", "sample_sizes"}}, written against the
    dataset contract. The runner hashes the exact file it hands to the protocol. Until the dataset and
    the protocol exist the run is recorded as failed — numbers are never invented.
    """
    db = client()
    proposal = db.table("experiment_proposals").select("*").eq("id", proposal_id) \
        .eq("project_id", project_id).maybe_single().execute()
    if not proposal or not proposal.data:
        return _err("proposal not found for this project")
    protocol = proposal.data["protocol"]
    if protocol not in PROTOCOLS:
        return _err(f"protocol {protocol!r} is not a closed protocol")

    run = db.table("experiment_runs").insert({
        "project_id": project_id,
        "hypothesis_id": proposal.data["hypothesis_id"],
        "proposal_id": proposal_id,
        "protocol": protocol,
        "parameters": parameters or {},
        "code_version": _code_version(),
        "dataset_hash": _sha256(DATASET) if DATASET.exists() else None,
        "status": "running",
        "started_at": _now(),
    }).execute().data[0]
    _log(project_id, "experiment_runner", "tool_call", f"run_experiment({protocol}) started",
         experiment_run_id=run["id"])

    error = None
    try:
        fn = _load_protocol(protocol)
        if not DATASET.exists():
            error = f"Analytic dataset {DATASET.relative_to(ROOT)} is not available yet (ENUT pipeline)."
        elif fn is None:
            error = f"Protocol {protocol!r} is not implemented yet (analysis/enut/protocols.py)."
        else:
            output = fn(DATASET, parameters or {})
    except Exception as exc:  # report the real failure to the agents and the panel
        error = f"{type(exc).__name__}: {exc}"
    if error is None:
        db.table("experiment_runs").update({
            "status": "succeeded",
            "results": output["results"],
            "sample_sizes": output.get("sample_sizes", {}),
            "finished_at": _now(),
        }).eq("id", run["id"]).execute()
        _log(project_id, "experiment_runner", "output", f"{protocol} succeeded",
             experiment_run_id=run["id"])
        return _ok(run_id=run["id"], status="succeeded", results=output["results"],
                   sample_sizes=output.get("sample_sizes", {}))

    db.table("experiment_runs").update({"status": "failed", "error": error, "finished_at": _now()}) \
        .eq("id", run["id"]).execute()
    _log(project_id, "experiment_runner", "error", error, experiment_run_id=run["id"])
    return _ok(run_id=run["id"], status="failed", error=error)


def read_run(run_id: str) -> str:
    res = client().table("experiment_runs").select("*").eq("id", run_id).maybe_single().execute()
    if not res or not res.data:
        return _err("run not found")
    return _ok(run=res.data)


# --- Critique and decision --------------------------------------------------

def record_decision(project_id: str, experiment_run_id: str, interpretation: str, rule_applied: str,
                    next_test: str, rationale: str, uncertainty: str | None = None,
                    limitations: str | None = None, decided_by: str = "scientific_critic",
                    hypothesis_id: str | None = None, hypothesis_status: str | None = None) -> str:
    """Store a decision that cites a real run and one of the pre-registered rules R1–R3."""
    if rule_applied not in RULE_IDS:
        return _err(f"rule_applied must be one of {RULE_IDS}")
    if hypothesis_status and hypothesis_status not in HYPOTHESIS_STATUSES:
        return _err(f"hypothesis_status must be one of {HYPOTHESIS_STATUSES}")
    db = client()
    run = db.table("experiment_runs").select("id,status").eq("id", experiment_run_id) \
        .eq("project_id", project_id).maybe_single().execute()
    if not run or not run.data:
        return _err("experiment_run_id does not belong to this project")

    row = db.table("decisions").insert({
        "project_id": project_id,
        "experiment_run_id": experiment_run_id,
        "interpretation": interpretation,
        "uncertainty": uncertainty,
        "limitations": limitations,
        "rule_applied": rule_applied,
        "next_test": next_test,
        "rationale": rationale,
        "decided_by": decided_by,
    }).execute().data[0]
    if hypothesis_id and hypothesis_status:
        db.table("hypotheses").update({"status": hypothesis_status}).eq("id", hypothesis_id).execute()
    _log(project_id, decided_by, "decision", f"{rule_applied}: {next_test}",
         output_refs={"decision_id": row["id"]}, experiment_run_id=experiment_run_id)
    return _ok(decision_id=row["id"], run_status=run.data["status"])
