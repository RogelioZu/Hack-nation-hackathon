"""Ingest the RAG corpus: download → chunk (keeping a locator) → embed → upsert sources/passages.

CLI: uv run python -m rag.ingest [--manifest rag/corpus.json]

Manifest entries: {kind, title, url, publisher?, year?, license?, doi?, path?}
- `path` (repo-relative, .md/.txt/.pdf) is read locally; otherwise `url` is downloaded (PDF or text).
- Re-ingesting a source replaces its passages, so the run is idempotent.
- Only ingest full text when the license allows it; otherwise use title + abstract as content.
"""

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

import httpx
from pypdf import PdfReader

from db import client
from rag.embed import embed_passages

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE = Path(__file__).resolve().parent.parent / ".cache"
CHUNK_CHARS = 1200
OVERLAP = 200


def _split(text: str) -> list[str]:
    text = re.sub(r"[ \t]+", " ", text).strip()
    if len(text) <= CHUNK_CHARS:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        # Prefer to cut at a paragraph or sentence boundary.
        cut = max(text.rfind("\n\n", start, end), text.rfind(". ", start, end))
        if end < len(text) and cut > start + CHUNK_CHARS // 2:
            end = cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - OVERLAP
    return [c for c in chunks if c]


def _load_bytes(entry: dict) -> tuple[bytes, str]:
    if entry.get("path"):
        p = ROOT / entry["path"]
        return p.read_bytes(), p.suffix.lower()
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / hashlib.sha1(entry["url"].encode()).hexdigest()
    if not cached.exists():
        r = httpx.get(entry["url"], follow_redirects=True, timeout=120)
        r.raise_for_status()
        cached.write_bytes(r.content)
    data = cached.read_bytes()
    return data, ".pdf" if data[:4] == b"%PDF" else ".txt"


def chunk_entry(entry: dict) -> list[dict]:
    """Return [{section, locator, content}] for one manifest entry."""
    data, ext = _load_bytes(entry)
    out: list[dict] = []
    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        for page_no, page in enumerate(reader.pages, start=1):
            for i, chunk in enumerate(_split(page.extract_text() or "")):
                out.append({"section": None, "locator": f"p. {page_no}" + (f" #{i + 1}" if i else ""), "content": chunk})
    else:
        text = data.decode("utf-8", errors="replace")
        # Split markdown by headings so each passage keeps its section title.
        parts = re.split(r"(?m)^(#{1,4} .+)$", text)
        section = None
        for part in parts:
            if re.match(r"^#{1,4} ", part):
                section = part.lstrip("#").strip()
                continue
            for i, chunk in enumerate(_split(part)):
                out.append({"section": section, "locator": f"{section or 'body'} #{i + 1}", "content": chunk})
    return out


def ingest(manifest: Path) -> None:
    db = client()
    for entry in json.loads(manifest.read_text()):
        url = entry.get("url") or f"file://{entry['path']}"
        source = {k: entry.get(k) for k in ("kind", "title", "publisher", "year", "license", "doi")}
        source["url"] = url
        row = db.table("sources").upsert(source, on_conflict="url").execute().data[0]

        passages = chunk_entry(entry)
        # Locators must be unique per source.
        seen: dict[str, int] = {}
        for p in passages:
            n = seen.get(p["locator"], 0)
            seen[p["locator"]] = n + 1
            if n:
                p["locator"] = f"{p['locator']} ({n + 1})"

        vectors = embed_passages([(p["section"] or "") + "\n" + p["content"] for p in passages])
        db.table("passages").delete().eq("source_id", row["id"]).execute()
        rows = [p | {"source_id": row["id"], "embedding": v} for p, v in zip(passages, vectors)]
        for i in range(0, len(rows), 100):
            db.table("passages").insert(rows[i : i + 100]).execute()
        print(f"{entry['title']}: {len(rows)} passages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parent / "corpus.json")
    ingest(parser.parse_args().manifest)
