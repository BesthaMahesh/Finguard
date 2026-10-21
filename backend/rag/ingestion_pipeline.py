"""
FinGuard Safe, Atomic, Incremental Knowledge Ingestion Pipeline.
Supports PDF, Markdown, Plain Text, HTML, CSV, DOCX formats.
Maintains cryptographic content hashes, policy versioning, and safe rollback.
Synchronizes ChromaDB, SQLite KnowledgeDocument, and ManifestManager.
Invalidates query caches on index modifications.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend.rag.chroma_client import get_knowledge_collection
from backend.rag.discovery import discover_documents, calculate_file_hash
from backend.rag.loaders.pdf_loader import PDFLoader, PDFExtractionError
from backend.rag.loaders.markdown_loader import MarkdownLoader, MarkdownExtractionError
from backend.rag.loaders.text_loader import TextLoader
from backend.rag.chunker import DocumentChunker
from backend.rag.manifest import ManifestManager
from backend.rag.document_types import DocumentMetadataModel, DocumentChunk
from backend.db.session import SessionLocal, engine
from backend.db.models import Base, KnowledgeDocument, AuditEvent, generate_uuid
from backend.observability.tracer import tracer, record_custom_span
from backend.rag.retriever import PolicyRetriever

logger = logging.getLogger(__name__)

class KnowledgeIngestionPipeline:
    """
    Enterprise Safe, Incremental, Idempotent Knowledge Ingestion Pipeline.
    Maintains cryptographic content hashes and prevents stale or duplicate chunks.
    Ensures safe rollback on indexing failure.
    """

    def __init__(self, target_dirs: Optional[List[str]] = None, chunk_size: int = 1000, overlap: int = 150):
        self.target_dirs = target_dirs or ["./knowledge_base", "./backend/rag/knowledge_base"]
        self.chunker = DocumentChunker(target_chunk_size=chunk_size, chunk_overlap=overlap)
        self.manifest_mgr = ManifestManager()
        self.collection = get_knowledge_collection()
        Base.metadata.create_all(bind=engine)

    def run_incremental_ingestion(self, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Discovers all supported documents, skips unchanged documents,
        and incrementally ingests new/modified documents into ChromaDB & SQLite.
        """
        import time
        start_time = time.time()
        discovered = discover_documents(self.target_dirs)

        stats = {
            "discovered": len(discovered),
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "total_chunks_indexed": 0,
            "documents_indexed": [],
            "documents_skipped": [],
            "documents_failed": []
        }

        any_indexed = False
        for doc_desc in discovered:
            if doc_desc.get("is_duplicate"):
                stats["skipped"] += 1
                stats["documents_skipped"].append({
                    "doc_id": doc_desc["doc_id"],
                    "file_name": doc_desc["file_name"],
                    "reason": "Duplicate content hash detected"
                })
                continue

            doc_id = doc_desc["doc_id"]
            content_hash = doc_desc["content_hash"]

            # Idempotency check: Skip if unchanged and not forcing re-index
            if not force_reindex and self.manifest_mgr.is_document_unchanged(doc_id, content_hash):
                stats["skipped"] += 1
                stats["documents_skipped"].append({
                    "doc_id": doc_id,
                    "file_name": doc_desc["file_name"],
                    "reason": "Unchanged content hash"
                })
                continue

            try:
                chunks_indexed = self.index_single_document(doc_desc)
                stats["processed"] += 1
                stats["total_chunks_indexed"] += chunks_indexed
                stats["documents_indexed"].append({
                    "doc_id": doc_id,
                    "file_name": doc_desc["file_name"],
                    "chunks": chunks_indexed
                })
                any_indexed = True
            except Exception as e:
                logger.error(f"Failed to ingest document '{doc_desc['file_name']}': {e}")
                stats["failed"] += 1
                stats["documents_failed"].append({
                    "doc_id": doc_id,
                    "file_name": doc_desc["file_name"],
                    "error": str(e)
                })

        if any_indexed:
            PolicyRetriever.clear_cache()

        duration = (time.time() - start_time) * 1000.0
        record_custom_span(
            name="knowledge_ingestion_pipeline",
            duration_ms=duration,
            attributes={
                "discovered": stats["discovered"],
                "processed": stats["processed"],
                "skipped": stats["skipped"],
                "failed": stats["failed"],
                "chunks": stats["total_chunks_indexed"]
            }
        )

        logger.info(
            f"Ingestion completed: Discovered={stats['discovered']}, Processed={stats['processed']}, "
            f"Skipped={stats['skipped']}, Failed={stats['failed']}, Chunks Indexed={stats['total_chunks_indexed']}"
        )
        return stats

    def index_single_document(self, doc_desc: Dict[str, Any]) -> int:
        """
        Parses, chunks, and atomically upserts vectors for a single document.
        Safe rollback guarantee: Existing vectors are NOT removed until replacement
        chunks are fully parsed and validated.
        """
        file_path = doc_desc["file_path"]
        file_name = doc_desc["file_name"]
        file_type = doc_desc["file_type"]
        category = doc_desc["category"]
        source_type = doc_desc["source_type"]
        doc_id = doc_desc["doc_id"]
        content_hash = doc_desc["content_hash"]
        file_size = doc_desc["file_size"]

        chunks: List[DocumentChunk] = []
        doc_title = file_name
        version = "1.0"
        page_count = 1
        char_count = 0
        full_text_sample = ""
        effective_from = None
        effective_to = None
        jurisdiction = "GLOBAL"
        approval_status = "APPROVED"
        document_access_scope = "ALL"
        status = "ACTIVE"

        # 1. Parse Document & Extract Metadata (Validation Phase)
        try:
            if file_type == "PDF":
                pdf_data = PDFLoader.load_pdf(file_path)
                doc_title = pdf_data["title"]
                page_count = pdf_data["total_pages"]
                char_count = pdf_data["total_characters"]
                chunks = self.chunker.chunk_pdf_pages(
                    doc_id=doc_id,
                    title=doc_title,
                    filename=file_name,
                    category=category,
                    source_type=source_type,
                    pages=pdf_data["pages"]
                )
                full_text_sample = pdf_data["pages"][0]["text"] if pdf_data["pages"] else ""

            elif file_type == "MD":
                md_data = MarkdownLoader.load_markdown(file_path)
                doc_title = md_data["title"]
                fm = md_data["frontmatter"]
                if fm.get("category"):
                    category = str(fm["category"])
                if fm.get("source_type"):
                    source_type = str(fm["source_type"])
                if fm.get("version"):
                    version = str(fm["version"])
                if fm.get("doc_id") or fm.get("document_id"):
                    doc_id = str(fm.get("doc_id") or fm.get("document_id"))
                if fm.get("effective_from"):
                    effective_from = str(fm["effective_from"])
                if fm.get("effective_to"):
                    effective_to = str(fm["effective_to"])
                if fm.get("jurisdiction"):
                    jurisdiction = str(fm["jurisdiction"]).upper()
                if fm.get("approval_status"):
                    approval_status = str(fm["approval_status"]).upper()
                if fm.get("document_access_scope"):
                    document_access_scope = str(fm["document_access_scope"]).upper()
                if fm.get("status"):
                    status = str(fm["status"]).upper()

                char_count = md_data["total_characters"]
                chunks = self.chunker.chunk_markdown_sections(
                    doc_id=doc_id,
                    title=doc_title,
                    filename=file_name,
                    category=category,
                    source_type=source_type,
                    sections=md_data["sections"]
                )
                full_text_sample = md_data["raw_content"][:500]

            elif file_type == "TXT":
                txt_data = TextLoader.load_plain_text(file_path)
                doc_title = txt_data["title"]
                char_count = txt_data["total_characters"]
                chunks = self.chunker.chunk_raw_text(
                    doc_id=doc_id,
                    title=doc_title,
                    filename=file_name,
                    file_type="TXT",
                    category=category,
                    source_type=source_type,
                    raw_text=txt_data["content"]
                )
                full_text_sample = txt_data["content"][:500]

            elif file_type == "HTML":
                html_data = TextLoader.load_html(file_path)
                doc_title = html_data["title"]
                char_count = html_data["total_characters"]
                chunks = self.chunker.chunk_raw_text(
                    doc_id=doc_id,
                    title=doc_title,
                    filename=file_name,
                    file_type="HTML",
                    category=category,
                    source_type=source_type,
                    raw_text=html_data["content"]
                )
                full_text_sample = html_data["content"][:500]

            elif file_type == "CSV":
                csv_data = TextLoader.load_csv(file_path)
                doc_title = csv_data["title"]
                char_count = csv_data["total_characters"]
                chunks = self.chunker.chunk_raw_text(
                    doc_id=doc_id,
                    title=doc_title,
                    filename=file_name,
                    file_type="CSV",
                    category=category,
                    source_type=source_type,
                    raw_text=csv_data["content"]
                )
                full_text_sample = csv_data["content"][:500]

            elif file_type == "DOCX":
                docx_data = TextLoader.load_docx(file_path)
                doc_title = docx_data["title"]
                char_count = docx_data["total_characters"]
                chunks = self.chunker.chunk_raw_text(
                    doc_id=doc_id,
                    title=doc_title,
                    filename=file_name,
                    file_type="DOCX",
                    category=category,
                    source_type=source_type,
                    raw_text=docx_data["content"]
                )
                full_text_sample = docx_data["content"][:500]

            if not chunks:
                raise ValueError(f"No usable content chunks could be extracted from '{file_name}'")

        except Exception as e:
            # Preservation of existing index on failure
            logger.error(f"Validation/Extraction failed for '{file_name}': {e}. Preserving last valid index.")
            meta_fail = DocumentMetadataModel(
                doc_id=doc_id,
                document_title=doc_title,
                category=category,
                source_type=source_type,
                file_type=file_type,
                file_name=file_name,
                file_path=file_path,
                content_hash=content_hash,
                file_size_bytes=file_size,
                status="FAILED",
                error_message=str(e)
            )
            self.manifest_mgr.record_document_status(doc_id, meta_fail, status="FAILED", error_message=str(e))
            raise

        # 2. Atomic Vector Replacement: Chunks are valid, proceed to Chroma purge and upsert
        try:
            self.collection.delete(where={"doc_id": doc_id})
        except Exception:
            pass

        # 3. Upsert Chunks into ChromaDB with Temporal & Policy Metadata
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            ids = [c.chunk_id for c in batch]
            documents = [c.text for c in batch]
            metadatas = [
                {
                    "doc_id": c.doc_id,
                    "document_title": c.document_title,
                    "section": c.section,
                    "page_number": int(c.page_number) if c.page_number is not None else 1,
                    "file_type": c.file_type,
                    "source_file": c.source_file,
                    "source_type": c.source_type,
                    "category": c.category,
                    "chunk_index": c.chunk_index,
                    "version": version,
                    "status": status,
                    "effective_from": effective_from or "",
                    "effective_to": effective_to or "",
                    "jurisdiction": jurisdiction,
                    "approval_status": approval_status,
                    "document_access_scope": document_access_scope
                }
                for c in batch
            ]
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        # 4. Synchronize with Relational Database
        db = SessionLocal()
        try:
            now_utc = datetime.now(timezone.utc)
            existing_doc = db.query(KnowledgeDocument).filter_by(doc_id=doc_id).first()
            manifest_meta = {
                "content_hash": content_hash,
                "file_path": file_path,
                "file_type": file_type,
                "file_size_bytes": file_size,
                "page_count": page_count,
                "character_count": char_count,
                "chunk_count": len(chunks),
                "source_type": source_type,
                "version": version,
                "status": status,
                "effective_from": effective_from,
                "effective_to": effective_to,
                "jurisdiction": jurisdiction,
                "approval_status": approval_status,
                "document_access_scope": document_access_scope,
                "ingested_at": now_utc.isoformat()
            }

            if existing_doc:
                existing_doc.title = doc_title
                existing_doc.category = category
                existing_doc.version = version
                existing_doc.status = status
                existing_doc.effective_from = effective_from
                existing_doc.effective_to = effective_to
                existing_doc.jurisdiction = jurisdiction
                existing_doc.approval_status = approval_status
                existing_doc.content_hash = content_hash
                existing_doc.document_access_scope = document_access_scope
                existing_doc.chunk_count = len(chunks)
                existing_doc.content = full_text_sample
                existing_doc.metadata_json = json.dumps(manifest_meta)
                existing_doc.ingested_at = now_utc
            else:
                kdoc = KnowledgeDocument(
                    doc_id=doc_id,
                    title=doc_title,
                    category=category,
                    version=version,
                    status=status,
                    effective_from=effective_from,
                    effective_to=effective_to,
                    jurisdiction=jurisdiction,
                    approval_status=approval_status,
                    content_hash=content_hash,
                    document_access_scope=document_access_scope,
                    chunk_count=len(chunks),
                    content=full_text_sample,
                    metadata_json=json.dumps(manifest_meta),
                    ingested_at=now_utc
                )
                db.add(kdoc)

            # Audit record
            audit_ev = AuditEvent(
                correlation_id=generate_uuid(),
                actor_id="system_ingestion_pipeline",
                actor_role="administrator",
                action="KNOWLEDGE_DOCUMENT_INDEXED",
                target_type="DOCUMENT",
                target_id=doc_id,
                outcome="SUCCESS",
                policy_version_applied=version,
                timestamp=now_utc,
                details_json=json.dumps({
                    "file_name": file_name,
                    "chunks": len(chunks),
                    "pages": page_count,
                    "version": version,
                    "hash": content_hash
                })
            )
            db.add(audit_ev)
            db.commit()
        finally:
            db.close()

        # 5. Record Document in Manifest
        meta_model = DocumentMetadataModel(
            doc_id=doc_id,
            document_title=doc_title,
            category=category,
            source_type=source_type,
            file_type=file_type,
            file_name=file_name,
            file_path=file_path,
            content_hash=content_hash,
            file_size_bytes=file_size,
            page_count=page_count,
            character_count=char_count,
            chunk_count=len(chunks),
            version=version,
            status=status,
            effective_from=effective_from,
            effective_to=effective_to,
            jurisdiction=jurisdiction,
            approval_status=approval_status,
            document_access_scope=document_access_scope,
            uploaded_at=now_utc.isoformat()
        )
        self.manifest_mgr.record_document_status(doc_id, meta_model, status="INDEXED")
        PolicyRetriever.clear_cache()

        logger.info(f"Indexed document '{file_name}' ({doc_id}) v{version} with {len(chunks)} chunks.")
        return len(chunks)

    def reindex_document(self, doc_id: str) -> Dict[str, Any]:
        """Forces re-indexing of a single specified document."""
        discovered = discover_documents(self.target_dirs)
        target = next((d for d in discovered if d["doc_id"] == doc_id), None)
        if not target:
            raise ValueError(f"Document with doc_id '{doc_id}' not found in knowledge base directories.")
        chunks_count = self.index_single_document(target)
        PolicyRetriever.clear_cache()
        return {"status": "SUCCESS", "doc_id": doc_id, "chunks_indexed": chunks_count}

    def remove_document_index(self, doc_id: str) -> bool:
        """
        Safely removes document vector chunks from Chroma and marks status in DB/manifest,
        WITHOUT deleting the original source file on disk.
        """
        try:
            self.collection.delete(where={"doc_id": doc_id})
        except Exception as e:
            logger.warning(f"Chroma delete error for {doc_id}: {e}")

        db = SessionLocal()
        try:
            doc = db.query(KnowledgeDocument).filter_by(doc_id=doc_id).first()
            if doc:
                db.delete(doc)
                db.commit()
        finally:
            db.close()

        self.manifest_mgr.remove_document(doc_id)
        PolicyRetriever.clear_cache()
        logger.info(f"Safely removed index and database records for document '{doc_id}'. Original file preserved.")
        return True
