import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.models import KnowledgeDocument, AuditEvent, generate_uuid
from backend.rag.retriever import PolicyRetriever
from backend.rag.ingestion_pipeline import KnowledgeIngestionPipeline
from backend.rag.manifest import ManifestManager
from backend.rag.discovery import SUPPORTED_EXTENSIONS
from backend.security.jwt_auth import get_current_user
from backend.security.rbac import check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge & Memory Layer (RAG)"])

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB limit
ALLOWED_UPLOAD_CATEGORIES = {
    "regulations",
    "aml_kyc",
    "fraud_patterns",
    "internal_policies",
    "research",
    "dataset_documentation",
    "markdown"
}

@router.get("/status")
def get_knowledge_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns high-level statistics and health of the knowledge base index and manifest.
    """
    check_permission(current_user["role"], "search_policies")
    manifest_mgr = ManifestManager()
    stats = manifest_mgr.get_summary_statistics()
    return {
        "status": "HEALTHY",
        "chroma_collection": "finguard_policies_and_typologies",
        "embedding_model": "all-MiniLM-L6-v2",
        "manifest": stats
    }

@router.get("/documents")
def list_knowledge_documents(
    category: Optional[str] = Query(None, description="Filter by category"),
    file_type: Optional[str] = Query(None, description="Filter by file type (PDF, MD, etc.)"),
    search: Optional[str] = Query(None, description="Search by title or filename"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns inventory of all indexed documents with page and chunk metrics.
    """
    check_permission(current_user["role"], "search_policies")
    manifest_mgr = ManifestManager()
    all_manifest_docs = manifest_mgr.get_all_documents()

    query = db.query(KnowledgeDocument)
    if category and category.lower() != "all":
        query = query.filter(KnowledgeDocument.category == category)
    docs = query.all()

    items = []
    for d in docs:
        manifest_meta = all_manifest_docs.get(d.doc_id, {})
        if not manifest_meta and d.metadata_json:
            try:
                manifest_meta = json.loads(d.metadata_json)
            except Exception:
                manifest_meta = {}

        ftype = manifest_meta.get("file_type", "MD")
        if file_type and file_type.lower() != "all" and ftype.upper() != file_type.upper():
            continue

        title_val = d.title
        fname_val = manifest_meta.get("file_name", d.doc_id)
        if search:
            s_low = search.lower()
            if s_low not in title_val.lower() and s_low not in fname_val.lower():
                continue

        items.append({
            "id": d.id,
            "doc_id": d.doc_id,
            "title": title_val,
            "category": d.category,
            "version": d.version,
            "chunk_count": d.chunk_count,
            "page_count": manifest_meta.get("page_count", 1),
            "character_count": manifest_meta.get("character_count", len(d.content or "")),
            "file_name": fname_val,
            "file_type": ftype,
            "file_size_bytes": manifest_meta.get("file_size_bytes", 0),
            "source_type": manifest_meta.get("source_type", "official_regulation"),
            "content_hash": manifest_meta.get("content_hash"),
            "status": manifest_meta.get("status", "INDEXED"),
            "ingested_at": d.ingested_at.isoformat() if d.ingested_at else None
        })

    return {
        "total": len(items),
        "items": items
    }

