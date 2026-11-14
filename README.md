# FinGuard: Autonomous Financial Risk Intelligence & Fraud Investigation Platform

![FinGuard Enterprise Agentic AI Ecosystem for Financial Risk](docs/architecture.png)

> **FinGuard** is an enterprise-grade financial risk intelligence and fraud investigation platform built on a verified **nine-layer architecture**. Combining machine learning, stateful LangGraph multi-agent orchestration, policy-grounded RAG, Model Context Protocol (MCP) tool integration, and OpenTelemetry observability, FinGuard empowers compliance teams and financial crime investigators with explainable, audited decision support.

---

## 🏛️ Exact 9-Layer Architecture

FinGuard implements every layer specified in the enterprise architecture specification:

1. **Layer 1 — User & Experience Layer**: Professional React 19 + TypeScript + Vite + Tailwind CSS dark-theme application featuring Executive Risk Overview, Transaction Intelligence with slide-over ledger inspection, live **Agent Workflow** (`/agents`) visualizer with SSE token typewriter, Investigation Workbench with 4-Eyes disposition review & agent replay, AI Risk Assistant with grounded RAG, Model Intelligence, Governance & Audit trail, and OpenTelemetry Observability Center.
2. **Layer 2 — Orchestration & Control Plane**: FastAPI + LangGraph stateful multi-agent workflow coordinating 10 specialized agents with dynamic fast-track conditional routing (`risk < 30` skips forensic nodes, saving ~80% compute), event streaming via `astream_events(version="v2")`, retry boundaries, and human-in-the-loop checkpoints.
3. **Layer 3 — Knowledge & Memory Layer**: Persistent Chroma vector store indexing AML/KYC guidelines (FATF Recommendation 16, RBI KYC/AML Master Direction), fraud typologies, and internal governance policies with source metadata, temporal freshness (`effective_from` / `effective_to`), and citation tracking.
4. **Layer 4 — Core Financial Risk Intelligence Layer**: PaySim dataset ingestion, feature engineering with target leakage guards (`LeakageGuard`), Random Forest fraud prediction, Market & Credit Risk exposure scoring, deterministic rule penalties, and TreeSHAP explainability.
5. **Layer 5 — Tools & Integrations Layer via MCP**: Standardized Model Context Protocol (MCP) server providing validated tools for transaction lookup, account profiling, risk scoring, policy search, case creation, and synthetic screening.
6. **Layer 6 — Observability & Monitoring Layer**: OpenTelemetry distributed traces, span recorders, latency percentiles, real-time Groq LLM token consumption & cost tracking, and Service Level Objectives (SLOs).
7. **Layer 7 — Governance, Security & Trust Layer**: Server-enforced Role-Based Access Control (RBAC) across 4 roles (`analyst`, `investigator`, `auditor`, `administrator`), JWT authentication, Presidio PII masking, `PromptGuard` injection defense, SHA-256 cryptographic audit hash chaining, and 4-Eyes disposition sign-off.
8. **Layer 8 — Data Sources Layer**: PaySim financial dataset (`PS_20174392719_1491204439457_log.csv`) ingestion pipeline, ledger consistency validation, and SQLite persistence (`finguard.db`).
9. **Layer 9 — Model Evaluation & QA Layer**: Empirical PR-AUC (0.9449), ROC-AUC (0.9844), F1-Score (0.9412), Balanced Accuracy (0.9445), 5-Fold Cross Validation (0.9388 ± 0.0082), baseline comparison against Gradient Boosting and Logistic Regression, and automated 80-test pytest suite.

---

## 🤖 The 10 Specialized LangGraph Agents

The core reasoning engine consists of 10 specialized LangGraph agents collaborating through a shared investigation state:

| Agent | Responsibility | Node Type & Edge Behavior |
| :--- | :--- | :--- |
| **1. Supervisor Agent** | Evaluates incoming transaction payload, generates correlation UUID, and determines initial graph routing strategy. | Orchestration Entry |
| **2. Transaction Intake Agent** | Validates schema constraints, formats currency decimals, masks sensitive account IDs, and loads persisted database records. | Intake & Ledger Normalization |
| **3. Data Quality Agent** | Enforces `LeakageGuard` checks, ensuring ground-truth target labels (`is_fraud`) are completely stripped prior to model inference. | Boundary & Quality Guard |
| **4. Fraud Detection Agent** | Executes trained Random Forest model, computes fraud probability, and triggers deterministic rule flags. | ML Classifier & Rule Engine |
| **5. Market & Credit Risk Agent** | Analyzes counterparty exposure, Value-at-Risk (VaR), portfolio concentration ratio, and assigns synthetic credit risk ratings. | Quantitative Risk Analytics |
| **6. Risk Assessment Agent** | Synthesizes ML probabilities, market risk, and rule penalties into a 0–100 composite risk score; evaluates dynamic fast-track threshold (`score < 30`). | Dynamic Conditional Router |
| **7. Investigation Agent** | Performs forensic graph analysis on origin account liquidation, velocity across 72 hours, and counterparty relationships. | Forensic Investigator *(Fast-Track Skipped)* |
| **8. Policy & Compliance Agent** | Performs semantic RAG retrieval across indexed regulatory documents (FATF Rec. 16, AML-04) and binds source citations. | Statutory Compliance *(Fast-Track Skipped)* |
| **9. Explainability Agent** | Synthesizes TreeSHAP feature attributions and streams objective risk narratives via Groq LLM without speculative language. | Live Token Streaming Generator |
| **10. Audit & Reporting Agent** | Assembles the complete forensic docket, records an immutable `AuditEvent`, and seals the record with a SHA-256 hash chain. | Audit Sealer & Terminal Node |

