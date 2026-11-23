"""Command line entry point.

    python cli.py index  data/sample_sows            # build ./index
    python cli.py ask    "What is Helios's fee for phase 2?"
    python cli.py eval   --retrieval                 # chunking x retrieval matrix (no LLM)
    python cli.py eval   --generation --llm ollama   # end-to-end answers with a local model
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from rag.evaluate import (ROOT, build_index, eval_generation, load_eval, markdown_table,
                          run_retrieval_matrix)
from rag.generate import answer, make_backend
from rag.index import RAGIndex
from rag.ingest import find_documents, ingest_paths

INDEX_DIR = ROOT / "index"
RESULTS_DIR = ROOT / "results"


def cmd_index(args):
    docs = find_documents(args.folder)
    chunks = ingest_paths(docs, strategy="section")
    RAGIndex(chunks).save(INDEX_DIR)
    print(f"Indexed {len(docs)} documents into {len(chunks)} chunks -> {INDEX_DIR}")


def cmd_ask(args):
    index = RAGIndex.load(INDEX_DIR)
    hits = index.search(args.question, k=args.k, mode=args.mode,
                        doc_ids=set(args.doc) if args.doc else None)
    ans = answer(args.question, hits, make_backend(args.llm, args.model))
    print("\n" + ans.text + "\n")
    for s in ans.sources:
        print(f"  [{s['n']}] {s['doc']} | {s['section']}" + (f" | p.{s['page']}" if s["page"] else ""))
    if ans.invalid_citations:
        print(f"  WARNING: cited missing sources {ans.invalid_citations}")


def cmd_eval(args):
    docs = find_documents(ROOT / "data" / "sample_sows")
    items = load_eval()
    RESULTS_DIR.mkdir(exist_ok=True)
    if args.retrieval:
        results = run_retrieval_matrix(docs, items)
        (RESULTS_DIR / "retrieval.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
        (RESULTS_DIR / "retrieval.md").write_text(markdown_table(results) + "\n", encoding="utf-8")
        print("\n" + markdown_table(results))
    if args.generation:
        index = build_index(docs, "section", True)
        res = eval_generation(index, items, make_backend(args.llm, args.model), k=args.k)
        name = res["model"].replace("/", "_").replace(":", "_")
        (RESULTS_DIR / f"generation_{name}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
        print(f"\n{res['model']}: answer accuracy {res['answer_accuracy']:.1%}, "
              f"citation validity {res['citation_validity']:.1%}, "
              f"refusal accuracy {res['refusal_accuracy']:.1%}, avg {res['avg_seconds']:.1f}s/question")


def main():
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser(description="SOW RAG Assistant")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("index"); s.add_argument("folder", type=Path); s.set_defaults(fn=cmd_index)

    s = sub.add_parser("ask"); s.add_argument("question")
    s.add_argument("--k", type=int, default=5)
    s.add_argument("--mode", default="hybrid_rerank")
    s.add_argument("--doc", action="append", help="restrict to a document id (repeatable)")
    s.add_argument("--llm", choices=["ollama", "claude"]); s.add_argument("--model")
    s.set_defaults(fn=cmd_ask)

    s = sub.add_parser("eval")
    s.add_argument("--retrieval", action="store_true"); s.add_argument("--generation", action="store_true")
    s.add_argument("--k", type=int, default=5)
    s.add_argument("--llm", choices=["ollama", "claude"]); s.add_argument("--model")
    s.set_defaults(fn=cmd_eval)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
