import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.rag.loaders.pdf_loader import PDFLoader, PDFExtractionError
from backend.rag.loaders.markdown_loader import MarkdownLoader, MarkdownExtractionError
from backend.rag.discovery import discover_documents, calculate_file_hash
from backend.rag.chunker import DocumentChunker
from backend.rag.manifest import ManifestManager
from backend.rag.retriever import PolicyRetriever
from backend.agents.policy_compliance import policy_compliance_agent
from backend.agents.investigator import investigation_agent
from backend.agents.agent_state import InvestigationState
from backend.security.jwt_auth import create_access_token

@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "admin", "role": "administrator", "user_id": "usr-adm-004"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def analyst_headers():
    token = create_access_token({"sub": "analyst", "role": "analyst", "user_id": "usr-analyst-001"})
    return {"Authorization": f"Bearer {token}"}

def test_pdf_loader_real_document():
    pdf_path = os.path.join("knowledge_base", "research", "ftfe2.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("ftfe2.pdf not found")

    res = PDFLoader.load_pdf(pdf_path)
    assert res["total_pages"] == 54
    assert res["total_characters"] > 100000
    assert len(res["pages"]) == 54
    assert res["pages"][0]["page_number"] == 1
    assert "BENEFICIAL OWNERSHIP" in res["pages"][0]["text"].upper()

def test_pdf_loader_error_handling():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"")
        empty_path = f.name

    try:
        with pytest.raises(PDFExtractionError):
            PDFLoader.load_pdf(empty_path)
    finally:
        os.remove(empty_path)

def test_markdown_loader_with_frontmatter():
    sample_md = os.path.join("knowledge_base", "internal_policies", "sample_transaction_fraud_investigation_procedure.md")
    if not os.path.exists(sample_md):
        pytest.skip("sample policy not found")

    res = MarkdownLoader.load_markdown(sample_md)
    assert "Transaction Fraud Investigation Procedure" in res["title"]
    assert res["frontmatter"].get("category") == "fraud_patterns"
    assert res["frontmatter"].get("source_type") == "sample_internal_policy"
    assert len(res["sections"]) >= 4

def test_discovery_and_hashing():
    discovered = discover_documents(["./knowledge_base"])
    assert len(discovered) >= 8

    pdf_docs = [d for d in discovered if d["file_type"] == "PDF"]
    assert len(pdf_docs) >= 3

    for d in discovered:
        assert len(d["content_hash"]) == 64
        assert d["file_type"] in ["PDF", "MD", "TXT", "CSV"]
        assert d["source_type"] in ["official_regulation", "sample_internal_policy", "research", "dataset_documentation"]

def test_chunker_page_provenance():
    chunker = DocumentChunker(target_chunk_size=500, chunk_overlap=50)
    mock_pages = [
        {"page_number": 1, "text": "This is page 1 content covering AML thresholds and customer verification."},
        {"page_number": 2, "text": "This is page 2 content detailing enhanced due diligence protocols."}
    ]
    chunks = chunker.chunk_pdf_pages(
        doc_id="test-doc",
        title="Test PDF",
        filename="test.pdf",
        category="regulations",
        source_type="official_regulation",
        pages=mock_pages
    )
    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[0].section == "Page 1"
    assert chunks[1].page_number == 2
    assert chunks[1].section == "Page 2"

def test_manifest_idempotency():
    manifest_mgr = ManifestManager()
    stats = manifest_mgr.get_summary_statistics()
    assert stats["total_indexed"] >= 8
    assert stats["total_chunks"] >= 800

def test_policy_retriever_semantic_search():
    citations = PolicyRetriever.search_policies(
        query="beneficial ownership legal arrangements guidance",
        top_k=2,
        min_relevance_score=0.45
    )
    assert len(citations) > 0
    top = citations[0]
    assert "ftfe2.pdf" in top["source_file"].lower() or "fattdata.pdf" in top["source_file"].lower()
    assert top["relevance_score"] >= 0.45
    assert top["page_number"] is not None

def test_policy_retriever_insufficient_evidence():
    resp = PolicyRetriever.answer_question_grounded(
        query="Subterranean Martian gold smelting import export license",
        top_k=2,
        min_relevance_score=0.45
    )
    assert resp.has_evidence is False
    assert resp.results_count == 0
    assert "Insufficient Evidence" in resp.synthesis

def test_api_endpoints_knowledge_status_and_documents(auth_headers):
    client = TestClient(app)
    # GET /status
    r_stat = client.get("/api/v1/knowledge/status", headers=auth_headers)
    assert r_stat.status_code == 200
    assert r_stat.json()["status"] == "HEALTHY"

    # GET /documents
    r_docs = client.get("/api/v1/knowledge/documents", headers=auth_headers)
    assert r_docs.status_code == 200
    assert r_docs.json()["total"] >= 8

def test_api_endpoints_search_query(auth_headers):
    client = TestClient(app)
    r_search = client.post("/api/v1/knowledge/search", headers=auth_headers, json={
        "query": "wire transfer thresholds customer due diligence",
        "top_k": 2
    })
    assert r_search.status_code == 200
    data = r_search.json()
    assert data["has_evidence"] is True
    assert len(data["citations"]) > 0

def test_langgraph_policy_agent_integration():
    state: InvestigationState = {
        "correlation_id": "test-trace-001",
        "transaction_id": 1,
        "raw_transaction_data": {"type": "TRANSFER", "amount": 250000},
        "user_query": None,
        "current_user_role": "investigator",
        "intake_status": "VALIDATED",
        "validated_transaction": {"type": "TRANSFER", "amount": 250000, "nameOrig": "C1234", "nameDest": "C5678"},
        "data_quality_report": {},
        "model_prediction": {},
        "risk_assessment": {"composite_risk_score": 75.0},
        "investigation_evidence": {},
        "policy_citations": [],
        "explanation_summary": "",
        "feature_attributions": [],
        "workflow_next_step": "POLICY",
        "requires_human_review": True,
        "review_checkpoint_reason": None,
        "final_report": {},
        "timeline": [],
        "tokens_consumed": 0,
        "error": None
    }
    updated_state = policy_compliance_agent(state)
    assert len(updated_state["policy_citations"]) > 0
    assert any(step["agent"] == "Policy & Compliance Agent" for step in updated_state["timeline"])
