"""Fast unit tests (no model downloads, no LLM calls)."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag import index as index_mod  # noqa: E402
from rag.bm25 import BM25, tokenize  # noqa: E402
from rag.evaluate import fact_present  # noqa: E402
from rag.generate import NOT_FOUND, answer, build_prompt  # noqa: E402
from rag.index import Hit, RAGIndex, reciprocal_rank_fusion  # noqa: E402
from rag.ingest import (Block, _split_long, chunk_fixed, chunk_section_aware,  # noqa: E402
                        find_documents, load_document)

DOCS = ROOT / "data" / "sample_sows"


# ------------------------------------------------------------------ ingestion
@pytest.mark.parametrize("name", ["northwind_mutual_claims_sow.pdf", "asterix_bank_kyc_sow.docx",
                                  "crestline_health_invoices_sow.md"])
def test_loaders_find_title_and_ten_sections(name):
    title, blocks = load_document(DOCS / name)
    assert title.startswith("Statement of Work")
    assert len({b.section for b in blocks}) == 10


def test_pdf_title_wrapping_is_rejoined():
    title, _ = load_document(DOCS / "northwind_mutual_claims_sow.pdf")
    assert title.endswith("Northwind Mutual Insurance")


def test_pdf_blocks_keep_page_numbers():
    _, blocks = load_document(DOCS / "helios_rfq_sow.pdf")
    assert {b.page for b in blocks} == {1, 2}


def test_unsupported_extension_rejected(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("a,b")
    with pytest.raises(ValueError):
        load_document(p)


def test_contextual_header_only_in_embed_text():
    chunks = chunk_section_aware("d", "Acme SOW", [Block("Fee is USD 5.", "5. Fees")])
    assert chunks[0].embed_text.startswith("Acme SOW > 5. Fees")
    assert chunks[0].text == "Fee is USD 5."


def test_sections_spanning_pages_are_merged():
    blocks = [Block("Part one.", "2. Scope", 1), Block("Part two.", "2. Scope", 2)]
    chunks = chunk_section_aware("d", "T", blocks)
    assert len(chunks) == 1 and chunks[0].page == 1


def test_long_sections_split_on_sentences_with_overlap():
    text = " ".join(f"Sentence number {i} has five words." for i in range(40))
    pieces = _split_long(text, max_words=50, overlap_words=12)
    assert len(pieces) > 1
    assert all(len(p.split()) <= 50 for p in pieces)
    assert all(p.endswith(".") for p in pieces)
    assert pieces[0].split(". ")[-1] in pieces[1]  # overlap carried forward


def test_fixed_chunker_covers_all_words():
    blocks = [Block(" ".join(f"w{i}" for i in range(300)), "s")]
    chunks = chunk_fixed("d", "T", blocks, window=100, overlap=20)
    covered = {w for c in chunks for w in c.text.split()}
    assert covered == {f"w{i}" for i in range(300)}


# ------------------------------------------------------------------ retrieval
def test_bm25_prefers_exact_rare_terms():
    bm = BM25(["the fee is usd 268,000 for phase one", "hosted in ap-south-1 mumbai", "general text"])
    assert bm.top_k("which region ap-south-1", 1)[0][0] == 1
    assert "268,000" in tokenize("Fee: USD 268,000.")


def test_rrf_rewards_agreement_between_rankers():
    fused = reciprocal_rank_fusion([[1, 2, 3], [3, 1, 2]])
    assert fused[0][0] == 1  # ranked 1st and 2nd beats 3rd and 1st


@pytest.fixture
def toy_index(monkeypatch):
    """Index with a fake embedder so tests do not download models."""
    def fake_embed(texts, is_query=False):
        vocab = ["fee", "region", "logs", "helios", "northwind"]
        v = np.array([[t.lower().count(w) + 0.01 for w in vocab] for t in texts], dtype="float32")
        return v / np.linalg.norm(v, axis=1, keepdims=True)
    monkeypatch.setattr(index_mod, "embed", fake_embed)
    chunks = chunk_section_aware("helios", "Helios SOW", [Block("The fee is USD 1.", "Fees"),
                                                          Block("Logs kept 180 days.", "Security")])
    chunks += chunk_section_aware("northwind", "Northwind SOW", [Block("The fee is USD 2.", "Fees")])
    return RAGIndex(chunks)


def test_metadata_filter_restricts_documents(toy_index):
    hits = toy_index.search("fee", k=3, mode="hybrid", doc_ids={"northwind"})
    assert hits and all(h.chunk.doc_id == "northwind" for h in hits)


def test_index_round_trip(toy_index, tmp_path):
    toy_index.save(tmp_path)
    again = RAGIndex.load(tmp_path)
    assert [c.chunk_id for c in again.chunks] == [c.chunk_id for c in toy_index.chunks]


def test_unknown_mode_rejected(toy_index):
    with pytest.raises(ValueError):
        toy_index.search("fee", mode="magic")


# ------------------------------------------------------------------ generation
class FakeBackend:
    def __init__(self, reply):
        self.reply = reply

    def complete(self, system, user):
        self.user = user
        return self.reply, "fake"


def _hits():
    c = chunk_section_aware("h", "Helios SOW", [Block("Fee is USD 1.", "Fees")])[0]
    return [Hit(c, 1.0, 0)]


def test_prompt_numbers_sources_with_location():
    p = build_prompt("q?", _hits())
    assert "[1] (Helios SOW | Fees)" in p and "Question: q?" in p


def test_citations_parsed_and_validated():
    a = answer("q", _hits(), FakeBackend("It is USD 1 [1]. Also [4]."))
    assert a.citations == [1] and a.invalid_citations == [4] and not a.grounded


def test_refusal_detected():
    a = answer("q", _hits(), FakeBackend(NOT_FOUND))
    assert a.refused and a.grounded


def test_no_hits_short_circuits_without_llm_call():
    assert answer("q", [], FakeBackend("should not be used")).refused


def test_fact_matching_respects_word_boundaries_and_alternatives():
    assert fact_present("three|3", "up to 3 suppliers")
    assert not fact_present("15", "within 150 minutes")
    assert fact_present("412,000", "The fee is USD 412,000 [1].")


def test_sample_corpus_present():
    assert len(find_documents(DOCS)) == 4
