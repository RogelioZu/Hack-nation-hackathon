"""search_evidence: hybrid (full-text + vector, RRF) retrieval with citation fields.

CLI: uv run python -m rag.search "weekly commute time and sleep" [-k 5]
"""

import argparse
import json
import re

from pydantic import BaseModel

from db import client
from rag.embed import embed_query

# English → Spanish domain terms. The corpus is Spanish: the Spanish full-text index cannot match
# English words and e5's cross-lingual matching is weak on short queries, so English terms found in
# the query get their Spanish equivalents appended. Spanish queries pass through unchanged.
GLOSSARY = {
    "commute": "traslado al trabajo", "commuting": "traslado al trabajo", "travel time": "tiempo de traslado",
    "sleep": "dormir", "sleeping": "dormir", "personal care": "cuidados personales", "eating": "comer",
    "meals": "comer alimentos", "care": "cuidados", "caregiving": "cuidados", "passive care": "cuidado pasivo",
    "household members": "integrantes del hogar", "household": "hogar", "children": "niñas y niños",
    "family": "convivencia familiar", "social": "convivencia social", "friends": "amistades",
    "leisure": "tiempo libre", "free time": "tiempo libre", "weekly": "semanal", "week": "semana",
    "reference week": "semana de referencia", "time use": "uso del tiempo", "simultaneous": "simultáneas",
    "work": "trabajo", "job": "trabajo", "employed": "población ocupada", "working hours": "horas de trabajo",
    "remote": "virtual a distancia", "telework": "virtual a distancia", "unpaid work": "trabajo no remunerado",
    "housework": "trabajo doméstico", "domestic work": "trabajo doméstico",
    "women": "mujeres", "men": "hombres", "sex": "sexo", "gender": "sexo",
    "sampling": "muestreo", "sampling design": "diseño muestral", "weight": "ponderador",
    "weights": "ponderadores factor de expansión", "expansion factor": "factor de expansión",
    "strata": "estratos", "stratum": "estrato", "primary sampling unit": "unidad primaria de muestreo UPM",
    "variance": "varianza", "confidence interval": "intervalo de confianza", "standard error": "error estándar",
    "questionnaire": "cuestionario", "question": "pregunta", "age": "edad",
    "mexico city": "Ciudad de México", "state of mexico": "Estado de México",
}


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


def expand_query(query: str) -> str:
    q = query.lower()
    extra = [es for en, es in GLOSSARY.items() if re.search(rf"\b{re.escape(en)}\b", q)]
    return f"{query} ({'; '.join(dict.fromkeys(extra))})" if extra else query


def search_evidence(query: str, k: int = 5) -> list[EvidenceHit]:
    text = expand_query(query)
    res = client().rpc(
        "hybrid_search",
        {"query_text": text, "query_embedding": embed_query(text), "match_count": k},
    ).execute()
    return [EvidenceHit(**row) for row in res.data]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    hits = search_evidence(args.query, args.k)
    print(json.dumps([h.model_dump() | {"content": h.content[:300]} for h in hits], indent=2, ensure_ascii=False))
