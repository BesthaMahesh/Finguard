# Financial Fraud Typologies & Investigation Playbook (FTP-01)
Document ID: POL-FRAUD-2024-01
Version: 2.1
Authority: Financial Crimes Intelligence Unit

## 1. Account Takeover (ATO) Characteristics
- Initial high-frequency balance checks followed by an abrupt liquidation.
- Disproportionately high transfer amounts compared to historical customer behavior.
- Complete liquidation of the origin balance (`newbalanceOrig = 0.0`) in a single execution step.
- Destination account is often newly created or possesses no substantial preceding activity.

## 2. Synthetic Identity & Shell Entity Indicators
- Destination account received funds but does not update legitimate destination balance appropriately (`newbalanceDest == oldbalanceDest` despite inbound funds).
- Identifier prefixes starting with synthetic customer codes (`C`) without verified KYC merchant registration (`M`).

## 3. Investigatory Checkpoints
1. Validate whether the counterparty is a registered merchant. Transactions with merchant entities (`M`) have lower historical fraud rates and represent commercial activity unless linked to an unauthorized merchant aggregation scheme.
2. Cross-reference SHAP feature contributions to ensure model decisions are grounded in behavioral flags (e.g., origin balance delta, liquidation drain) rather than random noise.
3. Record all forensic timeline events in the immutable audit trail.
