"""Function tools for the Omnigent research agents declared in /omnigent.yaml.

Every write goes through the service_role client (analysis/db.py) and leaves an
`agent_events` row, so the web panel can rebuild the loop. Tools return JSON
strings: Omnigent passes the LLM arguments as kwargs and stringifies the result.

Numbers only come from the deterministic engine (src/experiments/), which runs in its own
interpreter (EXPERIMENT_PYTHON, default .venv-experiments/bin/python, built from
requirements-experiments.txt) through scripts/run_experiment.py and scripts/check_experiment_spec.py.
Full discovery objects (critiques, hypotheses, candidates, decisions) are also written as JSON
artifacts under reports/discovery/<project_id>/ and in agent_events.output_refs.

Requires PYTHONPATH to include `agents/` and `analysis/` (see AGENTS.md §10).
"""

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx

from db import client

ROOT = Path(__file__).resolve().parents[2]

DATASET = ROOT / "data" / "processed" / "analytic_v1.parquet"
DATA_CONTRACT = ROOT / "docs" / "DATA_CONTRACT.md"
MANIFEST = ROOT / "metadata" / "analytic_v1_manifest.json"
APPROVAL = ROOT / "metadata" / "analytic_v1_experiment_approval.json"
SPEC_DIR = ROOT / "experiments"
REPORT_DIR = ROOT / "reports" / "experiments"
DISCOVERY_DIR = ROOT / "reports" / "discovery"
ENGINE_PYTHON = os.environ.get("EXPERIMENT_PYTHON") or str(ROOT / ".venv-experiments" / "bin" / "python")
ENGINE_METHOD = "weighted_linear_regression"
NEEDS_CONTRACT_REVISION = "requires_contract_revision"

# Pre-registered next-decision rules (AGENTS.md §2), stored on every new project. Guides, not a fixed sequence.
DECISION_RULES = [
    {"id": "R1", "if": "Sex difference is sufficiently supported and subgroup sizes are adequate",
     "then": "Propose a test on household composition / presence of children"},
    {"id": "R2", "if": "No sex difference appears",
     "then": "Propose sensitivity to long commutes or a non-linear relationship"},
    {"id": "R3", "if": "Data quality or sample size prevents a conclusion",
     "then": "Revise variables, cohort and measurement before continuing"},
]
RULE_IDS = tuple(r["id"] for r in DECISION_RULES)
VERDICTS = ("VALID", "UNCERTAIN", "REQUIRES_REVISION", "REQUIRES_HUMAN_REVIEW")

PROJECT_STATUSES = ("draft", "evidence", "planning", "running", "critique", "decided", "archived")
EVENT_TYPES = ("started", "tool_call", "handoff", "output", "decision", "approval", "error", "note")
HYPOTHESIS_STATUSES = ("proposed", "testing", "supported", "not_supported", "inconclusive", "superseded")

# What the strict ExperimentSpec accepts today (src/experiments/schemas.py, AGENTS.md §7.4).
SPEC_CAPABILITIES = {
    "dataset_version": ["analytic_v1"],
    "population": {"source": "approved_analytic_v1", "states": ["09", "15"], "age_range": [18, 65],
                   "sexes": ["male", "female"], "expected_n": "optional positive int"},
    "exposure": ["commute_5h"],
    "outcomes": ["sleep_weekday_min", "personal_hygiene_weekday_min",
                 "household_conversation_weekday_min", "leisure_weekday_min"],
    "covariates": ["work_weekday_min", "age", "sex", "state"],
    "method": [ENGINE_METHOD],
    "hypothesis_ids": ["H1", "H2"],
    "sensitivity_analyses": ["exclude_zero_weekday_work"],
    "uncertainty": ["psu_cluster_CR1_t"],
    "confidence_level": [0.95],
    "fixed_fields": {"schema_version": "1.0", "survey_weight": "weight", "cluster": "cluster",
                     "stratum": "stratum", "missingness_policy": "model_specific_complete_case"},
    "feasible_within_contract": [
        "Re-estimate the same model in a subpopulation (one sex, one state, an age range) by changing population",
        "Change the outcome set, the approved covariate set, the sensitivity list or include_unadjusted",
    ],
    "requires_contract_revision": [
        "Interactions (commute x sex, commute x children)", "Non-linear terms, splines, commute categories",
        "Two-part / participation models", "has_child_u15, has_minor_u18, work_modality or household_size as covariates",
        "Hypothesis ids other than H1/H2 inside the spec (H3/H4 and agent hypotheses are tracked in Supabase)",
    ],
    "pitfalls": [
        "Restricting to one sex while keeping 'sex' as covariate is RANK_DEFICIENT: drop 'sex' from covariates",
        "Restricting to one state while keeping 'state' as covariate is RANK_DEFICIENT: drop 'state'",
        "H2 needs at least two outcomes",
        "Separate subgroup runs are descriptive comparisons, not a formal interaction test",
    ],
}


