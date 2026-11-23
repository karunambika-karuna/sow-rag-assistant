"""A small, dependency-free Okapi BM25 implementation for keyword retrieval.

Keyword search catches exact terms that embeddings blur together: client names,
part numbers, amounts like "USD 268,000" or codes like "ap-south-1".
"""
from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-.,][a-z0-9]+)*")
STOPWORDS = frozenset(
    "a an and are as at be by for from has have how in is it its of on or that the this "
    "to was were what when where which who will with does do did".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


class BM25:
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(d)) for d in corpus]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avgdl = sum(self.lengths) / max(len(self.docs), 1)
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for doc, dl in zip(self.docs, self.lengths):
            s = 0.0
            for term in q:
                tf = doc.get(term)
                if tf:
                    s += self.idf[term] * tf * (self.k1 + 1) / (
                        tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out.append(s)
        return out

    def top_k(self, query: str, k: int) -> list[tuple[int, float]]:
        scored = sorted(enumerate(self.scores(query)), key=lambda x: x[1], reverse=True)
        return [(i, s) for i, s in scored[:k] if s > 0]
