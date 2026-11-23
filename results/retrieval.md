| Chunking | Retrieval | Chunks | Recall@1 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|
| fixed-120w | bm25 | 19 | 65.1% | 95.3% | 0.781 |
| fixed-120w | dense | 19 | 58.1% | 93.0% | 0.739 |
| fixed-120w | hybrid | 19 | 58.1% | 97.7% | 0.746 |
| fixed-120w | hybrid_rerank | 19 | 69.8% | 97.7% | 0.816 |
| section, no header | bm25 | 40 | 67.4% | 90.7% | 0.772 |
| section, no header | dense | 40 | 48.8% | 79.1% | 0.639 |
| section, no header | hybrid | 40 | 51.2% | 93.0% | 0.693 |
| section, no header | hybrid_rerank | 40 | 60.5% | 93.0% | 0.755 |
| section + contextual header | bm25 | 40 | 83.7% | 97.7% | 0.901 |
| section + contextual header | dense | 40 | 88.4% | 100.0% | 0.931 |
| section + contextual header | hybrid | 40 | 88.4% | 100.0% | 0.942 |
| section + contextual header | hybrid_rerank | 40 | 97.7% | 100.0% | 0.988 |
