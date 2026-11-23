"""Embedding, FAISS vector index, hybrid retrieval and cross-encoder reranking."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np

from .bm25 import BM25
from .ingest import Chunk

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
# bge models expect this instruction on queries (not on passages)
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MODES = ("bm25", "dense", "hybrid", "hybrid_rerank")


@lru_cache(maxsize=2)
def _embedder(name: str = EMBED_MODEL):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name)


@lru_cache(maxsize=2)
def _reranker(name: str = RERANK_MODEL):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(name)


def embed(texts: list[str], is_query: bool = False) -> np.ndarray:
    if is_query:
        texts = [QUERY_PREFIX + t for t in texts]
    vecs = _embedder().encode(texts, batch_size=32, normalize_embeddings=True,
                              show_progress_bar=False)
    return np.asarray(vecs, dtype="float32")


@dataclass
class Hit:
    chunk: Chunk
    score: float
    rank: int


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """Merge ranked lists without having to calibrate BM25 vs cosine scores."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


class RAGIndex:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray | None = None):
        self.chunks = chunks
        texts = [c.embed_text or c.text for c in chunks]
        self.vectors = vectors if vectors is not None else embed(texts)
        # Inner product on L2-normalised vectors == cosine similarity.
        self.faiss = faiss.IndexFlatIP(self.vectors.shape[1])
        self.faiss.add(self.vectors)
        self.bm25 = BM25(texts)

    # ------------------------------------------------------------ persistence
    def save(self, folder: str | Path) -> None:
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "chunks.json").write_text(
            json.dumps([c.to_dict() for c in self.chunks], indent=1), encoding="utf-8")
        np.save(folder / "vectors.npy", self.vectors)
        (folder / "config.json").write_text(json.dumps({"embed_model": EMBED_MODEL}), encoding="utf-8")

    @classmethod
    def load(cls, folder: str | Path) -> "RAGIndex":
        folder = Path(folder)
        cfg = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        if cfg["embed_model"] != EMBED_MODEL:
            raise ValueError(f"index built with {cfg['embed_model']}, re-index for {EMBED_MODEL}")
        chunks = [Chunk(**d) for d in json.loads((folder / "chunks.json").read_text(encoding="utf-8"))]
        return cls(chunks, np.load(folder / "vectors.npy"))

    # ------------------------------------------------------------ retrieval
    def _allowed(self, doc_ids: set[str] | None) -> set[int] | None:
        if not doc_ids:
            return None
        return {i for i, c in enumerate(self.chunks) if c.doc_id in doc_ids}

    def _dense(self, query: str, n: int, allowed: set[int] | None) -> list[int]:
        q = embed([query], is_query=True)
        _, ids = self.faiss.search(q, len(self.chunks) if allowed else n)
        out = [int(i) for i in ids[0] if i >= 0 and (allowed is None or i in allowed)]
        return out[:n]

    def _sparse(self, query: str, n: int, allowed: set[int] | None) -> list[int]:
        ranked = self.bm25.top_k(query, len(self.chunks))
        return [i for i, _ in ranked if allowed is None or i in allowed][:n]

    def search(self, query: str, k: int = 5, mode: str = "hybrid_rerank",
               candidates: int = 20, doc_ids: set[str] | None = None) -> list[Hit]:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        allowed = self._allowed(doc_ids)

        if mode == "bm25":
            order = [(i, 1.0 / (r + 1)) for r, i in enumerate(self._sparse(query, k, allowed))]
        elif mode == "dense":
            order = [(i, 1.0 / (r + 1)) for r, i in enumerate(self._dense(query, k, allowed))]
        else:
            fused = reciprocal_rank_fusion([
                self._dense(query, candidates, allowed),
                self._sparse(query, candidates, allowed),
            ])
            if mode == "hybrid":
                order = fused[:k]
            else:
                pool = [i for i, _ in fused[:candidates]]
                scores = _reranker().predict(
                    [(query, self.chunks[i].embed_text or self.chunks[i].text) for i in pool])
                order = sorted(zip(pool, map(float, scores)), key=lambda x: x[1], reverse=True)[:k]

        return [Hit(self.chunks[i], s, r) for r, (i, s) in enumerate(order)]
