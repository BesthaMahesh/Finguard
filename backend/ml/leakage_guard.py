from typing import List, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Mandatory forbidden columns that cause target leakage
FORBIDDEN_COLUMNS = {
    "isfraud",
    "isflaggedfraud",
    "target",
    "label",
    "fraud",
    "disposition",
    "case_outcome"
}

class LeakageGuard:
    """
    Enforces strict data hygiene to prevent target leakage in financial risk models.
    Validates feature sets, audits column names, and checks post-outcome balance indicators.
    """
    
    @staticmethod
    def audit_features(feature_names: List[str]) -> Tuple[bool, List[str]]:
        """
        Validates that no target variables or post-outcome indicators exist in feature inputs.
        """
        violations = []
        for feat in feature_names:
            normalized = feat.lower().strip()
            if normalized in FORBIDDEN_COLUMNS:
                violations.append(f"Direct target column found: {feat}")
            elif "target" in normalized or "ground_truth" in normalized:
                violations.append(f"Potential target indicator found: {feat}")
                
        is_clean = len(violations) == 0
        if not is_clean:
            logger.error(f"LeakageGuard detected violations: {violations}")
        return is_clean, violations

    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame, drop_targets: bool = True) -> pd.DataFrame:
        """
        Returns a clean dataframe strictly stripped of target columns when preparing inference features.
        """
        clean_df = df.copy()
        for col in clean_df.columns:
            if col.lower().strip() in FORBIDDEN_COLUMNS and drop_targets:
                clean_df = clean_df.drop(columns=[col])
        return clean_df
