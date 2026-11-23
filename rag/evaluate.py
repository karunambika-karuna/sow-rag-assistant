"""Benchmark retrieval and generation on data/eval_set.json.

Retrieval (no LLM needed): for every chunking strategy x retrieval mode, a question
counts as a hit at k if any of the top-k chunks contains the gold evidence span.
Reports Recall@1, Recall@5 and MRR@10.

Generation (needs an LLM backend): answer accuracy (all gold facts present),
citation validity (every answer cites a real source), and correct refusal rate
on questions the documents cannot answer.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .generate import answer
from .index import MODES, RAGIndex
from .ingest import ingest_paths

ROOT = Path(__file__).resolve().parent.parent


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def load_eval(path: Path = ROOT / "data" / "eval_set.json") -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def first_hit_rank(index: RAGIndex, item: dict, mode: str, k: int = 10) -> int | None:
    hits = index.search(item["q"], k=k, mode=mode)
    ev = _norm(item["evidence"])
    for h in hits:
        if ev in _norm(h.chunk.text):
            return h.rank + 1
    return None


def eval_retrieval(index: RAGIndex, items: list[dict], mode: str) -> dict:
    items = [i for i in items if not i.get("unanswerable")]
    ranks = [first_hit_rank(index, it, mode) for it in items]
    n = len(items)
    return {
        "recall@1": sum(r == 1 for r in ranks if r) / n,
        "recall@5": sum(r <= 5 for r in ranks if r) / n,
        "mrr@10": sum(1 / r for r in ranks if r) / n,
        "misses@5": [it["id"] for it, r in zip(items, ranks) if not r or r > 5],
    }


def fact_present(fact: str, text: str) -> bool:
    """A fact may list alternatives separated by '|'; any one matching counts."""
    t = _norm(text)
    return any(re.search(r"(?<![\w])" + re.escape(_norm(alt)) + r"(?![\w])", t)
               for alt in fact.split("|"))


def eval_generation(index: RAGIndex, items: list[dict], backend, k: int = 5,
                    mode: str = "hybrid_rerank") -> dict:
    rows = []
    for it in items:
        t0 = time.perf_counter()
        hits = index.search(it["q"], k=k, mode=mode)
        ans = answer(it["q"], hits, backend)
        row = {"id": it["id"], "q": it["q"], "answer": ans.text, "citations": ans.citations,
               "seconds": round(time.perf_counter() - t0, 2)}
        if it.get("unanswerable"):
            row["correct"] = ans.refused
        else:
            row["correct"] = not ans.refused and all(fact_present(f, ans.text) for f in it["facts"])
            row["cited_valid"] = bool(ans.citations) and not ans.invalid_citations
        rows.append(row)
        print(f"  {it['id']:6s} {'OK ' if row['correct'] else 'BAD'} {ans.text[:90]!r}")

    answerable = [r for r in rows if "cited_valid" in r]
    unanswerable = [r for r in rows if "cited_valid" not in r]
    return {
        "model": ans.model,
        "answer_accuracy": sum(r["correct"] for r in answerable) / len(answerable),
        "citation_validity": sum(r["cited_valid"] for r in answerable) / len(answerable),
        "refusal_accuracy": sum(r["correct"] for r in unanswerable) / max(len(unanswerable), 1),
        "avg_seconds": sum(r["seconds"] for r in rows) / len(rows),
        "rows": rows,
    }


def build_index(docs: list[Path], strategy: str, contextual_header: bool = True) -> RAGIndex:
    kwargs = {"contextual_header": contextual_header} if strategy == "section" else {}
    return RAGIndex(ingest_paths(docs, strategy=strategy, **kwargs))


def run_retrieval_matrix(docs: list[Path], items: list[dict]) -> list[dict]:
    configs = [
        ("fixed-120w", "fixed", False),
        ("section, no header", "section", False),
        ("section + contextual header", "section", True),
    ]
    results = []
    for label, strategy, header in configs:
        index = build_index(docs, strategy, header)
        for mode in MODES:
            r = eval_retrieval(index, items, mode)
            r.update({"chunking": label, "mode": mode, "chunks": len(index.chunks)})
            results.append(r)
            print(f"{label:30s} {mode:14s} R@1={r['recall@1']:.3f} R@5={r['recall@5']:.3f} "
                  f"MRR={r['mrr@10']:.3f}")
    return results


def markdown_table(results: list[dict]) -> str:
    lines = ["| Chunking | Retrieval | Chunks | Recall@1 | Recall@5 | MRR@10 |",
             "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['chunking']} | {r['mode']} | {r['chunks']} | {r['recall@1']:.1%} | "
                     f"{r['recall@5']:.1%} | {r['mrr@10']:.3f} |")
    return "\n".join(lines)