def _ok(**data: Any) -> str:
    return json.dumps({"ok": True, **data}, ensure_ascii=False, default=str)


def _err(message: str, **data: Any) -> str:
    return json.dumps({"ok": False, "error": message, **data}, ensure_ascii=False, default=str)


def _log(project_id: str, agent_name: str, event_type: str, summary: str,
         output_refs: dict | None = None, experiment_run_id: str | None = None,
         session_id: str | None = None, input_refs: dict | None = None) -> None:
    client().table("agent_events").insert({
        "project_id": project_id,
        "agent_name": agent_name,
        "event_type": event_type,
        "summary": summary,
        "input_refs": input_refs or {},
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


def _artifact(project_id: str, kind: str, object_id: str, payload: dict) -> str:
    """Write a discovery object as reports/discovery/<project_id>/<kind>/<id>.json; return its repo path."""
    path = DISCOVERY_DIR / project_id / kind / f"{object_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return path.relative_to(ROOT).as_posix()


def _read_artifact(project_id: str, kind: str, object_id: str) -> dict | None:
    path = DISCOVERY_DIR / project_id / kind / f"{object_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _engine(args: list[str], stdin: str | None = None, timeout: int = 600) -> subprocess.CompletedProcess:
    if not Path(ENGINE_PYTHON).exists():
        raise RuntimeError(f"Engine interpreter {ENGINE_PYTHON} not found: create it with "
                           "`uv venv -p 3.12 .venv-experiments && uv pip install -p .venv-experiments/bin/python "
                           "-r requirements-experiments.txt` or set EXPERIMENT_PYTHON")
    return subprocess.run([ENGINE_PYTHON, *args], cwd=ROOT, input=stdin, capture_output=True,
                          text=True, timeout=timeout)


def _check_spec(spec: dict) -> dict:
    """Schema validation + dry run of the engine; returns validity and n only."""
    proc = _engine(["scripts/check_experiment_spec.py"], stdin=json.dumps(spec))
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"valid": False, "code": "CHECK_FAILED", "message": (proc.stderr or proc.stdout)[-2000:]}


def _next_experiment_id() -> str:
    numbers = [int(m.group(1)) for d in (SPEC_DIR, REPORT_DIR) if d.exists()
               for p in d.iterdir() if (m := re.fullmatch(r"EXP-(\d{3,})", p.name))]
    return f"EXP-{max(numbers, default=0) + 1:03d}"


# --- Compact views of an ExperimentResult -----------------------------------

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


def _population_label(population: dict) -> str:
    sexes = population.get("sexes", [])
    return "all" if set(sexes) == {"male", "female"} else "+".join(sexes)


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
    return {
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


def _web_results(result: dict, spec: dict, compact: dict) -> dict:
    """experiment_runs.results: the shape web/lib/types.ts draws, plus the compact engine view."""
    group = _population_label(spec.get("population", {}))
    return {
        "label": "exploratory",
        "method": (f"Weighted linear regression (FAC_PER): outcome ~ commute_5h + "
                   f"{' + '.join(spec.get('covariates') or ['(no covariates)'])}"),
        "units": "Weekday (Mon-Fri) minutes associated with +300 weekday commute minutes",
        "uncertainty_method": ("CR1 cluster-robust SE by UPM_DIS with t(G-1) intervals; EST_DIS strata, FPC "
                               "and replicate weights not incorporated (approximation, not full survey variance)"),
        "estimates": [{"activity": e["outcome"], "sex": group, "estimate": round(e["coefficient"], 3),
                       "ci_low": round(e["interval"]["lower"], 3), "ci_high": round(e["interval"]["upper"], 3),
                       "n": e["n"]} for e in result["estimates"] if e["variant"] == "adjusted"],
        "notes": [f"{result['experiment_id']}: n={result['sample_size']}; ranking {result['ranking']['status']}",
                  *[f"Sensitivity {s['name']}: n_after={s['n_after']} ({s['n_excluded']} excluded)"
                    for s in result["sensitivity_results"]],
                  f"Review status: {result['review_status']}"],
        "engine": compact,
    }


def _sample_sizes(result: dict) -> dict:
    sizes = {c["step"]: c["n"] for c in result["population_counts"]}
    sizes["analytic_sample"] = result["sample_size"]
    for s in result["sensitivity_results"]:
        sizes[f"sensitivity_{s['name']}"] = s["n_after"]
    return sizes


def _artifacts(experiment_id: str) -> list[str]:
    paths = [SPEC_DIR / experiment_id / "spec.json",
             *[REPORT_DIR / experiment_id / n for n in ("result.json", "summary.md", "spec.json", "validation.json")]]
    return [p.relative_to(ROOT).as_posix() for p in paths if p.exists()]


def _load_result(experiment_id: str) -> tuple[dict, dict]:
    out = REPORT_DIR / experiment_id
    result = json.loads((out / "result.json").read_text(encoding="utf-8"))
    spec = json.loads((out / "spec.json").read_text(encoding="utf-8"))
    return result, spec


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


def search_web(query: str, max_results: int = 5, project_id: str | None = None) -> str:
    """Live web search through Bright Data's SERP API; registers each result in `sources` (kind 'report').

    Needs BRIGHTDATA_API_TOKEN and BRIGHTDATA_SERP_ZONE in the environment. Web snippets are context
    (grey literature, reports, news), never a source of numerical results.
    """
    token, zone = os.environ.get("BRIGHTDATA_API_TOKEN"), os.environ.get("BRIGHTDATA_SERP_ZONE")
    if not token or not zone:
        return _err("Bright Data is not configured (BRIGHTDATA_API_TOKEN / BRIGHTDATA_SERP_ZONE): "
                    "use search_openalex and search_evidence instead")
    r = httpx.post("https://api.brightdata.com/request", timeout=60,
                   headers={"Authorization": f"Bearer {token}"},
                   json={"zone": zone, "format": "raw",
                         "url": f"https://www.google.com/search?q={quote_plus(query)}&hl=en&brd_json=1"})
    if r.status_code >= 400:
        return _err(f"Bright Data request failed: HTTP {r.status_code} {r.text[:300]}")
    try:
        payload = r.json()
        if isinstance(payload.get("body"), str):
            payload = json.loads(payload["body"])
    except ValueError:
        return _err("Bright Data did not return parsed SERP JSON (check that the zone is a SERP API zone)")
    results = []
    for item in (payload.get("organic") or [])[:max(1, min(max_results, 10))]:
        url = item.get("link") or item.get("url")
        if not url:
            continue
        row = client().table("sources").upsert({
            "kind": "report",
            "title": item.get("title") or url,
            "url": url,
            "publisher": urlparse(url).netloc,
        }, on_conflict="url").execute().data[0]
        results.append({"source_id": row["id"], "title": row["title"], "url": url,
                        "snippet": item.get("description") or item.get("snippet")})
    if project_id:
        _log(project_id, "literature_agent", "tool_call", f'search_web("{query}") → {len(results)} web results',
             output_refs={"source_ids": [x["source_id"] for x in results], "provider": "brightdata"})
    return _ok(results=results)


# --- Experiment results and critique ----------------------------------------

def register_experiment(project_id: str, experiment_id: str = "EXP-001") -> str:
    """Register an already-published engine result (reports/experiments/<id>/) as a run of this project.

    Used to start the discovery loop from real evidence (EXP-001). Idempotent per project.
    """
    if not re.fullmatch(r"EXP-\d{3,}", experiment_id):
        return _err("experiment_id must look like EXP-001")
    db = client()
    existing = db.table("experiment_runs").select("id").eq("project_id", project_id) \
        .eq("parameters->>experiment_id", experiment_id).execute().data
    if existing:
        return _ok(run_id=existing[0]["id"], experiment_id=experiment_id, already_registered=True)
    try:
        result, spec = _load_result(experiment_id)
        validation = json.loads((REPORT_DIR / experiment_id / "validation.json").read_text(encoding="utf-8"))
    except OSError as exc:
        return _err(f"{experiment_id} has no published result: {exc}")
    if validation.get("status") != "PASS":
        return _err(f"{experiment_id} validation.json is not PASS")
    compact = _compact(result, spec)
    run = db.table("experiment_runs").insert({
        "project_id": project_id,
        "protocol": spec["method"],
        "parameters": spec,
        "dataset_hash": f"sha256:{result['provenance']['dataset_sha256']}",
        "code_version": _code_version(),
        "sample_sizes": _sample_sizes(result),
        "results": _web_results(result, spec, compact),
        "artifact_paths": _artifacts(experiment_id),
        "status": "succeeded",
        "finished_at": _now(),
    }).execute().data[0]
    _log(project_id, "discovery_director", "output",
         f"{experiment_id} registered as evidence (n={result['sample_size']}, ranking {result['ranking']['status']}, "
         f"{result['review_status']})", experiment_run_id=run["id"],
         output_refs={"experiment_id": experiment_id, "artifacts": _artifacts(experiment_id)})
    return _ok(run_id=run["id"], experiment_id=experiment_id, review_status=result["review_status"])


def read_experiment_result(run_id: str) -> str:
    """Compact, critic-ready view of a run: estimates, intervals, ranking, sensitivity, diagnostics, limitations."""
    res = client().table("experiment_runs").select("*").eq("id", run_id).maybe_single().execute()
    if not res or not res.data:
        return _err("run not found")
    run = res.data
    view = (run.get("results") or {}).get("engine")
    return _ok(run_id=run["id"], status=run["status"], error=run.get("error"),
               experiment_id=(run.get("parameters") or {}).get("experiment_id"),
               dataset_hash=run.get("dataset_hash"), sample_sizes=run.get("sample_sizes"),
               artifact_paths=run.get("artifact_paths"), result=view)


def save_critique(project_id: str, experiment_run_id: str, verdict: str, evidence_strength: str,
                  summary: str, uncertainty: str, limitations: list[str],
                  unsupported_interpretations: list[str] | None = None,
                  diagnostics_review: list[str] | None = None, open_questions: list[str] | None = None,
                  rule_applied: str | None = None, recommended_direction: str | None = None) -> str:
    """Store a ScientificCritique of a real run (decisions row by scientific_critic + JSON artifact)."""
    if verdict not in VERDICTS:
        return _err(f"verdict must be one of {VERDICTS}")
    if rule_applied and rule_applied not in RULE_IDS:
        return _err(f"rule_applied must be one of {RULE_IDS}")
    db = client()
    run = db.table("experiment_runs").select("id,status,parameters").eq("id", experiment_run_id) \
        .eq("project_id", project_id).maybe_single().execute()
    if not run or not run.data:
        return _err("experiment_run_id does not belong to this project")
    experiment_id = (run.data.get("parameters") or {}).get("experiment_id")
    row = db.table("decisions").insert({
        "project_id": project_id,
        "experiment_run_id": experiment_run_id,
        "interpretation": f"[{verdict}] {summary}",
        "uncertainty": uncertainty,
        "limitations": "\n".join(limitations),
        "rule_applied": rule_applied,
        "next_test": recommended_direction,
        "rationale": f"Evidence strength: {evidence_strength}",
        "decided_by": "scientific_critic",
    }).execute().data[0]
    critique = {
        "critique_id": row["id"], "experiment_run_id": experiment_run_id, "experiment_id": experiment_id,
        "verdict": verdict, "evidence_strength": evidence_strength, "summary": summary,
        "uncertainty": uncertainty, "diagnostics_review": diagnostics_review or [],
        "limitations": limitations, "unsupported_interpretations": unsupported_interpretations or [],
        "open_questions": open_questions or [], "rule_applied": rule_applied,
        "recommended_direction": recommended_direction, "created_at": _now(),
    }
    path = _artifact(project_id, "critiques", row["id"], critique)
    _log(project_id, "scientific_critic", "output", f"Critique of {experiment_id}: {verdict} ({evidence_strength})",
         output_refs={"critique": critique, "artifact": path}, experiment_run_id=experiment_run_id)
    return _ok(critique_id=row["id"], artifact=path)


# --- Hypotheses and candidates ----------------------------------------------

def save_hypothesis(project_id: str, code: str, statement: str, existing_evidence: list[dict],
                    inference: str, new_hypothesis: str, generated_by: str = "hypothesis_agent",
                    motivated_by_critique_id: str | None = None,
                    supporting_passage_ids: list[str] | None = None,
                    opposing_passage_ids: list[str] | None = None) -> str:
    """Store a falsifiable hypothesis with a stable code, separating evidence, inference and new hypothesis."""
    if not re.fullmatch(r"H\d+", code):
        return _err("code must look like H5 (H1–H4 are the protocol hypotheses)")
    row = client().table("hypotheses").insert({
        "project_id": project_id,
        "statement": f"[{code}] {statement}",
        "generated_by": generated_by,
        "supporting_passage_ids": supporting_passage_ids or [],
        "opposing_passage_ids": opposing_passage_ids or [],
    }).execute().data[0]
    hypothesis = {"hypothesis_id": row["id"], "code": code, "statement": statement, "generated_by": generated_by,
                  "existing_evidence": existing_evidence, "inference": inference,
                  "new_hypothesis": new_hypothesis, "motivated_by_critique_id": motivated_by_critique_id}
    path = _artifact(project_id, "hypotheses", row["id"], hypothesis)
    _log(project_id, generated_by, "output", f"Hypothesis {code} proposed: {statement}",
         output_refs={"hypothesis": hypothesis, "artifact": path})
    return _ok(hypothesis_id=row["id"], code=code, artifact=path)


def describe_dataset(project_id: str | None = None) -> str:
    """Data contract, manifest summary, approval status and what the ExperimentSpec accepts. Never returns rows."""
    if not DATASET.exists():
        return _err(f"{DATASET.relative_to(ROOT)} not found")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    approval = json.loads(APPROVAL.read_text(encoding="utf-8")) if APPROVAL.exists() else None
    template = json.loads((SPEC_DIR / "EXP-001" / "spec.json").read_text(encoding="utf-8"))
    if project_id:
        _log(project_id, "data_steward", "tool_call", "describe_dataset → data contract, manifest, spec capabilities")
    return _ok(dataset=str(DATASET.relative_to(ROOT)), dataset_hash=_sha256(DATASET),
               data_contract=DATA_CONTRACT.read_text(encoding="utf-8"),
               manifest_summary={k: manifest.get(k) for k in (
                   "dataset_version", "row_count", "population_rules", "primary_outcomes", "missingness",
                   "survey_design_fields", "scientific_limitations", "experiment_readiness") if k in manifest},
               experiment_approval={k: approval.get(k) for k in ("status", "authority", "scope", "historical_manifest_note")
                                    if k in approval} if isinstance(approval, dict) else None,
               spec_capabilities=SPEC_CAPABILITIES, spec_template=template)


def save_proposals(project_id: str, hypothesis_id: str, candidates: list[dict]) -> str:
    """Store ≥2 competing candidate experiments. Feasible ones carry an ExperimentSpec that is dry-run checked.

    Candidate keys: label, title, question, hypothesis_codes, expected_information_gain, required_variables,
    contract_feasible, feasibility, cost, limitations, could_change_interpretation, spec (required if feasible).
    The Discovery Director selects one later with select_candidate.
    """
    if len(candidates) < 2:
        return _err("at least two candidate experiments are required")
    labels = [c.get("label") for c in candidates]
    if None in labels or len(set(labels)) != len(labels):
        return _err("every candidate needs a unique label")
    checks = {}
    for c in candidates:
        if not c.get("contract_feasible"):
            continue
        if not isinstance(c.get("spec"), dict):
            return _err(f"candidate {c['label']} is marked contract_feasible but has no spec")
        spec = {**c["spec"], "experiment_id": "EXP-000"}  # real id assigned when it runs
        check = _check_spec(spec)
        if not check.get("valid"):
            return _err(f"candidate {c['label']} spec failed the engine check; fix it or mark it infeasible",
                        check=check, spec_capabilities=SPEC_CAPABILITIES)
        checks[c["label"]] = check

    rows = client().table("experiment_proposals").insert([{
        "project_id": project_id,
        "hypothesis_id": hypothesis_id,
        "label": c["label"],
        "title": c.get("title") or c["label"],
        "protocol": ENGINE_METHOD if c.get("contract_feasible") else NEEDS_CONTRACT_REVISION,
        "description": "\n".join(filter(None, [c.get("question"),
                                               f"Could change interpretation: {c.get('could_change_interpretation')}"
                                               if c.get("could_change_interpretation") else None])),
        "learning_value": c.get("expected_information_gain"),
        "feasibility": c.get("feasibility"),
        "cost": c.get("cost"),
        "selected": False,
    } for c in candidates]).execute().data
    ids = {r["label"]: r["id"] for r in rows}
    stored = []
    for c in candidates:
        candidate = {**c, "proposal_id": ids[c["label"]], "hypothesis_id": hypothesis_id,
                     "engine_check": checks.get(c["label"])}
        _artifact(project_id, "candidates", ids[c["label"]], candidate)
        stored.append(candidate)
    _log(project_id, "experiment_planner", "output",
         f"Candidates {', '.join(labels)} proposed ({sum(bool(c.get('contract_feasible')) for c in candidates)} "
         "feasible within the current contract)",
         output_refs={"proposal_ids": ids, "candidates": stored})
    return _ok(proposal_ids=ids, engine_checks=checks)


def select_candidate(project_id: str, proposal_id: str, rationale: str, alternatives_considered: str,
                     based_on_run_id: str, rule_applied: str | None = None) -> str:
    """Discovery Director: choose the candidate with the highest expected learning and record why."""
    if rule_applied and rule_applied not in RULE_IDS:
        return _err(f"rule_applied must be one of {RULE_IDS}")
    candidate = _read_artifact(project_id, "candidates", proposal_id)
    if not candidate:
        return _err("proposal not found for this project")
    if not candidate.get("contract_feasible"):
        return _err("this candidate needs a revision of the engine contract (human approval); "
                    "select a contract-feasible one or request human review")
    db = client()
    db.table("experiment_proposals").update({"selected": True, "selection_rationale": rationale}) \
        .eq("id", proposal_id).eq("project_id", project_id).execute()
    if candidate.get("hypothesis_id"):
        db.table("hypotheses").update({"status": "testing"}).eq("id", candidate["hypothesis_id"]).execute()
    row = db.table("decisions").insert({
        "project_id": project_id,
        "experiment_run_id": based_on_run_id,
        "interpretation": f"Selected candidate {candidate['label']}: {candidate.get('title')}",
        "rule_applied": rule_applied,
        "next_test": candidate.get("question") or candidate.get("title"),
        "rationale": f"{rationale}\nAlternatives considered: {alternatives_considered}",
        "decided_by": "discovery_director",
    }).execute().data[0]
    decision = {"decision_id": row["id"], "type": "candidate_selection", "proposal_id": proposal_id,
                "label": candidate["label"], "rationale": rationale,
                "alternatives_considered": alternatives_considered, "based_on_run_id": based_on_run_id,
                "rule_applied": rule_applied, "spec": candidate.get("spec")}
    path = _artifact(project_id, "decisions", row["id"], decision)
    _log(project_id, "discovery_director", "decision",
         f"Selected {candidate['label']} ({candidate.get('title')}): {rationale}",
         output_refs={"decision": decision, "artifact": path}, experiment_run_id=based_on_run_id)
    return _ok(decision_id=row["id"], proposal_id=proposal_id, spec=candidate.get("spec"))


# --- Experiment execution ---------------------------------------------------

def run_experiment(project_id: str, proposal_id: str) -> str:
    """Run the selected candidate's stored ExperimentSpec through the deterministic engine. Requires approval.

    Assigns the next free EXP-NNN id, writes experiments/<id>/spec.json, runs scripts/run_experiment.py
    (two identical executions, dataset hash checked) and persists a compact result in experiment_runs.
    """
    candidate = _read_artifact(project_id, "candidates", proposal_id)
    db = client()
    proposal = db.table("experiment_proposals").select("*").eq("id", proposal_id) \
        .eq("project_id", project_id).maybe_single().execute()
    if not candidate or not proposal or not proposal.data:
        return _err("proposal not found for this project")
    if not proposal.data["selected"]:
        return _err("only the candidate selected by the Discovery Director can run")
    experiment_id = _next_experiment_id()
    spec = {**candidate["spec"], "experiment_id": experiment_id}
    spec_path = SPEC_DIR / experiment_id / "spec.json"
    spec_path.parent.mkdir(parents=True, exist_ok=False)
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    run = db.table("experiment_runs").insert({
        "project_id": project_id,
        "hypothesis_id": proposal.data["hypothesis_id"],
        "proposal_id": proposal_id,
        "protocol": spec["method"],
        "parameters": spec,
        "code_version": _code_version(),
        "dataset_hash": _sha256(DATASET),
        "status": "running",
        "started_at": _now(),
    }).execute().data[0]
    _log(project_id, "experiment_runner", "tool_call", f"run_experiment({experiment_id}) started",
         experiment_run_id=run["id"], input_refs={"proposal_id": proposal_id, "spec_path": str(spec_path)})

    error = None
    try:
        proc = _engine(["scripts/run_experiment.py", spec_path.relative_to(ROOT).as_posix()])
        if proc.returncode != 0:
            error = (proc.stderr or proc.stdout).strip()[-2000:]
    except Exception as exc:  # report the real failure to the agents and the panel
        error = f"{type(exc).__name__}: {exc}"
    if error is None:
        result, spec = _load_result(experiment_id)
        compact = _compact(result, spec)
        db.table("experiment_runs").update({
            "status": "succeeded",
            "results": _web_results(result, spec, compact),
            "sample_sizes": _sample_sizes(result),
            "artifact_paths": _artifacts(experiment_id),
            "finished_at": _now(),
        }).eq("id", run["id"]).execute()
        _log(project_id, "experiment_runner", "output",
             f"{experiment_id} completed: n={result['sample_size']}, ranking {result['ranking']['status']}",
             experiment_run_id=run["id"], output_refs={"experiment_id": experiment_id,
                                                       "artifacts": _artifacts(experiment_id)})
        return _ok(run_id=run["id"], experiment_id=experiment_id, status="succeeded", result=compact)

    db.table("experiment_runs").update({"status": "failed", "error": error, "finished_at": _now()}) \
        .eq("id", run["id"]).execute()
    _log(project_id, "experiment_runner", "error", f"{experiment_id} failed: {error[:300]}",
         experiment_run_id=run["id"])
    return _ok(run_id=run["id"], experiment_id=experiment_id, status="failed", error=error)


# --- Decision ---------------------------------------------------------------

def record_decision(project_id: str, experiment_run_id: str, interpretation: str, rule_applied: str,
                    next_test: str, rationale: str, uncertainty: str | None = None,
                    limitations: str | None = None, decided_by: str = "discovery_director",
                    hypothesis_id: str | None = None, hypothesis_status: str | None = None) -> str:
    """Store the updated decision after a critique; cites a real run and a pre-registered rule. Requires approval."""
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
    decision = {"decision_id": row["id"], "type": "updated_decision", "experiment_run_id": experiment_run_id,
                "interpretation": interpretation, "rule_applied": rule_applied, "next_test": next_test,
                "rationale": rationale, "uncertainty": uncertainty, "limitations": limitations,
                "hypothesis_id": hypothesis_id, "hypothesis_status": hypothesis_status, "decided_by": decided_by}
    path = _artifact(project_id, "decisions", row["id"], decision)
    _log(project_id, decided_by, "decision", f"{rule_applied}: {next_test}",
         output_refs={"decision": decision, "artifact": path}, experiment_run_id=experiment_run_id)
    return _ok(decision_id=row["id"], run_status=run.data["status"], artifact=path)
