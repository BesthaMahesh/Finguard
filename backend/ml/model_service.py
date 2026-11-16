import os
import logging
import math
import joblib
from typing import Dict, Any, List, Tuple
from backend.ml.features import extract_features_single
from backend.ml.explainability_service import ExplainabilityService
from backend.core.config import settings
from backend.core.decision_policy import evaluate_decision_policy

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
        calculates composite operational risk score with guaranteed rule floors,
        and determines review requirements via the unified Decision Policy.
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

        # 2. Deterministic Rule Engine (Transparent, audited rules with statutory floors)
        rules_triggered = self._evaluate_rules(tx_data)

        # 3. Transparent Composite Risk Scoring (0 to 100)
        # Model contributes up to 60% baseline, rules contribute operational penalties.
        # CRITICAL POLICY: Composite score is max(raw_score, rule_floor), never lower than a triggered rule floor.
        base_score = fraud_prob * 60.0
        rule_penalty = sum(r.get("penalty", 0.0) for r in rules_triggered)
        raw_score = base_score + rule_penalty
        rule_floor = max([r.get("floor", 0.0) for r in rules_triggered], default=0.0)
        composite_score = max(raw_score, rule_floor)
        risk_score = round(min(100.0, max(0.0, composite_score)), 1)

        # 4. Operational Decision Policy (Single Source of Truth)
        rule_ids = [r.get("rule_id", "") for r in rules_triggered]
        policy_verdict = evaluate_decision_policy(
            risk_score=risk_score,
            rule_flags=rule_ids,
            data_quality_flags=[],
            transaction=tx_data
        )

        # 5. Explainability (SHAP feature contributions)
        feature_contributions = self.explainability_service.explain_transaction(tx_data)

        return {
            "fraud_probability": round(fraud_prob, 4),
            "predicted_fraud": 1 if fraud_prob >= settings.FRAUD_THRESHOLD else 0,
            "threshold_used": settings.FRAUD_THRESHOLD,
            "risk_score": risk_score,
            "risk_level": policy_verdict.risk_tier,
            "requires_human_review": policy_verdict.requires_human_review,
            "decision": policy_verdict.decision,
            "rule_flags": rules_triggered,
            "feature_contributions": feature_contributions[:6]  # Top 6 most impactful factors
        }

    def _evaluate_rules(self, tx_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Deterministic compliance & fraud pattern rules.
        Enforces statutory rule floors (AML-04, FATF Rec 16).
        """
        triggered = []
        try:
            amount = float(tx_data.get("amount", 0.0))
            old_orig = float(tx_data.get("oldbalanceOrg", tx_data.get("old_balance_org", 0.0)))
            new_orig = float(tx_data.get("newbalanceOrig", tx_data.get("new_balance_orig", 0.0)))
            old_dest = float(tx_data.get("oldbalanceDest", tx_data.get("old_balance_dest", 0.0)))
            new_dest = float(tx_data.get("newbalanceDest", tx_data.get("new_balance_dest", 0.0)))
        except (ValueError, TypeError):
            amount, old_orig, new_orig, old_dest, new_dest = 0.0, 0.0, 0.0, 0.0, 0.0

        tx_type = str(tx_data.get("type", "")).upper()
        dest = str(tx_data.get("nameDest", tx_data.get("name_dest", ""))).strip()
        is_merchant_dest = dest.startswith("M")

        # Flag 1: Non-finite or negative values
        raw_nums = [amount, old_orig, new_orig, old_dest, new_dest]
        if any(math.isnan(n) or math.isinf(n) for n in raw_nums) or any(n < 0 for n in [old_orig, new_orig, old_dest, new_dest]) or amount <= 0:
            triggered.append({
                "rule_id": "NEGATIVE_OR_NONFINITE_VALUES",
                "name": "Negative or Non-Finite Values",
                "description": "Ledger entry contains invalid negative balances, non-positive amount, or non-finite numbers.",
                "severity": "HIGH",
                "penalty": 40.0,
                "floor": 70.0
            })

        # Flag 2: Impossible Merchant Balance (PaySim M-accounts must be strictly 0.0)
        if is_merchant_dest and (old_dest > 0.0 or new_dest > 0.0):
            triggered.append({
                "rule_id": "IMPOSSIBLE_MERCHANT_BALANCE",
                "name": "Impossible Merchant Account Balance",
                "description": f"Merchant destination '{dest}' has nonzero balance (old: ${old_dest:,.2f}, new: ${new_dest:,.2f}).",
                "severity": "HIGH",
                "penalty": 40.0,
                "floor": 70.0
            })

        # Flag 3: Origin & Destination Ledger Reconciliation (AML-04)
        origin_variance = 0.0
        if tx_type in ("TRANSFER", "CASH_OUT", "PAYMENT", "DEBIT"):
            origin_variance = round((old_orig - amount) - new_orig, 2)
        elif tx_type == "CASH_IN":
            origin_variance = round((old_orig + amount) - new_orig, 2)

        dest_variance = 0.0
        if not is_merchant_dest and tx_type in ("TRANSFER", "CASH_IN"):
            dest_variance = round((new_dest - old_dest) - amount, 2)

        abs_orig_var = abs(origin_variance)
        abs_dest_var = abs(dest_variance)

        has_discrepancy = False
        if abs_orig_var > 10000.0 or abs_dest_var > 10000.0:
            has_discrepancy = True
            triggered.append({
                "rule_id": "LEDGER_VARIANCE_MAJOR",
                "name": "Major Accounting Ledger Discrepancy",
                "description": f"Unexplained ledger variance exceeds $10,000 threshold (origin var: ${origin_variance:,.2f}, dest var: ${dest_variance:,.2f}).",
                "severity": "HIGH",
                "penalty": 45.0,
                "floor": 70.0
            })
        elif abs_orig_var > 1.0 or abs_dest_var > 1.0:
            has_discrepancy = True
            triggered.append({
                "rule_id": "LEDGER_VARIANCE_MINOR",
                "name": "Minor Accounting Ledger Discrepancy",
                "description": f"Unexplained ledger variance exceeds 1.0 unit threshold (origin var: ${origin_variance:,.2f}, dest var: ${dest_variance:,.2f}).",
                "severity": "MEDIUM",
                "penalty": 25.0,
                "floor": 40.0
            })

        # Rule 4: Complete Account Drain
        if tx_type in ("TRANSFER", "CASH_OUT") and old_orig > 0 and new_orig == 0 and amount >= old_orig * 0.95:
            triggered.append({
                "rule_id": "RULE_LIQUIDATION_DRAIN",
                "name": "Full Account Liquidation",
                "description": "Entire origin balance was drained to zero via high-risk liquidation channel.",
                "severity": "CRITICAL",
                "penalty": 35.0,
                "floor": 85.0
            })

        # Rule 5: High-Value Threshold Exposure
        if amount >= 200000.0:
            triggered.append({
                "rule_id": "RULE_HIGH_VALUE_THRESHOLD",
                "name": "Large Value Exposure (>200,000 units)",
                "description": "Transaction amount exceeds enterprise high-value monitoring threshold.",
                "severity": "MEDIUM",
                "penalty": 15.0,
                "floor": 35.0
            })

        # Rule 6: Rapid Outflow from Zero Baseline
        if old_orig == 0.0 and amount > 0 and tx_type in ("TRANSFER", "CASH_OUT"):
            triggered.append({
                "rule_id": "RULE_ZERO_BALANCE_OUTFLOW",
                "name": "Outflow from Zero Balance Ledger",
                "description": "Transaction initiated despite origin recorded starting balance of zero.",
                "severity": "HIGH",
                "penalty": 25.0,
                "floor": 65.0
            })

        # Safeguard Rule: Legitimate Merchant Payment ONLY IF no ledger discrepancies or impossible merchant balances exist
        if tx_type == "PAYMENT" and is_merchant_dest and not has_discrepancy and old_dest == 0.0 and new_dest == 0.0:
            triggered.append({
                "rule_id": "SAFEGUARD_VERIFIED_MERCHANT",
                "name": "Standard POS/Merchant Settlement",
                "description": "Routine merchant transaction pattern. Reconciled and verified normal payment.",
                "severity": "INFO",
                "penalty": -20.0,
                "floor": 0.0
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
