"""Retrieval QA: fixed queries with expected evidence → hit@1, hit@k, MRR and form-noise share.

CLI: uv run python -m rag.eval [-k 5] [--queries rag/eval_queries.json]

A hit is relevant when its section/content contains one of `expect_any` (accent- and case-insensitive)
and, if given, its source has the expected `kind`. Matching by text instead of passage id keeps the
eval valid across re-ingestions.
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path

from rag.search import search_evidence

# Questionnaire form residue ("REGISTRE CON NÚMERO", dotted answer leaders) that pollutes passages.
NOISE = re.compile(r"REGISTRE|CIRCULE|\.{6,}")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c)))


def evaluate(queries: list[dict], k: int) -> dict:
    rows = []
    for q in queries:
        hits = search_evidence(q["query"], k)
        expected = [_norm(e) for e in q["expect_any"]]
        rank = next((i for i, h in enumerate(hits, start=1)
                     if (not q.get("kind") or h.source_kind == q["kind"])
                     and any(e in _norm(f"{h.section or ''} {h.content}") for e in expected)), None)
        noise = sum(bool(NOISE.search(h.content)) for h in hits)
        rows.append({"query": q["query"], "rank": rank, "noise": noise, "n": len(hits),
                     "top": f"{hits[0].source_kind} {hits[0].locator}" if hits else "-"})
    n = len(rows)
    return {
        "rows": rows,
        "hit@1": sum(r["rank"] == 1 for r in rows) / n,
        f"hit@{k}": sum(r["rank"] is not None for r in rows) / n,
        "mrr": sum(1 / r["rank"] for r in rows if r["rank"]) / n,
        "noise_share": sum(r["noise"] for r in rows) / max(1, sum(r["n"] for r in rows)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--queries", type=Path, default=Path(__file__).resolve().parent / "eval_queries.json")
    args = parser.parse_args()
    report = evaluate(json.loads(args.queries.read_text()), args.k)
    for r in report.pop("rows"):
        print(f"{str(r['rank'] or '✗'):>2}  noise {r['noise']}/{r['n']}  top: {r['top']:<34} {r['query']}")
    print(json.dumps({key: round(v, 3) for key, v in report.items()}))
