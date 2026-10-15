from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentMetadataModel(BaseModel):
    doc_id: str
    document_title: str
    category: str
    source_type: str = "official_regulation"
    file_type: str
    file_name: str
    file_path: str
    content_hash: str
    file_size_bytes: int
    page_count: int = 1
    character_count: int = 0
    chunk_count: int = 0
    version: str = "1.0"
    author: Optional[str] = None
    status: str = "INDEXED"  # INDEXED, FAILED, SKIPPED, MODIFIED
    error_message: Optional[str] = None
    ingested_at: Optional[str] = None

class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    document_title: str
    section: str
    page_number: Optional[int] = None
    file_type: str
    source_file: str
    source_type: str = "official_regulation"
    category: str = "regulations"
    text: str
    chunk_index: int = 0

class SourceCitation(BaseModel):
    document_id: str
    document_title: str
    category: str
    source_type: str
    file_type: str
    source_file: str
    page_number: Optional[int] = None
    section: str
    excerpt: str
    full_text: str
    relevance_score: float

class RetrievalResponse(BaseModel):
    query: str
    has_evidence: bool
    results_count: int
    citations: List[SourceCitation]
    synthesis: Optional[str] = None
    trace_id: Optional[str] = None
