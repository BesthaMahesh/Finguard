# FinGuard Enterprise Model Card: Random Forest Classifier v1.2

## Model Details
- **Model Name**: FinGuard PaySim Random Forest Classifier
- **Version**: `v1.2.0-rf-enterprise`
- **Architecture**: `RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=5, class_weight='balanced_subsample', random_state=42)`
- **Explainability**: TreeSHAP (`shap.TreeExplainer`)
- **Release Date**: October 2026

## Intended Use
- **Primary Domain**: Decision-support prioritization of suspicious transactions for financial crime investigators.
- **Intended Users**: Risk Analysts, Senior Investigators, Compliance Officers.
- **Out-of-Scope Use**: Autonomous unilateral prosecution or asset forfeiture without human review.

## Empirical Evaluation Metrics (Test Set)
- **PR-AUC (Precision-Recall Area Under Curve)**: **0.9449**
- **ROC-AUC (Receiver Operating Characteristic)**: **0.9844**
- **F1-Score (at operational threshold 0.65)**: **0.9412**
- **Precision**: **0.9231**
- **Recall**: **0.9600**
- **Decision Threshold**: **0.65**

## Empirical Confusion Matrix
- **True Negatives (TN)**: 27,002
- **False Positives (FP)**: 4
- **False Negatives (FN)**: 2
- **True Positives (TP)**: 48

## Training Data & Target Leakage Prevention
- **Source**: PaySim Synthetic Dataset (6.3M raw transactions simulated across 31 days).
- **Leakage Guard**: Strict programmatic removal of `isFraud` and `isFlaggedFraud` prior to feature matrix generation.
- **Imbalance Handling**: Subsample-balanced tree weighting addressing the extreme 0.13% base rate of financial fraud.

## Ethical & Governance Considerations
- **Non-Autonomous Finality**: The model serves strictly as an advisory triage signal.
- **Explainability Mandate**: Every score is accompanied by local TreeSHAP feature attributions and deterministic rule triggers.
