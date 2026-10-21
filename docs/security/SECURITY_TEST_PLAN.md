# FinGuard Comprehensive Security & Quality Test Plan

**Document Version:** 1.0.0  
**Target Environment:** Local Antigravity Workspace / CI Pipeline  
**Execution Framework:** `pytest` (Python 3.11 / 3.12 / 3.13)  
**Lead Author:** DevSecOps Specialist & QA Architect  

---

## 1. Test Strategy & Scope

The FinGuard security test suite validates that technical guardrails operate robustly across normal, boundary, and adversarial conditions. Tests run deterministically without requiring live cloud connections for core verification.

---

## 2. Test Suites & Coverage Breakdown

### 2.1 Authentication & RBAC (`test_enterprise_auth.py`, `test_enterprise_fixes.py`)
* `test_login_valid_credentials`: Confirms access token issue and profile payload.
* `test_login_invalid_credentials`: 401 response on mismatched password.
* `test_system_health_user_tier`: Confirms standard user only receives summary health, while admin receives full telemetry traces.
* `test_assistant_conversation_persistence`: Tests conversation creation, messaging, and verifies that User B receives `403 Forbidden` when attempting to access User A's thread.
* `test_investigation_review_submission`: Verifies that disposition actions update case status and record reviewer username.

### 2.2 Policy Versioning & Freshness (`test_policy_freshness_and_versioning.py`)
* `test_missing_effective_dates_handled_safely`: Ensures unversioned documents do not cause runtime crashes.
* `test_citations_report_actual_selected_policy_version`: Asserts that citations report `version`, `status`, and `jurisdiction`.
* `test_cache_invalidation_after_policy_update`: Validates that `clear_cache()` purges the query cache.
* `test_event_date_temporal_evaluation`: Confirms that queries with historical event dates evaluate temporal applicability.
* `test_abstention_on_non_existent_policy`: Tests that queries with zero supporting evidence return `has_evidence=False`, trigger human review, and synthesize an explicit insufficient-evidence message.
* `test_safe_indexing_error_preserves_last_index`: Simulates corrupt document parsing and confirms existing index remains intact while manifest records `FAILED`.

### 2.3 AI Security & Presidio PII (`test_ai_security_and_presidio.py`)
* `test_presidio_redact_email_and_phone`: Verifies redaction of email addresses and phone numbers.
* `test_presidio_redact_financial_accounts`: Verifies detection and masking of banking account numbers.
* `test_vault_unmasking_access_control`: Asserts that only authorized roles (`investigator`, `administrator`) can unmask vaulted tokens.
* `test_prompt_guard_detects_jailbreak_and_system_override`: Confirms detection of direct prompt injection, system overrides, and SQL injection strings.
* `test_prompt_guard_enforces_length_limit`: Verifies rejection of prompts exceeding 4,000 characters.
* `test_prompt_guard_untrusted_context_sandboxing`: Confirms that delimiter hijacking tokens (`<|im_start|>`, `[INST]`) are neutralized.
* `test_mcp_unapproved_tool_rejected`: Rejects unapproved tools with `FORBIDDEN_TOOL`.
* `test_mcp_server_side_rbac_enforcement`: Rejects unauthorized tool invocation when role lacks permission.
* `test_mcp_4_eyes_human_approval_bypass_attempt`: Confirms that high-severity actions (`FREEZE_ACCOUNT`) cannot be called without proper role and justification.
* `test_upload_mismatched_pdf_content_rejected`: Rejects non-PDF files disguised with a `.pdf` extension.
* `test_production_config_rejects_insecure_defaults`: Asserts that `Settings` raises a fatal validation error in production if `DEBUG=True` or `SECRET_KEY` is insecure.

### 2.4 RAG Evaluation & Groundedness (`test_rag_evaluation.py`)
* `test_rag_retrieval_relevance_benchmark`: Asserts top citations achieve relevance >= 0.40.
* `test_rag_citation_correctness_and_provenance`: Verifies page numbers, sections, and source filenames are preserved in citations.
* `test_rag_abstention_and_evidence_sufficiency`: Asserts strict abstention without hallucination on out-of-scope inquiries.
* `test_rag_grounded_synthesis_citations`: Asserts synthesized responses contain factual citations.

---

## 3. Test Execution Instructions

### Run All Security & Governance Tests
```bash
pytest backend/tests/test_ai_security_and_presidio.py backend/tests/test_policy_freshness_and_versioning.py backend/tests/test_rag_evaluation.py -v
```

### Run Entire Regression Test Suite
```bash
pytest -v
```
