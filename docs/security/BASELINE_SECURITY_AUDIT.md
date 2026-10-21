# FinGuard Baseline Security Audit

**Document Version:** 1.0.0  
**Audit Date:** October 2026  
**Audited Target:** FinGuard — Autonomous Financial Risk Intelligence Platform  
**Target Environment:** Local Workspace (`c:\Users\mahes\Documents\FinGuard-Autonomous-Financial-Risk-Intelligence`)  
**Lead Auditor:** Senior AI Security Architect & DevSecOps Specialist  

---

## 1. Executive Summary

This Baseline Security Audit evaluates the security posture of the **FinGuard Autonomous Financial Risk Intelligence & Fraud Investigation Platform** prior to comprehensive enterprise security hardening. FinGuard combines a FastAPI backend, LangGraph agent workflows, ChromaDB vector retrieval, Scikit-Learn/SHAP ML models, Model Context Protocol (MCP) tooling, and a React frontend to deliver financial crime analysis.

The baseline assessment identified critical security exposures in credential management, CORS policies, PII protection, MCP tool execution guardrails, and temporal regulatory retrieval.

---

## 2. Baseline Test Suite Execution

A complete run of the existing automated test suite was executed against the local environment using `pytest`:

```bash
pytest
```

### Baseline Results Summary
* **Platform:** Windows 11 / Python 3.13.0 / pytest-9.0.2 / LangSmith 0.6.4
* **Total Tests Discovered:** 47
* **Tests Passed:** 46 (97.9%)
* **Tests Failed:** 1 (2.1%)
* **Pre-existing Failure Analysis:**
  * **Test:** `backend/tests/test_knowledge_rag.py::test_policy_retriever_insufficient_evidence`
  * **Root Cause:** In `backend/rag/retriever.py`, the relevance threshold logic forced `min(min_relevance_score, 0.35)` instead of honoring the caller's requested threshold (e.g. 0.45). Consequently, an out-of-scope query ("Subterranean Martian gold smelting...") returned weak lexical/vector fragments that incorrectly flagged `has_evidence=True`.
* **Deprecation Warnings:** 67 warnings observed regarding `datetime.utcnow()` (deprecated in Python 3.12/3.13 in favor of `datetime.now(datetime.UTC)`), Pydantic v2 `class Config` vs `ConfigDict`, and FastAPI startup event handlers (`@app.on_event("startup")` vs `lifespan`).

---

## 3. Discovered Vulnerabilities & Architectural Deficiencies

### 3.1 Authentication & Secret Management (CWE-798, CWE-547)
* **Hardcoded Secret Key:** `backend/core/config.py` contained a static fallback `SECRET_KEY = "finguard-enterprise-autonomous-risk-intelligence-secure-jwt-key"`. In production, this allows forgery of JWT bearer tokens.
* **Permissive Debug Mode:** `DEBUG = True` default setting in `Settings`, risking traceback and internal state leakage.
* **Weak Seed Passwords:** Default test accounts (e.g., `user` / `12345`) trigger public breach warnings in browser password managers.

### 3.2 Cross-Origin Resource Sharing (CORS) Misconfiguration (CWE-942)
* `backend/main.py` configured:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.ALLOWED_ORIGINS,
      allow_origin_regex=r".*",
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
  The regex `r".*"` combined with `allow_credentials=True` exposes authenticated APIs and credentials to arbitrary malicious origins.

### 3.3 PII and Sensitive Financial Data Leakage (CWE-359, GDPR/PCI-DSS)
* `backend/security/pii_masker.py` was limited to basic regex masking for transaction account numbers (`C123***815`).
* Full names, email addresses, phone numbers, IP addresses, credit card formats, SWIFT/BIC codes, and tax identifiers were not systematically detected or redacted prior to dispatching prompts to external LLMs (Groq) or audit logging.
* Microsoft Presidio (`presidio-analyzer` / `presidio-anonymizer`) was not integrated into runtime workflows.

### 3.4 MCP Server & LLM Tool Execution Security (CWE-285, CWE-863)
* While `FinGuardMCPTools` had basic role assertions, tool invocation lacked strict server-side schema boundaries, explicit tool allowlists, read-only vs. side-effect capability separation, and mandatory multi-party ("4-Eyes") human approval for severe actions (such as `FREEZE_ACCOUNT` or `ESCALATE_TO_SAR`).
* `PromptGuard` relied solely on regex patterns for prompt injection, lacking structured length limits, semantic boundary checks, and untrusted RAG document containment.

### 3.5 Policy Versioning and Context Freshness Deficiencies (CWE-668)
* `backend/rag/document_types.py` only tracked static attributes (`doc_id`, `version`, `category`).
* Missing essential temporal attributes: `effective_from`, `effective_to`, `supersedes_version`, `approval_status`, `document_access_scope`, and `jurisdiction`.
* Retrieval queried the vector index without event-date temporal validation. Historical transactions (e.g., from 2021) risked being judged against newly adopted 2024 regulatory thresholds, violating compliance audit requirements.

### 3.6 Data Governance & Audit Immutability (CWE-778)
* Audit records lacked tamper-evident chaining or cryptographic digest verification.
* Ingestion re-indexing did not preserve rollback states in the event of partial indexing failures.

---

## 4. Remediation Roadmap

1. **Phase 2:** Secure configuration, fail-fast production secret validation, strict CORS whitelist, lifespan migration.
2. **Phase 3:** Microsoft Presidio integration with custom financial recognizers, workflow integration (LLMs, RAG, logging).
3. **Phase 4:** Prompt injection defense-in-depth, MCP tool server-side authorization, schema validation, read/write segregation, human-in-the-loop approvals.
5. **Phase 5:** Policy metadata expansion, date-aware temporal retriever, cache invalidation, safe atomic indexing.
6. **Phase 6:** LangGraph workflow decomposition for complex multi-step financial risk investigations.
7. **Phase 7:** ISO/IEC 27001:2022 control mapping and gap analysis.
8. **Phases 8–15:** Database governance, audit hardening, API hardening, automated tests, deployment security, and final verification.
