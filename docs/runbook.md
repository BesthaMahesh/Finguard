# FinGuard Operations Runbook & Startup Guide

## Prerequisites
- **Python**: Version 3.10+ (Tested on Python 3.13)
- **Node.js**: Version 18+ (Tested on Node 24.12)
- **Git**

---

## 1. Quick Start Commands

### Step 1: Environment Setup
Ensure the root `.env` file exists with the Groq API key:
```bash
# In repository root
cp .env.example .env
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Model Training & Evaluation
Trains the Random Forest model on PaySim data and saves `models/finguard_rf_model.joblib`:
```bash
python scripts/train_model.py
```

### Step 4: Ingest Regulatory Knowledge Base
Indexes compliance policies into Chroma vector store:
```bash
python scripts/ingest_knowledge.py
```

### Step 5: Seed Primary Ledger Database
Seeds 12,000 real PaySim transactions, model governance metadata, and initial investigation cases:
```bash
python scripts/seed_database.py
```

### Step 6: Start the FastAPI Backend
```bash
python backend/main.py
# Backend runs on http://127.0.0.1:8000
# OpenAPI Docs available at http://127.0.0.1:8000/docs
```

### Step 7: Start the React Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

---

## 2. Running Automated Tests
```bash
pytest backend/tests/ -v
```

---

## 3. Demo Role Credentials
The platform includes built-in test accounts across the 4 enterprise roles:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Risk Analyst** | `analyst` | `analyst123` |
| **Senior Investigator** | `investigator` | `investigator123` |
| **Compliance Auditor** | `auditor` | `auditor123` |
| **Security Administrator** | `admin` | `admin123` |
