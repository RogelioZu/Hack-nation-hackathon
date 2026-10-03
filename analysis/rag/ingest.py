"""Ingest the RAG corpus: download → clean → chunk (keeping section + locator) → embed → upsert sources/passages.

CLI: uv run python -m rag.ingest [--manifest rag/corpus.json] [--dry-run]

Manifest entries: {kind, title, url, publisher?, year?, license?, doi?, path?, pages?, exclude_pages?, chunking?}
- `path` (repo-relative, .md/.txt/.pdf) is read locally; otherwise `url` is downloaded (PDF or text).
- `pages` / `exclude_pages` (PDF only, 1-based, e.g. "3-25" or "1-3,71") select the pages to ingest.
- `chunking`: "page" (default; sections come from the PDF bookmarks) or "question" (questionnaires:
  one passage per numbered question such as "5.9", under its "SECCIÓN …" heading).
- PDF text is cleaned first: repeated headers/footers, page numbers, interviewer instructions and
  dotted answer leaders ("Sí ....... 1" → "Sí = 1") are removed.
- Re-ingesting a source replaces its passages, so the run is idempotent.
- Only ingest full text when the license allows it; otherwise use title + abstract as content.
"""

import argparse
import hashlib
import io
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import httpx
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE = Path(__file__).resolve().parent.parent / ".cache"
CHUNK_CHARS = 1200
OVERLAP = 200

# Interviewer instructions and form scaffolding: meaningless once the page layout is gone.
# Skip logic ("PASE A 5.10", "FILTRO 5.9 …") is kept: it explains structural missing values.
INSTRUCTIONS = re.compile(
    r"(?:MUESTRE LA TARJETA \w+ AL INFORMANTE\s*)?(?:Y\s+)?(?:REGISTRE|CIRCULE)\b[A-ZÁÉÍÓÚÑ ,]*|"
    r"\bLEA\b[A-ZÁÉÍÓÚÑ ,]*|\b(?:HORAS|MINUT ?OS)\b|"
    r"de lunes a\s+sábado y|viernes\?\s+domingo\?|_{3,}"
)
DROP_LINE = re.compile(
    r"\d{1,3}|[IVXLC]+|[^\W\d_]|[\W_]*|(?:UN )?CÓDIGO(?: PARA CADA OPCIÓN)?|AFIRMATIVA\.?|OBTENER RESPUESTA|"
    r"(?:PRIMERA|SEGUNDA|TERCERA|CUARTA) PERSONA|"
    r"CATEGORÍAS VARIABLES CLASIFICACIONES|\(Continúa\)|O ?B ?S ?E ?R ?V ?A ?C ?I ?O ?N ?E ?S"
)
MIN_CHARS = {"page": 60, "question": 40}  # shorter chunks are lone headings or layout debris
LEADER_CODE = re.compile(r"\s*(?:\.\s?){4,}[\s.]*(\d{1,2})(?=\s|$)")  # "Sí ........ 1" → "Sí = 1"
QUESTION = re.compile(r"(\d\.\d{1,2})(?:\.\d)?[a-z]?\s")               # "5.9 ", "5.10a ", "6.2.1a "
SECTION = re.compile(r"SECCIÓN ([IVX]+)\.\s+(\S.+)")


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


