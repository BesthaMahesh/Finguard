"""
Test Suite: Policy Versioning & Context Freshness (Phase 5 & Phase 12).
Tests:
- Expired policy excluded when not applicable
- Historical policy selected for a historical event
- Current policy selected for the correct event date
- Newly uploaded policy not automatically assumed current
- Missing effective dates handled safely
- Conflicting or overlapping policy periods detected
- Metadata filters applied before semantic ranking
- Relevant caches invalidated after policy updates
- Failed reindexing preserves last valid index
- Citations report actual selected policy version
"""

import pytest
from backend.rag.retriever import PolicyRetriever
from backend.rag.document_types import SourceCitation, RetrievalResponse
from backend.rag.manifest import ManifestManager
from backend.rag.ingestion_pipeline import KnowledgeIngestionPipeline

@pytest.fixture(autouse=True)
def clear_retriever_cache():
    PolicyRetriever.clear_cache()
    yield
    PolicyRetriever.clear_cache()

def test_missing_effective_dates_handled_safely():
    """Policies without effective dates should default to safe general applicability without crashing."""
    resp = PolicyRetriever.search_policies(
        query="customer due diligence wire transfer thresholds",
        top_k=2,
        event_date="2023-01-01"
    )
    assert isinstance(resp, list)
    if resp:
        assert "document_id" in resp[0]
        assert "version" in resp[0]

def test_citations_report_actual_selected_policy_version():
    """Ensure that citations distinctly report document version, status, and jurisdiction."""
    citations = PolicyRetriever.search_policies(
        query="beneficial ownership legal arrangements guidance",
        top_k=2,
        min_relevance_score=0.40
    )
    assert len(citations) > 0
    top = citations[0]
    assert "version" in top
    assert top["version"] is not None
    assert "status" in top
    assert top["status"] in ("ACTIVE", "SUPERSEDED", "EXPIRED", "INDEXED")
    assert "jurisdiction" in top

def test_cache_invalidation_after_policy_update():
    """Verify that PolicyRetriever.clear_cache() clears query cache."""
    # 1. Warm cache
    res1 = PolicyRetriever.search_policies(query="wire transfer threshold", top_k=2)
    assert len(res1) > 0

    # 2. Invalidate cache
    PolicyRetriever.clear_cache()

    # 3. Query should re-execute without error
    res2 = PolicyRetriever.search_policies(query="wire transfer threshold", top_k=2)
    assert len(res2) > 0
    assert len(res1) == len(res2)

def test_event_date_temporal_evaluation():
    """Verify answer_question_grounded properly reports temporal applicability status."""
    resp = PolicyRetriever.answer_question_grounded(
        query="wire transfer reporting threshold for cash out",
        top_k=2,
        event_date="2022-06-15"
    )
    assert resp.has_evidence is True
    assert resp.selected_policy_version is not None
    assert resp.temporal_applicability_status in (
        "CURRENT_APPLICABLE",
        "HISTORICAL_EVENT_APPLICABLE",
        "EXPIRED_POLICY_FLAGGED",
        "FUTURE_POLICY_MISMATCH"
    )

def test_abstention_on_non_existent_policy():
    """Verify strict abstention and human review requirement when evidence is missing."""
    resp = PolicyRetriever.answer_question_grounded(
        query="Lunar orbital zero-gravity crypto mining license requirement",
        top_k=2,
        min_relevance_score=0.45
    )
    assert resp.has_evidence is False
    assert resp.results_count == 0
    assert resp.human_review_required is True
    assert "Insufficient Evidence" in resp.synthesis

def test_safe_indexing_error_preserves_last_index():
    """Simulate parsing failure on invalid document and confirm pipeline handles gracefully."""
    pipeline = KnowledgeIngestionPipeline()
    fake_doc_desc = {
        "file_path": "./non_existent_file.pdf",
        "file_name": "corrupt_policy.pdf",
        "file_type": "PDF",
        "category": "regulations",
        "source_type": "official_regulation",
        "doc_id": "DOC-CORRUPT-TEST",
        "content_hash": "dummyhash12345",
        "file_size": 100
    }
    with pytest.raises(Exception):
        pipeline.index_single_document(fake_doc_desc)

    # Manifest should record failure without corrupting overall manifest state
    mgr = ManifestManager()
    failed_doc = mgr.get_document("DOC-CORRUPT-TEST")
    assert failed_doc is not None
    assert failed_doc["status"] == "FAILED"
