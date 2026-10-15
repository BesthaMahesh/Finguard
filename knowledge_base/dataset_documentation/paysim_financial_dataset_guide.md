---
title: PaySim Synthetic Financial Dataset Documentation
category: dataset_documentation
source_type: dataset_documentation
version: "1.0"
dataset_name: PaySim Synthetic Financial Transactions
author: FinGuard Data & ML Engineering
---

# PaySim Synthetic Financial Dataset Documentation

## 1. Overview and Simulation Mechanics
PaySim simulates mobile money transactions based on a sample of real financial logs from an African mobile financial services operator. The dataset contains 6,362,620 transactions spanning 744 time simulation steps (representing 30 days of synthetic activity).

## 2. Feature Schema and Attribute Definitions
- `step`: Maps a unit of time in the real world. 1 step is 1 hour. Total simulation steps = 744 (30 days).
- `type`: Transaction category. Permitted values:
  - `PAYMENT`: Routine consumer merchant payment.
  - `TRANSFER`: Funds transfer between customers.
  - `CASH_OUT`: Withdrawal of cash balance through an agent.
  - `DEBIT`: Bank debit transaction.
  - `CASH_IN`: Cash deposit into an account through an agent.
- `amount`: Transacted amount in local fiat currency.
- `nameOrig`: Customer ID initiating the transaction (starts with 'C').
- `oldbalanceOrg`: Initial account balance before the transaction.
- `newbalanceOrig`: Balance of the origin account following the transaction.
- `nameDest`: Recipient customer ID ('C...') or merchant ID ('M...').
- `oldbalanceDest`: Initial recipient balance before the transaction.
- `newbalanceDest`: Recipient balance after the transaction.
- `isFraud`: Ground-truth binary flag where 1 denotes fraudulent activity.
- `isFlaggedFraud`: Baseline business rule flag identifying unauthorized transfer attempts exceeding 200,000 currency units.

## 3. Fraud Characteristics and Imbalance
Fraud occurs almost exclusively in `TRANSFER` and `CASH_OUT` transaction types. The positive fraud prevalence is approximately 0.13%, representing extreme class imbalance requiring precision-recall optimization (PR-AUC) and careful decision threshold calibration.
