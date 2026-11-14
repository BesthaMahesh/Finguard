# FinGuard 4-Minute Executive Demo Script

> **Target Audience**: Financial Crime Risk Directors, Engineering Leads, and Compliance Officers.  
> **Duration**: 4 minutes  
> **Theme**: Explainable, Agentic AI for Financial Risk with Human-in-the-Loop Governance.

---

## ⏱️ Timeline Summary

| Time | Segment | Screen / Route | Core Message |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:45** | 1. Enterprise Architecture & Overview | `/overview` (Executive Dashboard) | 9-layer architecture, 10 specialized agents, single source of truth metrics. |
| **0:45 – 1:30** | 2. Transaction Ingestion & Ledger Safeguard | `/transactions` (Transactions Table) | + Add Transaction modal, impossible ledger rejection, unknown ground-truth. |
| **1:30 – 2:30** | 3. Live 10-Agent LangGraph Workflow | `/agents` (Agent Workflow) | Real SSE streaming, fast-track conditional routing, live Groq token typewriter. |
| **2:30 – 3:15** | 4. Investigation Dossier & 4-Eyes Review | `/investigations` (Case Workbench) | Full multi-agent trace, stored replay, mandatory investigator disposition. |
| **3:15 – 4:00** | 5. RAG Refusal & Cryptographic Audit Chain | `/assistant` & `/governance` | Strict RAG refusal on out-of-scope questions, SHA-256 chain verification. |

---

## 🎙️ Spoken Walkthrough

### Segment 1: Enterprise Architecture & Executive Overview (0:00 – 0:45)
* **Action**: Start on the **Risk Dashboard** (`/overview`).
* **Spoken Script**:
  > *"Welcome to FinGuard, an autonomous financial risk intelligence and fraud investigation platform. Unlike black-box detection systems, FinGuard is built on an exact nine-layer enterprise architecture powered by a stateful LangGraph graph of ten specialized agents.*
  >
  > *On our executive dashboard, all KPIs are unified from a single source of truth: our Random Forest classifier achieves a 0.9844 ROC-AUC, 0.9449 PR-AUC, and 0.9412 F1-score with 0.9445 balanced accuracy. Crucially, we treat PaySim synthetic limitations honestly: balance error features are strictly quarantined through our `LeakageGuard` before model ingestion.*
  >
  > *Notice our live queue: exactly 23 open cases awaiting human investigator review under the mandatory Four-Eyes principle."*

---

### Segment 2: Transaction Ingestion & Impossible Ledger Defense (0:45 – 1:30)
* **Action**: Click **Transactions** in the sidebar. Click the primary cyan **"+ Add Transaction"** button.
* **Spoken Script**:
  > *"Let's ingest a live transaction. FinGuard provides strict server-enforced ledger validation.*
  >
  > *If an attacker attempts to submit an impossible ledger—for instance, an outbound transfer where the origin balance increases—the system immediately rejects it with a 422 schema validation error.*
  >
  > *Now, let's click 'Load Sample: Fraud-Like Drain'. Notice that origin balance drains completely from $850,000 to $0 on a high-value transfer. Unlike evaluation datasets, real incoming transactions never fabricate a ground-truth label—`is_fraud` is set to null.*
  >
  > *Let's click 'Save & Run Agents Live'. The transaction is instantly committed to the ledger, and FinGuard triggers the live orchestration pipeline."*

---

### Segment 3: Live 10-Agent LangGraph Workflow View (1:30 – 2:30)
* **Action**: Transition to the **Agent Workflow** page (`/agents`).
* **Spoken Script**:
  > *"Here is FinGraph in real time. We are connected via Server-Sent Events directly to the LangGraph execution graph.*
  >
  > *Watch the horizontal pipeline strip at the top: each of our ten specialized agents transitions from Waiting to a pulsing Running state, and finally Completed.*
  >
  > *Notice our dynamic conditional routing: for routine payments under a composite risk of 30, the Supervisor triggers our Fast-Track route, skipping forensic nodes and saving 80% compute.*
  >
  > *For this high-risk transfer, all ten nodes execute: Intake validates the payload, Data Quality confirms zero target leakage, Fraud Detection runs Random Forest inference, Market & Credit Risk calculates Value-at-Risk exposure, and Investigation traces the rapid account liquidation.*
  >
  > *Down in the timeline, watch the Explainability Agent: tokens stream in live directly from the Groq Llama-3.3-70B model, synthesizing TreeSHAP attributions and regulatory citations into an objective, factual report.*
  >
  > *Finally, the Audit & Reporting Agent seals the docket with a SHA-256 cryptographic hash."*

---

### Segment 4: Investigation Dossier, 4-Eyes Review & Replay (2:30 – 3:15)
* **Action**: Click **Case Investigations** (`/investigations`). Select **CASE-FG-000199**.
* **Spoken Script**:
  > *"Now let's view this from the investigator's seat. Under our Four-Eyes Principle, AI never executes disruptive actions autonomously.*
  >
  > *On the case workbench, we don't have mock data: each case displays its verified multi-agent trace, complete with exact TreeSHAP waterfall values and statutory citations to FATF Recommendation 16 and AML-04.*
  >
  > *Clicking 'Replay Agent Run Live' allows auditors or compliance supervisors to re-execute the exact event sequence on-demand.*
  >
  > *Our investigator reviews the evidence, selects the disposition—such as 'Escalate to SAR'—enters their audited findings, and commits. The review is cryptographically timestamped and logged."*

---

### Segment 5: Grounded RAG Refusal & Cryptographic Audit Verification (3:15 – 4:00)
* **Action**: Click **FinGuard Assistant** (`/assistant`), then **Governance & Audit** (`/governance`).
* **Spoken Script**:
  > *"In our AI Risk Assistant, our RAG pipeline enforces a strict refusal threshold. If an analyst asks an out-of-scope question—such as recipes or unsupported policies—the system refuses to hallucinate, explicitly stating that verified policy guidance is unavailable.*
  >
  > *When asking about rapid liquidation under AML-04, it answers with exact document, section, and page citations.*
  >
  > *Finally, under Governance & Audit, every single event in FinGuard forms a SHA-256 tamper-evident hash chain. Let's click 'Verify Chain Integrity'. The backend walks the chain from genesis to the latest event block, verifying mathematical continuity.*
  >
  > *This is FinGuard: autonomous multi-agent intelligence, verifiable grounding, and uncompromising institutional trust."*

