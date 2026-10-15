# FinGuard Enterprise Model Governance & Human-in-the-Loop Policy
Document ID: GOV-AI-2024-09
Version: 1.5
Authority: Enterprise AI Ethics & Risk Oversight Committee

## 1. Principle of Decision Support (Non-Autonomous Finality)
- FinGuard is an AI-powered Decision Support System. Under no circumstances may an automated ML score, agent workflow, or LLM explanation execute an autonomous, unreviewed filing of a criminal Suspicious Activity Report (SAR) or irreversible legal enforcement.
- Automated models may triage, prioritize, alert, and draft investigation dockets. Final disposition requires review and sign-off by an authorized human investigator.

## 2. Thresholds for Mandatory Human Review
- Risk Score >= 70.0: Mandatory Level 2 Investigator review required.
- Operational Action "FREEZE_ACCOUNT": Requires dual authorization (4-Eyes Principle) from Investigator and Risk Manager.
- High Discrepancy Flag: Transactions with ledger variance > $10,000 must be routed to Core Banking Reconciliation.

## 3. Explainability and Fairness Mandates
- Every automated risk alert must provide intelligible feature attributions (SHAP scores or transparent rule triggers).
- Blanket "black-box" rejections are strictly prohibited under consumer protection regulations.
