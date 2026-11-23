# SOW Q&A Assistant: Retrieval-Augmented Generation

Ask questions about Statements of Work (PDF, Word, Markdown) and get short answers with
numbered citations back to the document, section and page. If the documents don't
contain the answer, it says so (`NOT_FOUND`) instead of guessing.

## How it works

```
 Indexing (once)                                Query (every question)
 ───────────────                                ──────────────────────
 PDF / DOCX / MD                                question
   │ pdfplumber, python-docx                      │
   ▼                                              ├──► BM25 keyword search  ──┐
 sections (heading-aware, page numbers)           ├──► FAISS vector search  ──┤ Reciprocal
   │ split long sections on sentences,            │    (BGE embeddings)       │ Rank Fusion
   │ 30-word overlap                              │                           ▼
   ▼                                              │              top 20 candidates
 chunks + contextual header                       │                           │ cross-encoder rerank
 "<doc title> > <section>"                        │                           ▼
   │                                              │                  top 5 chunks
   ├──► BGE embeddings ──► FAISS index            │                           │ numbered sources
   └──► BM25 index                                ▼                           ▼
                                               LLM (Claude API or local Ollama model)
                                                  │ answer with [n] citations, or NOT_FOUND
                                                  ▼
                                               citation check (cited ids must exist)
```

| Piece | File | Why |
|---|---|---|
| Section-aware chunking + contextual header | `rag/ingest.py` | A chunk that only says "The fixed fee is USD 268,000" can't be matched to "Helios's fee" unless the chunk carries its document and section name. |
| BM25 (own implementation) | `rag/bm25.py` | Exact terms such as amounts, codes (`ap-south-1`) and client names, which embeddings blur together. |
| FAISS + BGE embeddings | `rag/index.py` | Matches meaning: "uptime" ↔ "availability", "spending ceiling" ↔ "not-to-exceed cap". |
| Reciprocal Rank Fusion | `rag/index.py` | Merges the two rankings without calibrating BM25 scores against cosine scores. |
| Cross-encoder rerank | `rag/index.py` | Reads question and chunk together. More accurate than comparing vectors, but too slow for the whole corpus, so it runs only on the top 20. |
| Metadata filter | `rag/index.py` | Restrict a search to specific documents (`--doc helios_rfq_sow`). |
| Grounded prompt + citation validation | `rag/generate.py` | Answers only from sources and checks that every cited number refers to a real source. |

## Results

Corpus: 4 synthetic SOWs (fictional clients) in 3 formats that deliberately share the same
section structure with different values, so retrieval has to find the *right client's*
section. Eval set: 51 questions (43 answerable, 8 not answerable from the documents).

### Retrieval (`python cli.py eval --retrieval`)

| Chunking | Retrieval | Recall@1 | Recall@5 | MRR@10 |
|---|---|---|---|---|
| fixed 120-word windows | dense | 58.1% | 93.0% | 0.739 |
| fixed 120-word windows | hybrid + rerank | 69.8% | 97.7% | 0.816 |
| section, no header | dense | 48.8% | 79.1% | 0.639 |
| section + contextual header | bm25 | 83.7% | 97.7% | 0.901 |
| section + contextual header | dense | 88.4% | 100.0% | 0.931 |
| section + contextual header | hybrid | 88.4% | 100.0% | 0.942 |
| **section + contextual header** | **hybrid + rerank** | **97.7%** | **100.0%** | **0.988** |

Full matrix: `results/retrieval.md`.

Findings:
- **Contextual headers were the biggest win.** Section chunks *without* headers were worse
  than fixed windows (48.8% vs 58.1% R@1 dense), because a short section has no client name in it.
- **Hybrid alone did not improve Recall@1** over dense, but it raised Recall@5. The reranker then
  turned that better candidate pool into a better top 1 (88.4% → 97.7%).

### Generation (`python cli.py eval --generation --llm ollama`)

Local `gemma3` via Ollama, top-5 hybrid + rerank, temperature 0:

| Metric | Result |
|---|---|
| Answer accuracy (all gold facts in the answer) | 43 / 43 |
| Answers with valid citations | 43 / 43 |
| Correct `NOT_FOUND` on unanswerable questions | 7 / 8 |
| Average latency (CPU/GPU laptop) | 15.6 s / question |

The one failure: *"What is the warranty period after Helios go-live?"* was answered "three
years", taken from "three years of purchase order history". The model matched a number to
the question instead of the meaning. Possible fixes: a faithfulness check by a second LLM call,
or a reranker score threshold below which the system returns `NOT_FOUND` without asking the LLM.

Note: one answer ("Eleven percent") was first marked wrong by the string-matching grader. The
grader was fixed to accept number words, and the saved results were re-scored.

## Run it

```bash
pip install -r requirements.txt
python data/make_sample_docs.py          # render the sample SOWs to PDF / DOCX / MD
python cli.py index data/sample_sows
python cli.py ask "What uptime does Northwind's service need?"
python cli.py ask "What is the fee?" --doc helios_rfq_sow
python cli.py ask "..." --llm claude      # needs ANTHROPIC_API_KEY in .env
uvicorn api:app --reload                 # POST /ingest (file), POST /ask (JSON)
python -m pytest -q                      # 21 unit tests, no model downloads
```
