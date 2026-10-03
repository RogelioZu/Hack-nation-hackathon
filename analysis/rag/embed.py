"""Single embedding model for ingestion AND queries (must match vector(384) in the DB).

intfloat/multilingual-e5-small requires the "passage: " / "query: " prefixes.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"
DIMENSIONS = 384


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME, device="cpu")


def embed_passages(texts: list[str]) -> list[list[float]]:
    vectors = _model().encode([f"passage: {t}" for t in texts], normalize_embeddings=True, batch_size=32)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    return _model().encode(f"query: {text}", normalize_embeddings=True).tolist()
