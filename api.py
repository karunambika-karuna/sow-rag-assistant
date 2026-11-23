"""FastAPI service.

    uvicorn api:app --reload
    POST /ingest   (multipart file upload)  -> adds a document to the index
    POST /ask      {"question": "...", "k": 5, "doc_ids": ["helios_rfq_sow"]}
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

from rag.generate import answer, make_backend
from rag.index import MODES, RAGIndex
from rag.ingest import LOADERS, ingest_paths

ROOT = Path(__file__).resolve().parent
INDEX_DIR = ROOT / "index"
load_dotenv(ROOT / ".env")

app = FastAPI(title="SOW RAG Assistant")
state: dict = {"index": RAGIndex.load(INDEX_DIR) if (INDEX_DIR / "chunks.json").exists() else None,
               "backend": None}


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(5, ge=1, le=20)
    mode: str = "hybrid_rerank"
    doc_ids: list[str] | None = None


class Source(BaseModel):
    n: int
    chunk_id: str
    doc: str
    section: str
    page: int | None


class AskResponse(BaseModel):
    answer: str
    found: bool
    sources: list[Source]
    model: str


@app.post("/ingest")
async def ingest(file: UploadFile):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in LOADERS:
        raise HTTPException(400, f"Unsupported file type {suffix!r}; use {sorted(LOADERS)}")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / Path(file.filename).name
        with path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        new_chunks = ingest_paths([path])
    existing = state["index"].chunks if state["index"] else []
    keep = [c for c in existing if c.doc_id != path.stem]  # re-upload replaces the document
    state["index"] = RAGIndex(keep + new_chunks)
    state["index"].save(INDEX_DIR)
    return {"doc_id": path.stem, "chunks": len(new_chunks), "total_chunks": len(state["index"].chunks)}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    if state["index"] is None:
        raise HTTPException(409, "No documents indexed yet; POST /ingest first")
    if req.mode not in MODES:
        raise HTTPException(400, f"mode must be one of {MODES}")
    if state["backend"] is None:
        state["backend"] = make_backend()
    hits = state["index"].search(req.question, k=req.k, mode=req.mode,
                                 doc_ids=set(req.doc_ids) if req.doc_ids else None)
    ans = answer(req.question, hits, state["backend"])
    return AskResponse(answer=ans.text, found=not ans.refused,
                       sources=[Source(**s) for s in ans.sources], model=ans.model)
