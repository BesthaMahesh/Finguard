import os
import logging
import joblib
from typing import Dict, Any, List, Tuple
from backend.ml.features import extract_features_single
from backend.ml.explainability_service import ExplainabilityService
from backend.core.config import settings

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, model_path: str = "./models/finguard_rf_model.joblib"):
        self.model_path = model_path
        self._model = None
        self.explainability_service = ExplainabilityService()

    def _ensure_model(self):
        if self._model is None:
            if os.path.exists(self.model_path):
                try:
                    self._model = joblib.load(self.model_path)
                    logger.info("Loaded trained Random Forest model successfully.")
                except Exception as e:
                    logger.error(f"Failed to load model from {self.model_path}: {e}")
            else:
                logger.warning(f"Model file not found at {self.model_path}. Running with deterministic heuristic fallback until trained.")

    def predict_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes ML fraud probability prediction, applies deterministic rules,
        calculates composite operational risk score, and determines review requirement.
        """
        self._ensure_model()
        X_df = extract_features_single(tx_data)

        # 1. Machine Learning Model Score
        if self._model is not None:
            try:
                probs = self._model.predict_proba(X_df)[0]
                fraud_prob = float(probs[1])  # probability of positive class
            except Exception as e:
                logger.error(f"Model inference failed: {e}")
                fraud_prob = self._heuristic_prob(tx_data)
        else:
            fraud_prob = self._heuristic_prob(tx_data)

        # 2. Deterministic Rule Engine (Transparent, audited rules)
        rules_triggered = self._evaluate_rules(tx_data)

        # 3. Transparent Composite Risk Scoring (0 to 100)
        # Note: We clearly separate the ML model probability and the operational priority
        # Model contributes 60% of baseline weight, deterministic rule violations add operational severity
        base_score = fraud_prob * 60.0
        rule_penalty = sum(r["penalty"] for r in rules_triggered)
        raw_score = base_score + rule_penalty
        risk_score = round(min(100.0, max(0.0, raw_score)), 1)

        # 4. Operational Risk Level Categorization
        if risk_score >= 85.0:
            risk_level = "CRITICAL"
            requires_human_review = True
        elif risk_score >= 65.0:
            risk_level = "HIGH"
            requires_human_review = True
        elif risk_score >= 40.0:
            risk_level = "MEDIUM"
            requires_human_review = False
        else:
            risk_level = "LOW"
            requires_human_review = False

        # 5. Explainability (SHAP feature contributions)
        feature_contributions = self.explainability_service.explain_transaction(tx_data)

        return {
            "fraud_probability": round(fraud_prob, 4),
            "predicted_fraud": 1 if fraud_prob >= settings.FRAUD_THRESHOLD else 0,
            "threshold_used": settings.FRAUD_THRESHOLD,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "requires_human_review": requires_human_review,
            "rule_flags": rules_triggered,
            "feature_contributions": feature_contributions[:6]  # Top 6 most impactful factors
        }

    def _evaluate_rules(self, tx_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Deterministic compliance & fraud pattern rules.
        """
        triggered = []
        amount = float(tx_data.get("amount", 0.0))
        tx_type = str(tx_data.get("type", "")).upper()
        old_orig = float(tx_data.get("oldbalanceOrg", tx_data.get("old_balance_org", 0.0)))
        new_orig = float(tx_data.get("newbalanceOrig", tx_data.get("new_balance_orig", 0.0)))
        dest = str(tx_data.get("nameDest", tx_data.get("name_dest", "")))

        # Rule 1: Complete Account Drain
        if tx_type in ("TRANSFER", "CASH_OUT") and old_orig > 0 and new_orig == 0 and amount >= old_orig * 0.95:
            triggered.append({
                "rule_id": "RULE_LIQUIDATION_DRAIN",
                "name": "Full Account Liquidation",
                "description": "Entire origin balance was drained to zero via high-risk liquidation channel.",
                "severity": "HIGH",
                "penalty": 25.0
            })

        # Rule 2: Origin Ledger Discrepancy
        orig_expected = old_orig - amount
        if tx_type in ("TRANSFER", "CASH_OUT") and abs(orig_expected - new_orig) > 1.0:
            triggered.append({
                "rule_id": "RULE_LEDGER_INCONSISTENCY",
                "name": "Accounting Ledger Discrepancy",
                "description": f"Origin balance difference does not tally with transaction amount (discrepancy of {abs(orig_expected - new_orig):.2f}).",
                "severity": "CRITICAL",
                "penalty": 20.0
            })

        # Rule 3: High-Value Threshold Exposure
        if amount >= 200000.0:
            triggered.append({
                "rule_id": "RULE_HIGH_VALUE_THRESHOLD",
                "name": "Large Value Exposure (>200,000 units)",
                "description": "Transaction amount exceeds enterprise high-value monitoring threshold.",
                "severity": "MEDIUM",
                "penalty": 15.0
            })

        # Rule 4: Rapid Outflow from Zero Baseline
        if old_orig == 0.0 and amount > 0:
            triggered.append({
                "rule_id": "RULE_ZERO_BALANCE_OUTFLOW",
                "name": "Outflow from Zero Balance Ledger",
                "description": "Transaction initiated despite origin recorded starting balance of zero.",
                "severity": "HIGH",
                "penalty": 15.0
            })

        # Safeguard Rule: Legitimate Merchant Payment
        if tx_type == "PAYMENT" and dest.startswith("M"):
            triggered.append({
                "rule_id": "SAFEGUARD_VERIFIED_MERCHANT",
                "name": "Standard POS/Merchant Settlement",
                "description": "Routine merchant transaction pattern. Reduces synthetic risk weight.",
                "severity": "INFO",
                "penalty": -20.0
            })

        return triggered

    def _heuristic_prob(self, tx_data: Dict[str, Any]) -> float:
        """Deterministic fallback probability calculation."""
        amount = float(tx_data.get("amount", 0.0))
        tx_type = str(tx_data.get("type", "")).upper()
        old_orig = float(tx_data.get("oldbalanceOrg", tx_data.get("old_balance_org", 0.0)))
        new_orig = float(tx_data.get("newbalanceOrig", tx_data.get("new_balance_orig", 0.0)))

        prob = 0.02
        if tx_type in ("TRANSFER", "CASH_OUT"):
            prob += 0.25
            if old_orig > 0 and new_orig == 0:
                prob += 0.45
            if amount > 100000:
                prob += 0.15
        elif tx_type == "PAYMENT":
            prob = 0.01
        return min(0.99, prob)

model_service = ModelService()
