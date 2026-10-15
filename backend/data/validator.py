from typing import Dict, Any, List, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)

EXPECTED_PAYSIM_COLUMNS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg",
    "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest",
    "isFraud", "isFlaggedFraud"
]

VALID_TYPES = {"PAYMENT", "TRANSFER", "CASH_OUT", "DEBIT", "CASH_IN"}

class DataValidator:
    """
    Validates synthetic financial dataset schemas, data types, and value boundaries.
    """

    @staticmethod
    def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        missing_cols = [col for col in EXPECTED_PAYSIM_COLUMNS if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing mandatory schema columns: {missing_cols}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_records(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Performs thorough data quality validation.
        """
        issues = []
        total_rows = len(df)
        
        # Null check
        null_counts = df.isnull().sum().to_dict()
        has_nulls = any(cnt > 0 for cnt in null_counts.values())
        if has_nulls:
            issues.append(f"Null values detected: {null_counts}")
            
        # Amount range check
        if "amount" in df.columns:
            negative_amounts = (df["amount"] < 0).sum()
            if negative_amounts > 0:
                issues.append(f"Negative amount values found: {negative_amounts}")

        # Transaction type validity
        if "type" in df.columns:
            invalid_types = (~df["type"].str.upper().isin(VALID_TYPES)).sum()
            if invalid_types > 0:
                issues.append(f"Unrecognized transaction types detected: {invalid_types}")

        # Balance validity check
        for col in ["oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]:
            if col in df.columns:
                negative_bal = (df[col] < 0).sum()
                if negative_bal > 0:
                    issues.append(f"Negative balance in {col}: {negative_bal}")

        status = "PASSED" if len(issues) == 0 else "WARNINGS_FOUND"
        return {
            "status": status,
            "total_rows_checked": total_rows,
            "null_counts": null_counts,
            "issues": issues,
            "is_valid": len(issues) == 0
        }
