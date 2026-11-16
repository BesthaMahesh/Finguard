# FinGuard 4-Minute Executive Demo Script

> **Target Audience**: Financial Crime Risk Directors, Engineering Leads, and Compliance Officers.  
> **Duration**: 4 minutes  
> **Theme**: Explainable, Agentic AI for Financial Risk with Human-in-the-Loop Governance.

---

## ⏱️ Timeline Summary

| Time | Segment | Screen / Route | Core Message |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:45** | 1. Enterprise Architecture & Overview | `/overview` (Executive Dashboard) | 9-layer architecture, 10 specialized agents, single source of truth metrics, 12,000 historical baseline + N live transactions. |
| **0:45 – 1:30** | 2. Transaction Ingestion & Ledger Safeguard | `/transactions` (Transactions Table) | + Add Transaction modal, live variance warnings, statutory rule floors (`max(ML, floor)`), auto-case escalation. |
| **1:30 – 2:30** | 3. Live 10-Agent LangGraph Workflow | `/agents` (Agent Workflow) | Real SSE streaming, fast-track conditional routing, what-if simulation mode, live Groq token typewriter with post-generation validator. |
| **2:30 – 3:15** | 4. Investigation Dossier & 4-Eyes Review | `/investigations` (Case Workbench) | Server-enforced 4-Eyes separation (submitter cannot approve own case), structured evidence citation, stored trace replay. |
| **3:15 – 4:00** | 5. RAG Refusal & Cryptographic Audit Chain | `/assistant` & `/governance` | Strict RAG refusal on out-of-scope queries, claim-level citations, SHA-256 genesis-to-tip hash chain verification. |

---

## 🎙️ Spoken Walkthrough

### Segment 1: Enterprise Architecture & Executive Overview (0:00 – 0:45)
* **Action**: Start on the **Risk Dashboard** (`/overview`).
* **Spoken Script**:
  > *"Welcome to FinGuard, an autonomous financial risk intelligence and fraud investigation platform. Unlike black-box detection systems, FinGuard is built on an exact nine-layer enterprise architecture powered by a stateful LangGraph graph of ten specialized agents.*
  >
  > *On our executive dashboard, all KPIs are unified from a single source of truth: our Random Forest classifier achieves a 0.9844 ROC-AUC, 0.9449 PR-AUC, and 0.9412 F1-score with 0.9445 balanced accuracy. Crucially, we treat PaySim synthetic limitations honestly: balance error features are strictly quarantined through our `LeakageGuard` before model ingestion.*
  >
  > *Notice our live dataset counters: exactly 12,000 historical transactions plus live-entered transactions, and 23 active cases awaiting human investigator review under the mandatory Four-Eyes principle."*

---

### Segment 2: Transaction Ingestion & Statutory Rule Floors (0:45 – 1:30)
* **Action**: Click **Transactions** in the sidebar. Click the primary cyan **"+ Add Transaction"** button.
* **Spoken Script**:
  > *"Let's ingest a live transaction. FinGuard provides deterministic ledger reconciliation.*
  >
  > *Notice as I enter a high-value transfer with an impossible balance change or merchant destination with a nonzero balance, the UI immediately surfaces an inline forensic reconciliation warning.*
  >
  > *Rather than blinding the compliance team, FinGuard permits forensic anomaly ingestion while enforcing statutory rule floors: composite risk is computed as `max(ML-based score, rule floor)`. Any major ledger variance (> $10,000) or impossible merchant balance enforces a statutory floor of 70 (HIGH risk), mandating Level 2 investigator review regardless of ML probability.*
  >
  > *We also provide an 'Auto-fill balances from amount' helper for routine data entry.*
  >
  > *Let's click 'Save & Run Agents Live'. The transaction is committed with audit warnings, and FinGuard triggers the live orchestration pipeline."*

---

### Segment 3: Live 10-Agent LangGraph Workflow View (1:30 – 2:30)
* **Action**: Transition to the **Agent Workflow** page (`/agents`).
* **Spoken Script**:
  > *"Here is FinGuard in real time. We are connected via Server-Sent Events directly to the LangGraph execution graph.*
  >
  > *Watch the horizontal pipeline strip at the top: each of our ten specialized agents transitions from Waiting to a pulsing Running state, and finally Completed.*
  >
  > *Notice our dynamic conditional routing: for routine payments under a composite risk of 30, the Supervisor triggers our Fast-Track route, skipping forensic nodes and saving 80% compute.*
  >
  > *For anomalous or elevated transactions, all ten nodes execute: Intake normalizes decimals, Data Quality executes deterministic ledger reconciliation, Fraud Detection runs Random Forest inference, Market & Credit Risk calculates Value-at-Risk exposure, and Investigation traces counterparty velocity.*
  >
  > *When looking up an existing database transaction, records are locked read-only with a lock icon. Investigators can click 'Edit as what-if simulation' to experiment with counterfactual parameters without polluting database records or creating spurious cases.*
  >
  > *Down in the timeline, watch the Explainability Agent: tokens stream in live directly from Groq Llama-3.3-70B. Our post-generation validator ensures the LLM receives structured facts only and never hallucinates mitigating words like 'neutralized' to undermine the statutory risk score.*
  >
  > *Finally, the Audit & Reporting Agent seals the docket with a SHA-256 cryptographic hash."*

---

### Segment 4: Investigation Dossier, 4-Eyes Review & Replay (2:30 – 3:15)
* **Action**: Click **Case Investigations** (`/investigations`). Select **CASE-FG-000199**.
* **Spoken Script**:
  > *"Now let's view this from the investigator's seat. Under our Four-Eyes Principle, AI never executes disruptive actions autonomously.*
  >
  > *Crucially, FinGuard enforces strict 4-Eyes separation both client-side and server-side: the analyst who submitted the transaction cannot approve their own case disposition—any such attempt returns HTTP 403 Forbidden with an audit log alert.*
  >
  > *On the workbench, the disposition decision defaults to unselected, requiring the investigator to explicitly check verified evidence boxes (such as Rapid Liquidation or Counterparty Velocity) and write at least 30 characters of factual notes before committing.*
  >
  > *Clicking 'Replay agent run' allows auditors or compliance supervisors to re-execute the exact event sequence on-demand with stored trace fidelity."*

---

### Segment 5: Grounded RAG Refusal & Cryptographic Audit Verification (3:15 – 4:00)
* **Action**: Click **FinGuard Assistant** (`/assistant`), then **Governance & Audit** (`/governance`).
* **Spoken Script**:
  > *"In our AI Risk Assistant, our RAG pipeline enforces a strict refusal threshold. If an analyst asks an out-of-scope question—such as recipes or unrelated topics—the system refuses to hallucinate, explicitly stating that verified policy guidance is unavailable.*
  >
  > *When asking about rapid liquidation under AML-04, it answers with concise, claim-level citations without meaningless 'Page None' tags.*
  >
  > *Finally, under Governance & Audit, every single event in FinGuard forms a SHA-256 tamper-evident hash chain. Let's click 'Verify Chain Integrity'. The backend walks the chain from genesis to the latest event block, verifying mathematical continuity.*
  >
  > *If test data needs to be purged, administrators can trigger our one-click 'Reset to Canonical Demo Data' to restore the exact 12,000 historical transactions and 25 baseline cases.*
  >
  > *This is FinGuard: autonomous multi-agent intelligence, verifiable grounding, and uncompromising institutional trust."*
