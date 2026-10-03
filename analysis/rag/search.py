"""search_evidence: hybrid (full-text + vector, RRF) retrieval with citation fields.

CLI: uv run python -m rag.search "weekly commute time and sleep" [-k 5]
"""

import argparse
import json

from pydantic import BaseModel

from db import client
from rag.embed import embed_query


class EvidenceHit(BaseModel):
    passage_id: str
    source_id: str
    source_title: str
    source_kind: str
    url: str | None
    doi: str | None
    section: str | None
    locator: str
    content: str
    score: float


def search_evidence(query: str, k: int = 5) -> list[EvidenceHit]:
    res = client().rpc(
        "hybrid_search",
        {"query_text": query, "query_embedding": embed_query(query), "match_count": k},
    ).execute()
    return [EvidenceHit(**row) for row in res.data]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    hits = search_evidence(args.query, args.k)
    print(json.dumps([h.model_dump() | {"content": h.content[:300]} for h in hits], indent=2, ensure_ascii=False))
