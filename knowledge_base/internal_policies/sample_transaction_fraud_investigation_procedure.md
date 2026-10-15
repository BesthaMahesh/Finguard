---
title: Transaction Fraud Investigation Procedure
category: fraud_patterns
source_type: sample_internal_policy
version: "1.0"
author: FinGuard Financial Crime Risk Committee
effective_date: "2026-01-15"
classification: SAMPLE_INTERNAL_POLICY
---

# Transaction Fraud Investigation Procedure

## 1. Purpose and Scope
This document outlines standard operating procedures for investigating flagged anomalies, rapid account liquidations, and high-value wire transfers detected across FinGuard risk monitoring systems. 

> **Important Notice:** This is a sample internal policy template intended for operational guidelines and simulated procedural compliance. It does not supersede statutory directives issued by statutory regulators (such as RBI, FinCEN, or FATF).

## 2. High-Risk Transfer Thresholds and Immediate Actions
For all domestic and cross-border fund transfers:
- **Transactions exceeding $200,000 USD** or local equivalent with an AI Composite Risk Score ≥ 65.0 must undergo immediate second-level investigator authorization (Four-Eyes Principle).
- **Full Account Depletion**: Transactions where the origin account balance is reduced to zero (`newbalanceOrig == 0`) while transferring greater than 80% of historical average balance trigger an immediate 4-hour settlement hold pending source-of-funds verification.

## 3. Account Takeover (ATO) and Rapid Liquidation Typologies
When reviewing rapid liquidation alerts:
- Cross-reference origin account velocity over the preceding 72 hours.
- Verify whether the destination counterparty is a newly registered beneficiary (`nameDest` active < 48 hours).
- In the event of mismatched ledger state or balance anomalies, freeze outbound credit and notify the AML reporting officer.

## 4. Four-Eyes Principle and Escalation
1. Any analyst identifying confirmed indicators of compromise must escalate the case docket to Senior Investigator status within 30 minutes.
2. If confirmed fraud probability exceeds 0.85, a Suspicious Activity Report (SAR / STR) draft docket must be initialized automatically.
3. Final disposition requires dual cryptographic signatures from the Lead Investigator and Compliance Director.