def _page_set(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    pages: set[int] = set()
    for part in spec.split(","):
        lo, _, hi = part.strip().partition("-")
        pages.update(range(int(lo), int(hi or lo) + 1))
    return pages


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip().lower()


def _clean_line(line: str) -> str:
    line = INSTRUCTIONS.sub(" ", line)
    line = LEADER_CODE.sub(r" = \1", line)
    line = re.sub(r"(?:\.\s?){4,}", " ", line)       # leaders without an answer code
    line = re.sub(r"(?<!\S)[:.](?!\S)", " ", line)   # empty time boxes ":  .  :"
    line = re.sub(r"\s+", " ", line).strip()
    return "" if DROP_LINE.fullmatch(line) else line


def _pdf_pages(reader: PdfReader, entry: dict) -> list[tuple[int, list[str]]]:
    """[(page_no, cleaned lines)] for the selected pages, without repeated headers/footers."""
    keep, drop = _page_set(entry.get("pages")), _page_set(entry.get("exclude_pages")) or set()
    raw = []
    for page_no, page in enumerate(reader.pages, start=1):
        if (keep is None or page_no in keep) and page_no not in drop:
            text = unicodedata.normalize("NFKC", page.extract_text() or "")
            text = re.sub(r"(?<=[a-záéíóúñ])-[ \t]*\n[ \t]*(?=[a-záéíóúñ])", "", text)  # de-hyphenate
            raw.append((page_no, [l for l in text.splitlines() if l.strip()]))
    # A line seen at the top or bottom of many pages is a running header/footer.
    edges = Counter(_norm(l) for _, lines in raw for l in set(lines[:3] + lines[-3:]))
    boiler = {l for l, n in edges.items() if n >= max(3, 0.3 * len(raw))}
    return [(page_no, [c for l in lines if _norm(l) not in boiler and (c := _clean_line(l))])
            for page_no, lines in raw]


def _join(lines: list[str]) -> str:
    """Re-join lines wrapped by the PDF layout; keep breaks after sentences and before bullets/headings."""
    out = ""
    for line in lines:
        soft = out and not re.search(r"[.:;?!]$", out) and not re.match(r"[•»–-]|\d+(?:\.\d+)*\.?\s", line)
        out += (" " if soft else "\n" if out else "") + line
    return out


def _outline(reader: PdfReader) -> dict[int, list[tuple[str, str]]]:
    """{page_no: [(heading, "Parent › Heading"), …]} from the PDF bookmarks, in reading order."""
    starts: dict[int, list[tuple[str, str]]] = {}

    def walk(items: list, parents: list[str]) -> None:
        last = None
        for item in items:
            if isinstance(item, list):
                walk(item, parents + [last] if last else parents)
                continue
            last = item.title.strip()
            page_no = reader.get_destination_page_number(item) + 1
            starts.setdefault(page_no, []).append((last, " › ".join(parents + [last])))

    walk(reader.outline, [])
    return starts


def _page_chunks(reader: PdfReader, entry: dict) -> list[dict]:
    """Chunk each page, splitting it where a bookmarked heading starts so passages carry their section."""
    outline, section, out = _outline(reader), None, []
    for page_no, lines in _pdf_pages(reader, entry):
        headings = outline.get(page_no, [])
        found = [h for h in headings if any(_norm(l).startswith(_norm(h[0])[:25]) for l in lines)]
        for h in headings:
            if h not in found:  # heading text not on the page: the section starts at its top
                section = h[1]
        segments: list[tuple[str | None, list[str]]] = [(section, [])]
        for line in lines:
            hit = next((h for h in found if _norm(line).startswith(_norm(h[0])[:25])), None)
            if hit:
                found.remove(hit)
                section = hit[1]
                segments.append((section, []))
            segments[-1][1].append(line)
        n = 0
        for seg_section, seg_lines in segments:
            for chunk in _split(_join(seg_lines)):
                if len(chunk) < MIN_CHARS["page"]:
                    continue
                n += 1
                out.append({"section": seg_section, "locator": f"p. {page_no}" + (f" #{n}" if n > 1 else ""),
                            "content": chunk})
    return out


def _question_chunks(reader: PdfReader, entry: dict) -> list[dict]:
    """One passage per numbered question. Text before a page's first question (intros) joins the next one."""
    out: list[dict] = []
    section = None
    open_q: dict = {}  # {number, section, page, lines} of the question being collected

    def flush() -> None:
        if not open_q:
            return
        label = f"Pregunta {open_q['number']}"
        chunks = [c for c in _split("\n".join(open_q["lines"])) if len(c) >= MIN_CHARS["question"]]
        for i, chunk in enumerate(chunks):
            out.append({"section": f"{open_q['section']} › {label}" if open_q["section"] else label,
                        "locator": f"p. {open_q['page']} · {open_q['number']}" + (f" #{i + 1}" if i else ""),
                        "content": chunk})

    for page_no, lines in _pdf_pages(reader, entry):
        intro: list[str] | None = []  # lines before this page's first question; None once one is seen
        for line in lines:
            if m := SECTION.match(line):
                section = f"Sección {m[1]}. {m[2].capitalize()}"
                continue
            m = QUESTION.match(line + " ")
            if m and m[1] != open_q.get("number"):
                flush()
                open_q = {"number": m[1], "section": section, "page": page_no, "lines": (intro or []) + [line]}
                intro = None
            elif m or intro is None:  # sub-question ("6.4a") or body of the open question
                open_q["lines"].extend((intro or []) + [line])
                intro = None
            else:
                intro.append(line)
        if intro and open_q:  # page without a new question: its lines continue the open one
            open_q["lines"].extend(intro)
    flush()
    return out


def chunk_entry(entry: dict) -> list[dict]:
    """Return [{section, locator, content}] for one manifest entry."""
    data, ext = _load_bytes(entry)
    if ext == ".pdf":
        reader = PdfReader(io.BytesIO(data))
        return _question_chunks(reader, entry) if entry.get("chunking") == "question" else _page_chunks(reader, entry)
    out: list[dict] = []
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


def _dedupe_locators(passages: list[dict]) -> None:
    # Locators must be unique per source.
    seen: dict[str, int] = {}
    for p in passages:
        n = seen.get(p["locator"], 0)
        seen[p["locator"]] = n + 1
        if n:
            p["locator"] = f"{p['locator']} ({n + 1})"


def ingest(manifest: Path, dry_run: bool = False) -> None:
    for entry in json.loads(manifest.read_text()):
        passages = chunk_entry(entry)
        _dedupe_locators(passages)
        if dry_run:
            print(f"{entry['title']}: {len(passages)} passages (dry run)")
            continue
        from db import client  # heavy imports only when writing
        from rag.embed import embed_passages

        db = client()
        url = entry.get("url") or f"file://{entry['path']}"
        source = {k: entry.get(k) for k in ("kind", "title", "publisher", "year", "license", "doi")}
        source["url"] = url
        row = db.table("sources").upsert(source, on_conflict="url").execute().data[0]

        vectors = embed_passages([(p["section"] or "") + "\n" + p["content"] for p in passages])
        db.table("passages").delete().eq("source_id", row["id"]).execute()
        rows = [p | {"source_id": row["id"], "embedding": v} for p, v in zip(passages, vectors)]
        for i in range(0, len(rows), 100):
            db.table("passages").insert(rows[i : i + 100]).execute()
        print(f"{entry['title']}: {len(rows)} passages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parent / "corpus.json")
    parser.add_argument("--dry-run", action="store_true", help="chunk and count only; no embeddings, no DB writes")
    args = parser.parse_args()
    ingest(args.manifest, args.dry_run)
