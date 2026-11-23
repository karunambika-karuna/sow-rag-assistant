"""Load PDF / DOCX / Markdown / TXT files into section-aware chunks.

Two chunking strategies are provided so their effect can be measured:

* ``fixed``     - naive sliding window of N words, no structure (the baseline).
* ``section``   - split on document headings, keep each section together where it
                  fits, split long sections on sentence boundaries with overlap, and
                  prepend a contextual header ("<doc title> > <section>") to every chunk.

The contextual header is what lets a chunk that only says "The fixed fee is
USD 268,000" be found for the question "What is Helios's fee?".
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pdfplumber
from docx import Document

HEADING_RE = re.compile(r"^\s*(\d{1,2}(\.\d+)*\.?)\s+[A-Z][^\n]{2,80}$")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


@dataclass
class Block:
    """A run of text with the structure it came from."""
    text: str
    section: str
    page: int | None = None


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    section: str
    page: int | None
    text: str                       # the raw chunk text shown to users / cited
    embed_text: str = ""            # what gets embedded and BM25-indexed
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- loaders

def _load_pdf(path: Path) -> tuple[str, list[Block]]:
    blocks: list[Block] = []
    title, section = "", "Preamble"
    with pdfplumber.open(path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            buf: list[str] = []
            for line in (page.extract_text() or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                if not title:
                    title = line
                    continue
                # A long PDF title wraps onto several lines before the first heading.
                if section == "Preamble" and not blocks and not buf and not HEADING_RE.match(line):
                    title = f"{title} {line}"
                    continue
                if HEADING_RE.match(line):
                    if buf:
                        blocks.append(Block(" ".join(buf), section, page_no))
                        buf = []
                    section = line
                else:
                    buf.append(line)
            if buf:
                blocks.append(Block(" ".join(buf), section, page_no))
    return title, blocks


def _load_docx(path: Path) -> tuple[str, list[Block]]:
    doc = Document(str(path))
    title, section, blocks = "", "Preamble", []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        style = (p.style.name or "").lower()
        if style == "title" and not title:
            title = text
        elif style.startswith("heading") or HEADING_RE.match(text):
            section = text
        else:
            blocks.append(Block(text, section))
    return title or path.stem, blocks


def _load_markdown(path: Path) -> tuple[str, list[Block]]:
    title, section, blocks, buf = "", "Preamble", [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            if buf:
                blocks.append(Block(" ".join(buf), section))
                buf = []
            if len(m.group(1)) == 1 and not title:
                title = m.group(2).strip()
            else:
                section = m.group(2).strip()
        elif line.strip():
            buf.append(line.strip())
    if buf:
        blocks.append(Block(" ".join(buf), section))
    return title or path.stem, blocks


LOADERS = {".pdf": _load_pdf, ".docx": _load_docx, ".md": _load_markdown, ".txt": _load_markdown}


def load_document(path: str | Path) -> tuple[str, list[Block]]:
    path = Path(path)
    try:
        loader = LOADERS[path.suffix.lower()]
    except KeyError:
        raise ValueError(f"Unsupported file type: {path.suffix}") from None
    return loader(path)


# ---------------------------------------------------------------- chunking

def _split_long(text: str, max_words: int, overlap_words: int) -> list[str]:
    """Split on sentence boundaries into pieces of <= max_words, with overlap."""
    sentences = SENTENCE_RE.split(text)
    pieces, cur = [], []
    for sent in sentences:
        if cur and len(" ".join(cur + [sent]).split()) > max_words:
            pieces.append(" ".join(cur))
            # carry trailing sentences forward as overlap
            tail, n = [], 0
            for s in reversed(cur):
                n += len(s.split())
                if n > overlap_words:
                    break
                tail.insert(0, s)
            cur = tail
        cur.append(sent)
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def chunk_section_aware(doc_id: str, title: str, blocks: list[Block],
                        max_words: int = 180, overlap_words: int = 30,
                        contextual_header: bool = True) -> list[Chunk]:
    # merge consecutive blocks of the same section (a section may span pages)
    merged: list[Block] = []
    for b in blocks:
        if merged and merged[-1].section == b.section:
            merged[-1].text += " " + b.text
        else:
            merged.append(Block(b.text, b.section, b.page))

    chunks = []
    for b in merged:
        for piece in _split_long(b.text, max_words, overlap_words):
            header = f"{title} > {b.section}\n" if contextual_header else ""
            chunks.append(Chunk(
                chunk_id=f"{doc_id}::{len(chunks):03d}", doc_id=doc_id, doc_title=title,
                section=b.section, page=b.page, text=piece, embed_text=header + piece,
            ))
    return chunks


def chunk_fixed(doc_id: str, title: str, blocks: list[Block],
                window: int = 120, overlap: int = 20) -> list[Chunk]:
    """Baseline: ignore structure, slide a fixed word window over the whole text."""
    words = " ".join(b.text for b in blocks).split()
    chunks, step = [], window - overlap
    for start in range(0, max(len(words) - overlap, 1), step):
        piece = " ".join(words[start:start + window])
        chunks.append(Chunk(
            chunk_id=f"{doc_id}::{len(chunks):03d}", doc_id=doc_id, doc_title=title,
            section="", page=None, text=piece, embed_text=piece,
        ))
    return chunks


def ingest_paths(paths: list[Path], strategy: str = "section", **kwargs) -> list[Chunk]:
    out: list[Chunk] = []
    for path in paths:
        title, blocks = load_document(path)
        doc_id = Path(path).stem
        if strategy == "fixed":
            out += chunk_fixed(doc_id, title, blocks, **kwargs)
        elif strategy == "section":
            out += chunk_section_aware(doc_id, title, blocks, **kwargs)
        else:
            raise ValueError(f"unknown chunking strategy {strategy!r}")
    return out


def find_documents(folder: str | Path) -> list[Path]:
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in LOADERS)