### Dynamic Conditional Routing (Fast-Track vs. Deep Forensic Track)
- **Fast-Track Route (`Composite Score < 30.0`)**: Routine payments and low-risk transfers skip the deep forensic Investigation and Policy Compliance agents, jumping directly from Risk Assessment to Explainability and Audit Reporting. This reduces execution latency to ~3ms and saves ~80% compute.
- **Deep Forensic Route (`Composite Score ≥ 30.0`)**: Elevated and high-risk transactions execute all 10 agents sequentially, performing full account-liquidation forensic tracing, regulatory RAG grounding, and mandatory 4-Eyes human investigator review.

---

## 📊 Single Source of Truth: Model Evaluation & Performance

All evaluation metrics are computed in `scripts/train_model.py` and serialized to `models/metrics.json`, ensuring the UI dashboard, API endpoints, and documentation read from the identical source of truth:

| Metric | Score | Benchmark / Context |
| :--- | :--- | :--- |
| **ROC-AUC** | **0.9844** | High discriminatory power across all decision thresholds |
| **PR-AUC** | **0.9449** | Robust precision-recall curve on highly imbalanced fraud classes |
| **Precision** | **1.0000** (100.0%) | 0 false positives observed on held-out evaluation test split |
| **Recall** | **0.8889** (88.9%) | 48 confirmed frauds detected, 6 missed on evaluated sample |
| **F1-Score** | **0.9412** | Harmonic mean of precision and recall |
| **Balanced Accuracy** | **0.9445** | Arithmetic mean of sensitivity (88.9%) and specificity (100.0%) |
| **5-Fold Cross Validation** | **0.9388 ± 0.0082** | Mean F1 score across 5 stratified folds demonstrating low variance |
| **Optimal Threshold** | **0.65** | Calibrated decision boundary balancing fraud capture vs. false friction |

### Baseline Model Comparison
| Model Architecture | Precision | Recall | F1-Score | PR-AUC |
| :--- | :--- | :--- | :--- | :--- |
| **Random Forest (FinGuard Primary)** | **1.0000** | **0.8889** | **0.9412** | **0.9449** |
| Gradient Boosting (XGBoost Baseline) | 0.9412 | 0.8889 | 0.9143 | 0.9124 |
| Logistic Regression (Linear Baseline) | 0.8125 | 0.7222 | 0.7647 | 0.7418 |

### Transparent Dataset & Synthetic Limitations
> **Notice on PaySim Synthetic Characteristics**: PaySim is an agent-based synthetic simulation of mobile money transfers. In synthetic data, origin balance error features (`oldbalanceOrg - amount == 0`) create high separability, explaining why our sample test split achieves zero false positives. In production systems, benign ledger inconsistencies occur routinely. FinGuard mitigates data leakage by stripping target variables through `LeakageGuard`, enforcing deterministic business logic checks, and using 4-Eyes human confirmation before any critical action is executed.

---

## 🔐 Server-Enforced 4-Role RBAC Matrix

FinGuard implements strict, server-side role enforcement on every API route via JWT claims:

| Role | Default User | Credentials | Permitted Capabilities & Restrictions |
| :--- | :--- | :--- | :--- |
| **Analyst** | `sarah` / `user` | `user@finguard.local` / `12345` | View transactions, execute live agent workflows, query AI Risk Assistant. Cannot submit case dispositions or access system admin. |
| **Investigator** | `marcus` | `marcus@finguard.local` / `12345` | Complete case dossier access, submit verified dispositions (`ESCALATE_TO_SAR`, `FREEZE_ACCOUNT`), sign off on 4-Eyes review. |
| **Auditor** | `elena` | `elena@finguard.local` / `12345` | Read-only access to immutable audit logs, model performance reports, and SHA-256 cryptographic chain integrity verification. |
| **Administrator** | `admin` | `admin@finguard.local` / `123456` | Full platform access, user account management (enable/disable, password resets), MCP tool registry, and bulk CSV ingest. |

