import os
import logging
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from backend.ml.features import extract_features_single, FEATURE_COLUMNS

logger = logging.getLogger(__name__)

FEATURE_DISPLAY_NAMES = {
    "amount_log": "Transaction Amount (Log Scale)",
    "orig_balance_delta": "Origin Balance Depletion Amount",
    "dest_balance_delta": "Destination Balance Inflow",
    "orig_balance_error": "Origin Ledger Accounting Discrepancy",
    "dest_balance_error": "Destination Ledger Discrepancy",
    "is_zero_orig": "Origin Initial Balance is Zero",
    "is_dest_zero_init": "Destination Initial Balance is Zero",
    "is_account_cleared": "Complete Account Drain (100% Liquidation)",
    "dest_is_merchant": "Destination is Merchant Entity",
    "hour_of_day": "Hour of Day (Temporal Window)",
    "type_CASH_OUT": "High-Risk Channel: Cash Out",
    "type_TRANSFER": "High-Risk Channel: Wire Transfer",
    "type_PAYMENT": "Channel: Merchant Payment",
    "type_CASH_IN": "Channel: Cash Inflow",
    "type_DEBIT": "Channel: Debit Processing"
}

class ExplainabilityService:
    def __init__(self, model_path: str = "./models/finguard_rf_model.joblib", background_path: str = "./models/shap_background.joblib"):
        self.model_path = model_path
        self.background_path = background_path
        self._model = None
        self._explainer = None
        self._background = None

    def _load(self):
        if self._model is None and os.path.exists(self.model_path):
            self._model = joblib.load(self.model_path)
        if self._background is None and os.path.exists(self.background_path):
            self._background = joblib.load(self.background_path)
            try:
                import shap
                # TreeExplainer for RandomForest
                self._explainer = shap.TreeExplainer(self._model, data=self._background)
            except Exception as e:
                logger.warning(f"Could not initialize TreeExplainer with background data: {e}. Fallback to model-only TreeExplainer.")
                try:
                    import shap
                    self._explainer = shap.TreeExplainer(self._model)
                except Exception as ex:
                    logger.error(f"Fallback TreeExplainer also failed: {ex}")
                    self._explainer = None

    def explain_transaction(self, tx_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Computes SHAP feature importance contributions for a specific transaction.
        Returns list of features ordered by absolute impact on the risk score.
        """
        self._load()
        X_df = extract_features_single(tx_data)
        
        explanations = []
        if self._explainer is not None:
            try:
                shap_values = self._explainer.shap_values(X_df, check_additivity=False)
                # For binary classification in RandomForest:
                # shap_values is either an array of shape (N, M, 2) or a list of two arrays [N, M]
                if isinstance(shap_values, list) and len(shap_values) > 1:
                    vals = shap_values[1][0]  # Positive class (Fraud)
                elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                    vals = shap_values[0, :, 1]
                else:
                    vals = shap_values[0]

                for col, val in zip(FEATURE_COLUMNS, vals):
                    feature_val = float(X_df[col].iloc[0])
                    explanations.append({
                        "feature_name": col,
                        "display_name": FEATURE_DISPLAY_NAMES.get(col, col),
                        "feature_value": feature_val,
                        "shap_value": float(val),
                        "impact": "INCREASES_RISK" if val > 0 else "DECREASES_RISK",
                        "absolute_impact": abs(float(val))
                    })
            except Exception as e:
                logger.warning(f"SHAP explanation computation failed, falling back to heuristic weights: {e}")
                explanations = self._fallback_explanations(X_df)
        else:
            explanations = self._fallback_explanations(X_df)

        # Sort descending by absolute impact
        explanations.sort(key=lambda x: x["absolute_impact"], reverse=True)
        return explanations

    def _fallback_explanations(self, X_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Heuristic fallback feature contributions when model artifacts are initializing."""
        explanations = []
        for col in FEATURE_COLUMNS:
            val = float(X_df[col].iloc[0])
            shap_val = 0.0
            if col == "is_account_cleared" and val == 1:
                shap_val = 0.35
            elif col in ("type_TRANSFER", "type_CASH_OUT") and val == 1:
                shap_val = 0.25
            elif col == "orig_balance_error" and abs(val) > 100:
                shap_val = 0.20
            elif col == "amount_log" and val > 10:
                shap_val = 0.15
            elif col in ("type_PAYMENT", "dest_is_merchant") and val == 1:
                shap_val = -0.30
            
            explanations.append({
                "feature_name": col,
                "display_name": FEATURE_DISPLAY_NAMES.get(col, col),
                "feature_value": val,
                "shap_value": shap_val,
                "impact": "INCREASES_RISK" if shap_val > 0 else "DECREASES_RISK",
                "absolute_impact": abs(shap_val)
            })
        return explanations
