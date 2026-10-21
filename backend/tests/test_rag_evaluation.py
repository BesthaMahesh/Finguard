"""
Test Suite: RAG Evaluation & Groundedness Benchmarks (Phase 12).
Evaluates:
- Retrieval Relevance
- Citation Correctness
- Evidence Sufficiency & Groundedness
- Abstention Quality on Out-of-Scope Prompts
- Traceability and Provenance Preservation
"""

import pytest
from backend.rag.retriever import PolicyRetriever
from backend.rag.document_types import RetrievalResponse

def test_rag_retrieval_relevance_benchmark():
    """Evaluate that top citations meet minimal relevance threshold and reference genuine documents."""
    citations = PolicyRetriever.search_policies(
        query="beneficial ownership legal arrangements guidance",
        top_k=3,
        min_relevance_score=0.40
    )
    assert len(citations) > 0
    for c in citations:
        assert c["relevance_score"] >= 0.40
        assert len(c["document_title"]) > 0
        assert c["source_file"].endswith((".pdf", ".md", ".txt"))

def test_rag_citation_correctness_and_provenance():
    """Evaluate that citations contain exact location provenance (page number or section)."""
    citations = PolicyRetriever.search_policies(
        query="wire transfer rapid cash out suspicious pattern",
        top_k=2,
        min_relevance_score=0.35
    )
    assert len(citations) > 0
    top = citations[0]
    assert "citation_location" in top
    assert len(top["citation_location"]) > 5
    assert top["version"] is not None

def test_rag_abstention_and_evidence_sufficiency():
    """Verify that unsupported claims are never fabricated when evidence is insufficient."""
    unsupported_query = "Automated Martian crypto asteroid mining export certificate"
    resp: RetrievalResponse = PolicyRetriever.answer_question_grounded(
        query=unsupported_query,
        top_k=2,
        min_relevance_score=0.45
    )
    # The system must explicitly abstain
    assert resp.has_evidence is False
    assert resp.results_count == 0
    assert "Insufficient Evidence" in resp.synthesis
    assert resp.human_review_required is True

def test_rag_grounded_synthesis_citations():
    """Verify that when evidence is found, synthesis references sources or provides grounded excerpt."""
    query = "four eyes principle in fraud investigations"
    resp: RetrievalResponse = PolicyRetriever.answer_question_grounded(
        query=query,
        top_k=2,
        min_relevance_score=0.40
    )
    assert resp.has_evidence is True
    assert resp.results_count > 0
    assert len(resp.citations) > 0
    assert resp.synthesis is not None
    assert len(resp.synthesis) > 20
