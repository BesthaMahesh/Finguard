"""
FinGuard Document Models & Policy Metadata Schema.
Implements Policy Versioning, Temporal Freshness (effective_from/effective_to),
Access Scopes, and Provenance Types.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class DocumentMetadataModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    doc_id: str
    document_title: str
    category: str = "regulations"  # AML, KYC, FRAUD_TYPOLOGY, SANCTIONS, INTERNAL_POLICY
    source_type: str = "official_regulation"
    file_type: str
    file_name: str
    file_path: str
    content_hash: str
    file_size_bytes: int
    page_count: int = 1
    character_count: int = 0
    chunk_count: int = 0
    
    # Versioning and Lifecycle
    version: str = "1.0"
    status: str = "ACTIVE"  # ACTIVE, SUPERSEDED, EXPIRED, DRAFT, RETRACTED, INDEXED
    effective_from: Optional[str] = None  # ISO format: YYYY-MM-DD
    effective_to: Optional[str] = None    # ISO format: YYYY-MM-DD (None = current/in force)
    uploaded_at: Optional[str] = None
    last_reviewed_at: Optional[str] = None
    supersedes_version: Optional[str] = None

    # Governance & Access Scope
    jurisdiction: str = "GLOBAL"  # GLOBAL, US, EU, FATF, IN, UK
    approval_status: str = "APPROVED"  # APPROVED, PENDING_REVIEW, REJECTED
    classification: str = "INTERNAL"  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    document_access_scope: str = "ALL"  # ALL, INVESTIGATOR_ONLY, AUDITOR_ONLY, ADMIN_ONLY

    author: Optional[str] = None
    error_message: Optional[str] = None
    ingested_at: Optional[str] = None


class DocumentChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")

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

    # Versioning & Freshness attributes
    version: str = "1.0"
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    status: str = "ACTIVE"
    jurisdiction: str = "GLOBAL"
    approval_status: str = "APPROVED"
    document_access_scope: str = "ALL"


class SourceCitation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: str
    document_title: str
    version: str = "1.0"
    status: str = "ACTIVE"
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    jurisdiction: str = "GLOBAL"
    approval_status: str = "APPROVED"
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
    model_config = ConfigDict(extra="ignore")

    query: str
    has_evidence: bool
    results_count: int
    citations: List[SourceCitation]
    synthesis: Optional[str] = None
    trace_id: Optional[str] = None

    # Temporal & Governance Metadata
    selected_policy_version: Optional[str] = None
    temporal_applicability_status: Optional[str] = "NO_TEMPORAL_RESTRICTION"
    human_review_required: bool = False
    review_reason: Optional[str] = None