@router.get("/documents/{document_id}")
def get_knowledge_document_detail(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns full metadata, excerpt preview, and provenance for a specific document.
    """
    check_permission(current_user["role"], "search_policies")
    doc = db.query(KnowledgeDocument).filter_by(doc_id=document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found.")

    manifest_mgr = ManifestManager()
    manifest_meta = manifest_mgr.get_document(document_id) or {}
    if not manifest_meta and doc.metadata_json:
        try:
            manifest_meta = json.loads(doc.metadata_json)
        except Exception:
            manifest_meta = {}

    return {
        "id": doc.id,
        "doc_id": doc.doc_id,
        "title": doc.title,
        "category": doc.category,
        "version": doc.version,
        "chunk_count": doc.chunk_count,
        "content_preview": doc.content[:3500] if doc.content else "",
        "has_more_content": len(doc.content or "") > 3500,
        "total_characters": len(doc.content or ""),
        "metadata": manifest_meta,
        "ingested_at": doc.ingested_at.isoformat() if doc.ingested_at else None
    }

@router.post("/search")
def search_knowledge(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Executes grounded semantic search across the knowledge base with citations and synthesis.
    """
    check_permission(current_user["role"], "search_policies")
    query = payload.get("query", "").strip()
    top_k = int(payload.get("top_k", 4))
    category = payload.get("category")
    min_score = float(payload.get("min_relevance_score", 0.40))

    if not query or len(query) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters long.")

    response = PolicyRetriever.answer_question_grounded(
        query=query,
        top_k=top_k,
        category=category,
        min_relevance_score=min_score
    )

    return response.model_dump()

@router.post("/ingest")
def trigger_knowledge_ingest(
    payload: Optional[Dict[str, Any]] = Body(default={}),
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers incremental ingestion across all knowledge base directories.
    """
    check_permission(current_user["role"], "ingest_data")
    force_reindex = bool(payload.get("force_reindex", False) if payload else False)

    pipeline = KnowledgeIngestionPipeline()
    stats = pipeline.run_incremental_ingestion(force_reindex=force_reindex)
    return {
        "status": "SUCCESS",
        "details": stats
    }

@router.post("/reindex")
def trigger_document_reindex(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Forces safe re-indexing of a single specified document or all documents.
    """
    check_permission(current_user["role"], "ingest_data")
    doc_id = payload.get("doc_id")
    reindex_all = bool(payload.get("reindex_all", False))

    pipeline = KnowledgeIngestionPipeline()
    if reindex_all:
        stats = pipeline.run_incremental_ingestion(force_reindex=True)
        return {"status": "SUCCESS", "message": "All documents re-indexed successfully", "details": stats}
    elif doc_id:
        res = pipeline.reindex_document(doc_id)
        return {"status": "SUCCESS", "message": f"Document {doc_id} re-indexed", "details": res}
    else:
        raise HTTPException(status_code=400, detail="Must provide either 'doc_id' or 'reindex_all: true'.")

@router.delete("/documents/{document_id}")
def delete_knowledge_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Safely removes document vector chunks from ChromaDB and metadata records from database/manifest.
    Preserves original source document file on disk.
    """
    check_permission(current_user["role"], "ingest_data")
    pipeline = KnowledgeIngestionPipeline()
    success = pipeline.remove_document_index(document_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' could not be deleted.")

    # Audit log entry
    audit_ev = AuditEvent(
        correlation_id=generate_uuid(),
        actor_id=current_user["username"],
        actor_role=current_user["role"],
        action="KNOWLEDGE_DOCUMENT_UNINDEXED",
        target_type="DOCUMENT",
        target_id=document_id,
        outcome="SUCCESS",
        details_json=json.dumps({"action": "Vector chunks and metadata removed; source file preserved."})
    )
    db.add(audit_ev)
    db.commit()

    return {"status": "SUCCESS", "message": f"Document '{document_id}' removed from index. Source file preserved."}

@router.post("/upload")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    category: str = Form("regulations"),
    current_user: dict = Depends(get_current_user)
):
    """
    Uploads a supported document (.pdf, .md, .txt, .html, .csv, .docx)
    Validates file extension, size limit, and prevents directory traversal.
    Saves document in knowledge_base/<category> and triggers incremental ingestion.
    """
    check_permission(current_user["role"], "ingest_data")

    # 1. Validate Category
    target_category = category.lower().strip()
    if target_category not in ALLOWED_UPLOAD_CATEGORIES:
        target_category = "regulations"

    # 2. Validate Filename & Extension (Sanitize path traversal)
    raw_filename = os.path.basename(file.filename or "")
    if not raw_filename:
        raise HTTPException(status_code=400, detail="Missing or invalid filename.")

    # Prevent directory traversal attacks
    safe_filename = "".join(c for c in raw_filename if c.isalnum() or c in ("-", "_", ".")).strip()
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    # 3. Read and enforce size limit
    content_bytes = await file.read()
    if len(content_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum permissible upload limit of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
        )
    if len(content_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    # 4. Save to target category directory in knowledge_base
    dest_dir = os.path.abspath(os.path.join("knowledge_base", target_category))
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, safe_filename)

    with open(dest_path, "wb") as f:
        f.write(content_bytes)

    # 5. Automatically trigger incremental ingestion
    pipeline = KnowledgeIngestionPipeline()
    stats = pipeline.run_incremental_ingestion()

    return {
        "status": "SUCCESS",
        "message": f"File '{safe_filename}' uploaded to {target_category}/ and ingested.",
        "file_name": safe_filename,
        "category": target_category,
        "file_size_bytes": len(content_bytes),
        "ingestion_stats": stats
    }
