# FinGuard Model Evaluation & Quality Assurance Guide

## 1. Class Imbalance Strategy
Financial fraud datasets typically exhibit acute class imbalance (PaySim features approximately 0.13% positive fraud cases). Conventional accuracy is an uninformative metric: a trivial classifier predicting 100% negative achieves 99.87% accuracy while intercepting zero fraud.

FinGuard emphasizes:
1. **Precision-Recall Area Under Curve (PR-AUC)** as the primary target metric.
2. **ROC-AUC** for discriminatory separability across probability thresholds.
3. **Balanced Subsampling (`balanced_subsample`)** in Random Forest decision trees to calibrate leaf impurity without over-fitting.

## 2. Threshold Optimization & Operating Cost Curves
Instead of defaulting to an uncalibrated 0.50 threshold, FinGuard evaluates operational cost trade-offs:
- **Low Threshold (0.20 - 0.35)**: Maximizes recall (intercepts 99%+ of frauds) at the expense of elevated operational workload from false positives.
- **Calibrated Operational Threshold (0.65)**: Minimizes analyst fatigue with high precision (0.9231) while preserving high recall (0.9600), delivering an optimal F1-score of 0.9412.
- **High Threshold (0.85)**: Reserved for urgent automated quarantine actions.

## 3. Drift Monitoring Design
FinGuard continuously monitors:
- **Population Stability Index (PSI)** on numerical feature distributions (`amount_log`, `orig_balance_delta`).
- **Concept Drift**: Shifts in empirical precision and recall observed during human reviewer disposition outcomes.