---

## ⚡ Live Features

### 1. Live Multi-Agent Workflow View (`/agents`)
- **Server-Sent Events (SSE)**: Streams events from `POST /api/v1/agents/analyze/stream` using `astream_events("v2")`.
- **Horizontal Pipeline Strip**: Real-time status badges for all 10 agents (*Waiting, Running Pulsing, Completed, Skipped via Fast-Track*).
- **Live LLM Token Typewriter**: Streams explanation narrative tokens in real time from Groq (`llama-3.3-70b-versatile`).
- **Orchestrator Verdict Card**: Displays final composite risk score, operational tier, policy citations, and deep-link to create/open investigation dockets.
- **Trace Replay**: Full historical agent runs stored in SQLite `agent_runs` table, replayed on-demand in both the Agent Workflow and Investigation Workbench.

### 2. Transaction Ingestion & Modal (`+ Add Transaction`)
- Primary button on Transactions table header and quick-action on Risk Dashboard.
- Strict ledger consistency validation (impossible balances and negative amounts rejected with 422).
- Presets: *"Load Sample: Normal Payment"* and *"Load Sample: Fraud-Like Drain"*.
- Actions: *"Save only"* and *"Save & Run Agents Live"*.
- Auto-case creation for High / Critical risk transactions with status `OPEN` and 4-Eyes review required.
- Bulk CSV upload with row-by-row ledger validation for Administrators.

### 3. Cryptographic Audit Hash Chaining
- Every transaction creation, agent execution, user status change, and investigator disposition computes a SHA-256 hash incorporating the previous event's hash (`event_hash = SHA256(corr_id : action : target_id : prev_hash : timestamp)`).
- **"Verify Chain Integrity"** button in Governance & Audit page verifies genesis-to-tip integrity on-demand.

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, and 3.13)
- Node.js 18+ (tested on Node 20 and 24)

### 2. Environment Configuration
Create `.env` in the project root:
```env
PROJECT_NAME="FinGuard - Autonomous Financial Risk Intelligence"
ENVIRONMENT="development"
DEBUG=True
DATABASE_URL="sqlite:///./finguard.db"
SECRET_KEY="finguard-enterprise-autonomous-risk-intelligence-secure-jwt-key"
GROQ_API_KEY="your_groq_api_key_here"
GROQ_MODEL="llama-3.3-70b-versatile"
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000","https://finguard-mu-wheat.vercel.app"]
```

### 3. Installation
```bash
# Python backend
pip install -r requirements.txt

# Node frontend
cd frontend
npm install
cd ..
```

### 4. Database Setup & Knowledge Ingestion
```bash
# Ingest compliance documents into ChromaDB
python scripts/ingest_knowledge.py

# Seed database with transactions and accounts
python scripts/seed_database.py

# Regenerate case dossiers with verified LangGraph multi-agent traces
python scripts/regenerate_cases.py
```

### 5. Run Automated Tests
```bash
# Run complete test suite (80 tests)
pytest backend/tests/ -v

# Run frontend build check
npm --prefix frontend run build
```

### 6. Start Development Servers
**Terminal 1 (Backend - FastAPI)**:
```bash
python backend/main.py
# API runs on: http://127.0.0.1:8000
# OpenAPI Docs: http://127.0.0.1:8000/docs
```

**Terminal 2 (Frontend - React + Vite)**:
```bash
cd frontend
npm run dev
# UI runs on: http://localhost:5173
```

---

## ☁️ Cloud Deployment Guide (Render + Vercel)

### Backend Deployment on Render
1. Create a **Web Service** on [Render](https://render.com) connected to your repository.
2. Configure settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variables in Render Dashboard:
   - `ENVIRONMENT`: `production`
   - `DEBUG`: `False`
   - `SECRET_KEY`: `[generate strong 32+ character key]`
   - `GROQ_API_KEY`: `[your Groq API key]`
   - `GROQ_MODEL`: `llama-3.3-70b-versatile`
   - `DATABASE_URL`: `sqlite:///./finguard.db`
   - `ALLOWED_ORIGINS`: `["https://finguard-mu-wheat.vercel.app"]`
4. Health check path: `/health`

### Frontend Deployment on Vercel
1. Import repository on [Vercel](https://vercel.com).
2. Configure project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add Environment Variable:
   - `VITE_API_URL`: `https://[your-render-app-name].onrender.com`
4. Deploy. The frontend includes automatic Render cold-start detection and wake-up notifications.

---

## 📄 License & Compliance Notice

This platform is a **decision-support tool** for authorized compliance professionals, not financial or legal advice. Final regulatory filings and account interventions require human investigator sign-off in compliance with the **Four-Eyes Principle**.
