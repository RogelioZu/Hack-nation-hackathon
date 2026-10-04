"""Local tools for the Scientific Critic on a committed ExperimentResult (agents/scientific_critic.yaml).

Standard library only: no Supabase, embeddings or PDF parsing. The critic reads the published engine
artifacts under reports/experiments/<id>/ (never writes there) and stores its ScientificCritique as
reports/discovery/local/critiques/<critique_id>.json. Numbers only come from the engine artifact:
save_scientific_critique rejects decimal numbers that do not appear in it.
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
PROTOCOL = ROOT / "docs" / "EXPERIMENT_PROTOCOL.md"
CRITIQUE_DIR = ROOT / "reports" / "discovery" / "local" / "critiques"
CRITIC_SPEC = ROOT / "agents" / "scientific_critic.yaml"

STATUSES = ("VALID", "UNCERTAIN", "REQUIRES_REVISION", "REQUIRES_HUMAN_REVIEW")  # EXPERIMENT_PROTOCOL.md
EVIDENCE_KINDS = ("OBSERVED_EVIDENCE", "INFERENCE")
# Causal or definitive-ranking wording is not allowed in evidence statements (AGENTS.md §2).
CAUSAL = re.compile(r"\b(causes?|caused|causing|leads? to|results? in|reduces?|reduced|sacrific\w*|"
                    r"definitively|the most sacrificed|effect of commut\w*)\b", re.IGNORECASE)
DECIMAL = re.compile(r"[-−]?\d+\.\d+")


def _ok(**data: Any) -> str:
    return json.dumps({"ok": True, **data}, ensure_ascii=False, default=str)


def _err(message: str, **data: Any) -> str:
    return json.dumps({"ok": False, "error": message, **data}, ensure_ascii=False, default=str)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _untraceable(texts: list[str], allowed: set[float]) -> list[str]:
    """Decimal numbers in the critique that match no artifact value (rounded to the digits written)."""
    bad = []
    for text in texts:
        for token in DECIMAL.findall(text):
            number = float(token.replace("−", "-"))
            tolerance = 0.5 * 10 ** -len(token.split(".")[1])
            if not any(abs(abs(number) - abs(x)) <= tolerance + 1e-12 for x in allowed):
                bad.append(token)
    return bad


def _declared_executor() -> dict:
    """harness/model declared in the critic spec (read as text: no YAML dependency)."""
    text = CRITIC_SPEC.read_text(encoding="utf-8") if CRITIC_SPEC.exists() else ""
    return {key: (m.group(1) if (m := re.search(rf"^\s+{key}:\s*(\S+)", text, re.MULTILINE)) else None)
            for key in ("harness", "model")}


def _code_version() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def read_experiment_artifact(experiment_id: str = "EXP-001") -> str:
    """Critic-ready view of a committed ExperimentResult plus the pre-registered hypotheses H1-H4."""
    try:
        result_path, result, spec = _source(experiment_id)
    except (OSError, ValueError) as exc:
        return _err(str(exc))
    evaluated = {h["id"] for group in ("supported_hypotheses", "unsupported_hypotheses", "inconclusive_hypotheses")
                 for h in result.get(group, [])}
    return _ok(source_artifact=result_path.relative_to(ROOT).as_posix(), source_sha256=_sha256(result_path),
               dataset_version=result["dataset_version"],
               dataset_sha256=result["provenance"]["dataset_sha256"],
               result=_compact(result, spec),
               protocol_hypotheses=_protocol_hypotheses(),
               hypotheses_evaluated_by_engine=sorted(evaluated),
               note=("engine_candidate_next_experiments are unselected alternatives recorded by the engine; "
                     "the critic lists open questions but does not propose or choose the next experiment."))


def save_scientific_critique(experiment_id: str, scientific_status: str, status_rationale: str,
                             evidence_summary: list[dict], uncertainties: list[str], limitations: list[str],
                             unsupported_claims: list[str], untested_questions: list[str]) -> str:
    """Validate and store a ScientificCritique of a committed experiment; never overwrites."""
    try:
        result_path, result, spec = _source(experiment_id)
    except (OSError, ValueError) as exc:
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

    statements = [str(e["statement"]) for e in evidence_summary]
    causal = [s for s in statements if CAUSAL.search(s)]
    if causal:
        return _err("Causal or definitive-ranking wording in evidence_summary; use association language",
                    statements=causal)
    texts = [status_rationale, *statements, *uncertainties, *limitations, *unsupported_claims, *untested_questions]
    other_ids = sorted({i for t in texts for i in re.findall(r"EXP-\d{3,}", t)} - {experiment_id})
    if other_ids:
        return _err("The critique must not propose or reference other experiments", experiment_ids=other_ids)
    # Only what read_experiment_artifact shows (not the covariance matrices), so a made-up
    # number cannot pass by matching one of thousands of unrelated values.
    bad = _untraceable(texts, _numbers(_compact(result, spec)) | _numbers(spec) | _numbers(_protocol_hypotheses()))
    if bad:
        return _err("Numbers not found in the engine artifact; quote its values, never compute new ones",
                    numbers=sorted(set(bad)))

    CRITIQUE_DIR.mkdir(parents=True, exist_ok=True)
    n = 1 + sum(1 for _ in CRITIQUE_DIR.glob(f"CRIT-{experiment_id}-*.json"))
    critique_id = f"CRIT-{experiment_id}-{n:03d}"
    critique = {
        "critique_id": critique_id,
        "experiment_id": experiment_id,
        "scientific_status": scientific_status,
        "status_rationale": status_rationale,
        "evidence_summary": [{"kind": e["kind"], "statement": e["statement"], "source": e.get("source")}
                             for e in evidence_summary],
        "uncertainties": uncertainties,
        "limitations": limitations,
        "unsupported_claims": unsupported_claims,
        "untested_questions": [{"kind": "UNTESTED_QUESTION", "question": q} for q in untested_questions],
        "provenance": {
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
        },
    }
    path = CRITIQUE_DIR / f"{critique_id}.json"
    with path.open("x", encoding="utf-8", newline="\n") as f:  # "x": never overwrite
        f.write(json.dumps(critique, indent=2, ensure_ascii=False) + "\n")
    return _ok(critique_id=critique_id, artifact=path.relative_to(ROOT).as_posix())
