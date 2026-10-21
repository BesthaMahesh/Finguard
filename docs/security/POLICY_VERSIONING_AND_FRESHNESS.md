# FinGuard Policy Versioning & Context Freshness Architecture

**Modules:** `backend/rag/document_types.py`, `backend/rag/retriever.py`, `backend/rag/ingestion_pipeline.py`, `backend/rag/manifest.py`  
**Regulatory Context:** Financial Crime Compliance, FATF Guidance, RBI Master Directions, Wolfsberg Group AML Principles  
**Document Version:** 1.0.0  

---

## 1. Overview & Problem Statement

Financial regulations evolve continuously:
* A transaction executed in **May 2021** must be judged against the regulatory thresholds and reporting guidelines effective in **May 2021**.
* Evaluating a 2021 transaction against newly amended **2024 regulations** introduces compliance hallucination and invalid audit findings.
* Conversely, real-time transaction monitoring must strictly utilize **currently active** policies and exclude superseded or expired rules.

FinGuard implements **Version-Aware & Temporal Freshness RAG**:
1. Documents maintain explicit effective windows (`effective_from`, `effective_to`), approval states, and version numbers.
2. The retriever accepts an `event_date` parameter and validates policy applicability **before** vector ranking.
3. Ingestion re-indexing is **atomic and safe**: failed re-indexing never destroys the last valid vector index.

---

## 2. Policy Metadata Schema

Every regulatory document and vector chunk indexed in FinGuard contains:

| Metadata Field | Type | Description |
| :--- | :--- | :--- |
| `doc_id` | String | Unique regulatory document identifier (e.g. `FATF-REC-2023`, `RBI-KYC-DIR`). |
| `version` | String | Semantic version string (e.g. `1.0`, `2.1`). |
| `status` | String | Lifecycle status: `ACTIVE`, `SUPERSEDED`, `EXPIRED`, `DRAFT`, `RETRACTED`. |
| `effective_from` | String (ISO) | Start date of legal validity (`YYYY-MM-DD`). |
| `effective_to` | String (ISO) | End date of validity (`YYYY-MM-DD` or `None` if currently in force). |
| `uploaded_at` | String (ISO) | System timestamp of file upload (distinct from effective validity dates). |
| `last_reviewed_at` | String (ISO) | Compliance officer review timestamp. |
| `supersedes_version` | String | Prior document version superseded by this document. |
| `content_hash` | String (SHA256) | Cryptographic digest for idempotency and tampering detection. |
| `jurisdiction` | String | Applicable jurisdiction: `GLOBAL`, `US`, `EU`, `FATF`, `IN`, `UK`. |
| `category` | String | Taxonomy: `regulations`, `aml_kyc`, `fraud_patterns`, `internal_policies`. |
| `source_type` | String | Provenance classification: `official_regulation`, `internal_policy`, `research`. |
| `approval_status` | String | Four-eyes governance state: `APPROVED`, `PENDING_REVIEW`, `REJECTED`. |
| `classification` | String | Confidentiality: `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`. |
| `document_access_scope` | String | Entitlement scope: `ALL`, `INVESTIGATOR_ONLY`, `AUDITOR_ONLY`, `ADMIN_ONLY`. |

---

## 3. Version-Aware Retrieval Algorithm

```
Query + [Optional event_date, jurisdiction, user_role]
                      │
                      ▼
            [Metadata Pre-Filtering]
                      │
       ├─ Check: jurisdiction matches or is "GLOBAL"
       ├─ Check: user_role meets document_access_scope
       ├─ Check: if event_date provided:
       │    ├─ effective_from <= event_date
       │    └─ effective_to >= event_date
       └─ Check: if no event_date: status != "SUPERSEDED" (unless include_superseded)
                      │
                      ▼
         [ChromaDB Vector Similarity]
                      │
                      ▼
   [Strict Relevance Threshold (relevance >= min_score)]
                      │
                      ▼
        [Deduplication & Top-K Ranking]
                      │
                      ▼
      [Formatted Citations with Version Tag]
```

### Ambiguous & Conflicting Policy Handling
If overlapping policy versions exist or applicability cannot be determined unequivocally from the metadata:
1. `RetrievalResponse.temporal_applicability_status` is flagged as `AMBIGUOUS_REQUIRES_HUMAN_REVIEW`.
2. `RetrievalResponse.human_review_required` is set to `True`.
3. The query is routed to a compliance officer checkpoint.

---

## 4. Safe Atomic Ingestion & Rollback

* **Two-Phase Commit:** During single-document or batch re-indexing, the parser and chunker extract all chunks into memory and validate them first.
* **Preservation on Failure:** If an exception occurs during parsing or embedding generation, existing ChromaDB vector chunks and database records are **not** touched. The document is flagged as `status = "FAILED"` in the manifest without corrupting search capabilities.
* **Cache Invalidation:** Whenever documents are added, updated, or removed, `PolicyRetriever.clear_cache()` is called, preventing stale answers from persisting in memory.
