# FinGuard Data Dictionary: PaySim Dataset & Engineered Signals

## 1. Raw PaySim Synthetic Dataset Schema

| Column Name | Data Type | Description | Target Leakage Status |
| :--- | :--- | :--- | :--- |
| `step` | Integer | Simulated hour unit of time (1 step = 1 hour). Total simulation ~744 steps (31 days). | Permitted Feature |
| `type` | String | Transaction rail category: `PAYMENT`, `TRANSFER`, `CASH_OUT`, `DEBIT`, `CASH_IN`. | Permitted Feature (One-Hot Encoded) |
| `amount` | Float | Amount of the transaction in local currency units. | Permitted Feature (Log Transformed) |
| `nameOrig` | String | Synthetic identifier of transaction origin account (e.g., `C1231006815`). | Entity Metadata |
| `oldbalanceOrg`| Float | Initial balance of origin account prior to transaction execution. | Permitted Feature |
| `newbalanceOrig`| Float | Updated balance of origin account subsequent to transaction execution. | Permitted Feature (Audited) |
| `nameDest` | String | Synthetic identifier of destination account (`M...` for merchant, `C...` for customer). | Permitted Feature (`dest_is_merchant`) |
| `oldbalanceDest`| Float | Initial balance of recipient before transaction. | Permitted Feature |
| `newbalanceDest`| Float | New balance of recipient after transaction. | Permitted Feature (Audited) |
| `isFraud` | Integer | Ground-truth historical label (1 = fraud, 0 = legitimate). | **STRICT TARGET - NEVER USED AS INPUT FEATURE** |
| `isFlaggedFraud`| Integer | Historical simple rule flag (transactions > 200,000). | **FORBIDDEN FEATURE - TARGET LEAKAGE** |

---

## 2. Engineered Risk Features

FinGuard applies strict feature sanitization via `LeakageGuard` before training or inference:

1. `amount_log`: `np.log1p(amount)` — normalizes heavy-tailed financial values.
2. `orig_balance_delta`: `oldbalanceOrg - newbalanceOrig` — raw funds outflow from origin.
3. `dest_balance_delta`: `newbalanceDest - oldbalanceDest` — raw funds inflow to recipient.
4. `orig_balance_error`: `(oldbalanceOrg - amount) - newbalanceOrig` — reveals ledger accounting discrepancy (bypasses).
5. `dest_balance_error`: `(oldbalanceDest + amount) - newbalanceDest` — reveals destination accounting anomalies.
6. `is_zero_orig`: Binary indicator if origin started with zero balance (`oldbalanceOrg == 0`).
7. `is_dest_zero_init`: Binary indicator if destination had zero prior balance.
8. `is_account_cleared`: Binary flag (`newbalanceOrig == 0 and oldbalanceOrg > 0`) indicating complete account liquidation.
9. `dest_is_merchant`: Binary flag indicating if recipient is registered merchant (`nameDest.startswith('M')`).
10. `hour_of_day`: `step % 24` — captures temporal cyclical behavior.
11. `type_CASH_OUT`, `type_TRANSFER`, `type_PAYMENT`, `type_CASH_IN`, `type_DEBIT`: One-hot encoded transaction channels.
