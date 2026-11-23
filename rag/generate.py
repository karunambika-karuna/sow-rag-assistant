"""Grounded answer generation with numbered citations.

Backends:
  * ``claude`` - Anthropic Claude API (needs ANTHROPIC_API_KEY or an `ant auth login` profile)
  * ``ollama`` - a local model through Ollama (free, offline; default for the benchmark)
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from .index import Hit

NOT_FOUND = "NOT_FOUND"
CITE_RE = re.compile(r"\[(\d+)\]")

SYSTEM_PROMPT = f"""You answer questions about Statements of Work (SOWs) using ONLY the numbered
sources provided. Rules:
- Every factual sentence must end with the source number(s) it came from, like [2] or [1][3].
- Copy figures, dates and names exactly as written in the source.
- Sources can come from different clients' SOWs. Use only sources about the client the question asks about.
- If the sources do not contain the answer, reply with exactly {NOT_FOUND} and nothing else.
- Be concise: one to three sentences."""


def build_prompt(question: str, hits: list[Hit]) -> str:
    parts = []
    for n, h in enumerate(hits, start=1):
        c = h.chunk
        where = f"{c.doc_title} | {c.section}" + (f" | page {c.page}" if c.page else "")
        parts.append(f"[{n}] ({where})\n{c.text}")
    return "Sources:\n\n" + "\n\n".join(parts) + f"\n\nQuestion: {question}"


@dataclass
class Answer:
    text: str
    citations: list[int] = field(default_factory=list)
    invalid_citations: list[int] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    model: str = ""

    @property
    def refused(self) -> bool:
        return NOT_FOUND in self.text

    @property
    def grounded(self) -> bool:
        """Answered with at least one citation and no citation pointing at a missing source."""
        return self.refused or (bool(self.citations) and not self.invalid_citations)


class ClaudeBackend:
    def __init__(self, model: str = "claude-opus-5-5"):
        import anthropic
        self.client = anthropic.Anthropic()
        self.model = model

    def complete(self, system: str, user: str) -> tuple[str, str]:
        # Server-side fallback: if a safety classifier declines, the API retries on a
        # fallback model chosen by refusal category instead of returning an empty answer.
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system,
            output_config={"effort": "low"},  # short grounded answers: low effort is enough
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": user}],
        )
        if response.stop_reason == "refusal":
            return NOT_FOUND, response.model
        text = "".join(b.text for b in response.content if b.type == "text")
        return text.strip(), response.model


class OllamaBackend:
    def __init__(self, model: str = "gemma3"):
        import ollama
        self.ollama = ollama
        self.model = model

    def complete(self, system: str, user: str) -> tuple[str, str]:
        r = self.ollama.chat(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            options={"temperature": 0, "num_ctx": 8192},
        )
        return r["message"]["content"].strip(), f"ollama/{self.model}"


def make_backend(name: str | None = None, model: str | None = None):
    name = name or os.getenv("RAG_LLM", "ollama")
    if name == "claude":
        return ClaudeBackend(model or "claude-opus-5-5")
    if name == "ollama":
        return OllamaBackend(model or os.getenv("OLLAMA_MODEL", "gemma3"))
    raise ValueError(f"unknown backend {name!r}")


def answer(question: str, hits: list[Hit], backend) -> Answer:
    if not hits:
        return Answer(NOT_FOUND)
    text, model = backend.complete(SYSTEM_PROMPT, build_prompt(question, hits))
    cited = sorted({int(n) for n in CITE_RE.findall(text)})
    valid = [n for n in cited if 1 <= n <= len(hits)]
    return Answer(
        text=text,
        citations=valid,
        invalid_citations=[n for n in cited if n not in valid],
        sources=[{"n": n, "chunk_id": hits[n - 1].chunk.chunk_id, "doc": hits[n - 1].chunk.doc_title,
                  "section": hits[n - 1].chunk.section, "page": hits[n - 1].chunk.page}
                 for n in valid],
        model=model,
    )
