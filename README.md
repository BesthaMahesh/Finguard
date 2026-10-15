# FinGuard: Autonomous Financial Risk Intelligence & Fraud Investigation Platform

![FinGuard Enterprise Agentic AI Ecosystem for Financial Risk](docs/architecture.png)

> **FinGuard** is an enterprise-grade financial risk analysis and fraud investigation platform built on an exact **nine-layer architecture**. Combining machine learning, multi-agent orchestration, policy-grounded RAG, Model Context Protocol (MCP) tools, and OpenTelemetry observability, FinGuard empowers compliance teams and investigators with explainable decision support at scale.

---

## 🏛️ Exact 9-Layer Architecture

FinGuard implements every layer specified in the enterprise architecture specification:

1. **Layer 1 — User & Experience Layer**: Professional React 19 + TypeScript + Vite + Tailwind CSS application featuring an Executive Risk Overview, Transaction Intelligence table with slide-over forensic ledger inspection, Investigation Workbench with 4-Eyes disposition review, AI Risk Assistant, Model Intelligence, Governance & Audit trail, and OpenTelemetry Observability Center.
2. **Layer 2 — Orchestration & Control Plane**: FastAPI + LangGraph stateful 9-agent workflow coordinating specialized agents with conditional routing, retry boundaries, and human-approval checkpoints.
3. **Layer 3 — Knowledge & Memory Layer**: Persistent Chroma vector store indexing AML/KYC guidelines, FATF typologies, and internal governance policies with source metadata and citation tracking.
4. **Layer 4 — Core Financial Risk Intelligence Layer**: PaySim dataset ingestion, feature engineering with target leakage guards, Random Forest ML fraud prediction, deterministic rule engine, and TreeSHAP explainability.
5. **Layer 5 — Tools & Integrations Layer via MCP**: Standardized Model Context Protocol (MCP) server providing validated tools for transaction lookup, account profiling, risk scoring, policy search, case creation, and synthetic screening.
6. **Layer 6 — Observability & Monitoring Layer**: OpenTelemetry distributed traces, span recorders, latency percentiles, Groq token counters, and Service Level Objectives (SLOs).
7. **Layer 7 — Governance, Security & Trust Layer**: Server-side Role-Based Access Control (RBAC) across 4 roles (`analyst`, `investigator`, `auditor`, `administrator`), JWT authentication, PII masking, `PromptGuard` injection defense, and 4-Eyes review enforcement.
8. **Layer 8 — Data Sources Layer**: PaySim synthetic financial dataset (`PS_20174392719_1491204439457_log.csv`) ingestion pipeline, schema validator, and SQLite persistence.
9. **Layer 9 — Model Evaluation & QA Layer**: Empirical PR-AUC (0.9449), ROC-AUC (0.9844), F1-Score (0.9412), confusion matrix analysis, threshold operating curves, and automated test suite.

---

## 🤖 The 9 Specialized LangGraph Agents

| Agent | Responsibility |
| :--- | :--- |
| **Supervisor Agent** | Coordinates workflow, evaluates intent, assigns correlation IDs, and dynamically branches between fast-track and deep investigation. |
| **Transaction Intake Agent** | Validates incoming transaction fields and looks up persisted database records. |
| **Data Quality Agent** | Audits boundary constraints, ledger balance signs, and enforces `LeakageGuard` checks. |
| **Fraud Detection Agent** | Executes the trained Random Forest model and applies deterministic rule penalties. |
| **Risk Assessment Agent** | Synthesizes ML probabilities and rules into a 0-100 composite score; flags human-review checkpoints. |
| **Investigation Agent** | Examines origin balance liquidation, counterparty relationships, and transaction velocity. |
| **Policy & Compliance Agent** | Performs semantic RAG retrieval across indexed AML/KYC regulations and attaches source citations. |
| **Explainability Agent** | Synthesizes TreeSHAP feature attributions and objective risk narratives via Groq LLM without speculative claims. |
| **Audit & Reporting Agent** | Compiles structured forensic dockets and records immutable `AuditEvent` logs in the relational database. |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+

### 2. Setup Environment
Ensure `.env` exists with your Groq API key:
```bash
cp .env.example .env
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 4. Train Model & Seed Database
```bash
# Train Random Forest model on PaySim data
python scripts/train_model.py

# Ingest compliance policies into ChromaDB
python scripts/ingest_knowledge.py

# Seed SQLite database with 12,000 real PaySim transactions and cases
python scripts/seed_database.py
```

### 5. Run Automated Tests
```bash
pytest backend/tests/ -v
```

### 6. Start Applications
**Terminal 1 (Backend - FastAPI)**:
```bash
python backend/main.py
# Server: http://127.0.0.1:8000
# Docs: http://127.0.0.1:8000/docs
```

**Terminal 2 (Frontend - React + Vite)**:
```bash
cd frontend
npm run dev
# Dashboard: http://localhost:5173
```

---

## 🔐 Enterprise Accounts & Role-Based Access Control

The application provisions two initial development accounts, configurable via environment variables or interactive provisioning:

| Account | Email / Identifier | Role | Dev Password | Permitted Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Standard User** | `user@finguard.local` | `USER` | `12345` | Risk Dashboard, Transactions, Investigations & Review, Risk Assistant, Policies & Documents, Detection Performance |
| **Administrator** | `admin@finguard.local` | `ADMIN` | `123456` | Complete platform access + User Management (enable/disable, password reset), MCP tools, system diagnostics |

### Account Provisioning & Security Controls
- **Idempotent Provisioning Command**:
  ```bash
  python -m backend.db.init_users
  ```
  *(Also runs automatically on backend application startup)*
- **Configurable Environment Variables**: In production, override development passwords via `DEFAULT_USER_PASSWORD` and `DEFAULT_ADMIN_PASSWORD` in `.env`.
- **Password Storage**: Passwords are never committed or stored in plaintext; they are hashed with PBKDF2-HMAC-SHA256 (100,000 rounds + 16-byte random salt).
- **Brute-Force Rate Limiting**: Repeated failed login attempts are throttled using a sliding-window rate limiter (5 failed attempts per 60 seconds per account).
- **Backend Role Enforcement**: Roles and permissions are strictly enforced on backend API endpoints via OAuth2 Bearer tokens and JWT claims.

---

## 📊 Empirical Model Performance Summary

- **Trained Model**: Random Forest Classifier (Depth 10, Balanced Subsample)
- **PR-AUC**: **0.9449**
- **ROC-AUC**: **0.9844**
- **Precision**: **0.9231**
- **Recall**: **0.9600**
- **F1 Score**: **0.9412**
- **Decision Threshold**: **0.65**
- **Target Leakage**: Guaranteed 0% leakage via `LeakageGuard`
