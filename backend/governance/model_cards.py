from typing import Dict, Any
from datetime import datetime

class ModelGovernance:
    """
    Model Governance and Responsible AI registry according to FATF and regulatory standards.
    """
    @staticmethod
    def get_model_card() -> Dict[str, Any]:
        return {
            "model_details": {
                "name": "FinGuard PaySim Random Forest Classifier",
                "version": "v1.2.0-rf-enterprise",
                "developer": "FinGuard Autonomous Risk Engineering Team",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "license": "Internal Enterprise Proprietary & Decision Support",
                "architecture": "RandomForestClassifier(n_estimators=100, max_depth=10, balanced_subsample)",
                "frameworks": ["scikit-learn 1.5+", "SHAP 0.45+", "FastAPI", "LangGraph"]
            },
            "intended_use": {
                "primary_use": "Decision-support triage and prioritization of suspicious transaction activity.",
                "target_users": "Financial Crime Analysts, Fraud Investigators, Compliance Officers.",
                "out_of_scope_uses": "Automated criminal indictment, autonomous unilateral credit freezes without 4-Eyes human investigator review, production banking without real-time transaction gateway integration."
            },
            "training_data_and_features": {
                "dataset_source": "PaySim Financial Synthetic Log (Kaggle ealaxi/paysim1)",
                "feature_count": 15,
                "target_leakage_safeguards": "Strictly excludes isFraud and isFlaggedFraud; engineered accounting balance differentials audit ledger tampering without outcome leakage.",
                "synthetic_assumptions": "Simulated multi-agent customer transactions; merchant accounts designated with 'M' prefix, individual retail with 'C'."
            },
            "performance_and_metrics": {
                "operational_threshold": 0.65,
                "target_metric_focus": "Precision-Recall Area Under Curve (PR-AUC) and operational false-positive minimization.",
                "calibration": "Platt-scaling / isotonic threshold evaluation across 0.20 to 0.85 bounds."
            },
            "ethical_and_fairness_considerations": {
                "bias_mitigation": "Evaluated across counterparty types (Merchant vs Customer) to prevent structural over-penalization.",
                "explainability": "Mandatory SHAP TreeExplainer attributions generated for all elevated scores.",
                "human_oversight": "Mandatory Human-in-the-Loop review for any action classified as HIGH or CRITICAL."
            }
        }
