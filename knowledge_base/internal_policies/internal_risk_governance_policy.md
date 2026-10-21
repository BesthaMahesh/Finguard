# FinGuard Enterprise Model Governance & Human-in-the-Loop Policy
Document ID: GOV-AI-2024-09
Version: 1.5
Authority: Enterprise AI Ethics & Risk Oversight Committee

## 1. Principle of Decision Support (Model Scores vs. Verified Fraud)
- **Distinction Between Model Scores and Verified Fraud**: An automated ML fraud score or composite risk score is a statistical probability indicator used for triage and prioritization. It does **not** constitute verified, confirmed, or legally actionable fraud.
- **Non-Autonomous Finality**: FinGuard operates strictly as an AI-powered Decision Support System. Under no circumstances may an automated ML score, agent workflow, or LLM explanation execute an autonomous, unreviewed filing of a criminal Suspicious Activity Report (SAR) or irreversible legal enforcement.
- **Human Verification Requirement**: Automated models triage, prioritize, alert, and draft investigation dockets. Establishing verified fraud requires investigative corroboration, evidentiary review, and formal sign-off by an authorized human investigator under the Four-Eyes principle.

## 2. Thresholds for Mandatory Human Review
- Risk Score >= 70.0: Mandatory Level 2 Investigator review required.
- Operational Action "FREEZE_ACCOUNT": Requires dual authorization (4-Eyes Principle) from Investigator and Risk Manager.
- High Discrepancy Flag: Transactions with ledger variance > $10,000 must be routed to Core Banking Reconciliation.

## 3. Explainability and Fairness Mandates
- Every automated risk alert must provide intelligible feature attributions (SHAP scores or transparent rule triggers).
- Blanket "black-box" rejections are strictly prohibited under consumer protection regulations.

## 4. Handling Unsupported Inquiries and Insufficient Policy Evidence
- **Strict Abstention Guarantee**: When an investigator inquiry is not supported by indexed regulatory policies or verified operational procedures, the platform must withhold automated synthesis to prevent hallucination.
- **Human Escalation**: The system must explicitly issue an Insufficient Policy Evidence notice and direct the user to consult the Financial Crimes Intelligence Manual or file an escalation with the Chief Risk Office (CRO).

