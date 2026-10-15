# Standard Operating Procedure: Anti-Money Laundering & Rapid Liquidation (AML-04)
Document ID: POL-AML-2024-04
Version: 3.2
Effective Date: 2024-01-15
Authority: Global Financial Compliance & Risk Office
Applicability: Global Transaction Monitoring & Fraud Intelligence

## 1. Overview and Objective
This procedure establishes operational standards for detecting, triaging, and escalating suspicious transactions characterized by anomalous rapid movement of funds. Such mechanisms frequently signify money mule networks, account takeover, or layered illicit proceeds.

## 2. Key Risk Typologies
### 2.1 Pass-Through and Immediate Cash-Out (Mule Activity)
- Definition: An account receives funds via electronic wire or peer-to-peer transfer (`TRANSFER`), immediately followed by an equivalent or near-equivalent withdrawal (`CASH_OUT`) within a short temporal window (typically within step intervals of 1 to 24 hours).
- Indicator: Origin balance drops to zero or near-zero, leaving an account balance of less than 1% of the pre-transaction balance.

### 2.2 Ledger Accounting Discrepancies
- Indicator: Where the reported transaction amount does not reconcile with the ledger balance differential: `(oldbalanceOrg - amount) != newbalanceOrig`.
- Threshold: Any unexplained variance exceeding 1.0 currency unit must be escalated for forensic reconciliation and marked as potential ledger tampering or bypass fraud.

## 3. Escalation and Threshold Matrix
- **Tier 1 (Automated Monitoring)**: Risk score below 40.0. Standard routine logging.
- **Tier 2 (Investigator Triage)**: Risk score between 40.0 and 69.9. Flagged for queue review within 48 hours.
- **Tier 3 (Enhanced Due Diligence & Freeze Checkpoint)**: Risk score >= 70.0. Requires mandatory human review (4-Eyes principle) prior to account closure or external SAR filing.
- **Large Value Trigger**: Single transaction volume exceeding 200,000 currency units initiates mandatory enhanced verification.

## 4. Regulatory Reporting Guidance (SAR / STR)
Under Financial Action Task Force (FATF) Recommendation 16 and FinCEN SAR rules, investigators must document:
1. Transaction timestamp, step, and reference identifiers.
2. Inferred origin and destination entities.
3. Quantified risk score and specific machine learning model signals.
4. Explanatory features and justification for disposition.
