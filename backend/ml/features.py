import numpy as np
import pandas as pd
from typing import Dict, Any, List
from backend.ml.leakage_guard import LeakageGuard

FEATURE_COLUMNS = [
    "amount_log",
    "orig_balance_delta",
    "dest_balance_delta",
    "orig_balance_error",
    "dest_balance_error",
    "is_zero_orig",
    "is_dest_zero_init",
    "is_account_cleared",
    "dest_is_merchant",
    "hour_of_day",
    "type_CASH_OUT",
    "type_TRANSFER",
    "type_PAYMENT",
    "type_CASH_IN",
    "type_DEBIT"
]

def engineer_features_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw PaySim transaction dataframe into sanitized ML feature dataframe.
    Guarantees no target leakage.
    """
    df_clean = LeakageGuard.sanitize_dataframe(df, drop_targets=False)
    features = pd.DataFrame(index=df_clean.index)
    
    # 1. Log transform amount (reduces extreme skewness in financial values)
    amount = df_clean["amount"].clip(lower=0)
    features["amount_log"] = np.log1p(amount)
    
    # 2. Balance deltas
    old_orig = df_clean["oldbalanceOrg"].fillna(0)
    new_orig = df_clean["newbalanceOrig"].fillna(0)
    old_dest = df_clean["oldbalanceDest"].fillna(0)
    new_dest = df_clean["newbalanceDest"].fillna(0)
    
    features["orig_balance_delta"] = old_orig - new_orig
    features["dest_balance_delta"] = new_dest - old_dest
    
    # 3. Accounting discrepancy errors
    features["orig_balance_error"] = (old_orig - amount) - new_orig
    features["dest_balance_error"] = (old_dest + amount) - new_dest
    
    # 4. Behavioral indicator flags
    features["is_zero_orig"] = (old_orig == 0).astype(int)
    features["is_dest_zero_init"] = (old_dest == 0).astype(int)
    features["is_account_cleared"] = ((new_orig == 0) & (old_orig > 0)).astype(int)
    
    # 5. Destination entity type
    if "nameDest" in df_clean.columns:
        features["dest_is_merchant"] = df_clean["nameDest"].astype(str).str.startswith("M").astype(int)
    else:
        features["dest_is_merchant"] = 0
        
    # 6. Temporal step modulo 24 (simulated hour of day)
    features["hour_of_day"] = (df_clean["step"].fillna(0) % 24).astype(int)
    
    # 7. Transaction type one-hot encoding
    tx_type = df_clean["type"].astype(str).str.upper()
    features["type_CASH_OUT"] = (tx_type == "CASH_OUT").astype(int)
    features["type_TRANSFER"] = (tx_type == "TRANSFER").astype(int)
    features["type_PAYMENT"] = (tx_type == "PAYMENT").astype(int)
    features["type_CASH_IN"] = (tx_type == "CASH_IN").astype(int)
    features["type_DEBIT"] = (tx_type == "DEBIT").astype(int)
    
    # Validate against LeakageGuard
    is_valid, violations = LeakageGuard.audit_features(list(features.columns))
    if not is_valid:
        raise ValueError(f"Feature engineering failed leakage audit: {violations}")
        
    return features[FEATURE_COLUMNS]

def extract_features_single(tx_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Extracts features for a single incoming transaction dict.
    """
    df = pd.DataFrame([{
        "step": tx_data.get("step", 1),
        "type": str(tx_data.get("type", "PAYMENT")).upper(),
        "amount": float(tx_data.get("amount", 0.0)),
        "oldbalanceOrg": float(tx_data.get("oldbalanceOrg", tx_data.get("old_balance_org", 0.0))),
        "newbalanceOrig": float(tx_data.get("newbalanceOrig", tx_data.get("new_balance_orig", 0.0))),
        "oldbalanceDest": float(tx_data.get("oldbalanceDest", tx_data.get("old_balance_dest", 0.0))),
        "newbalanceDest": float(tx_data.get("newbalanceDest", tx_data.get("new_balance_dest", 0.0))),
        "nameOrig": str(tx_data.get("nameOrig", tx_data.get("name_orig", "C00000000"))),
        "nameDest": str(tx_data.get("nameDest", tx_data.get("name_dest", "M00000000"))),
    }])
    return engineer_features_df(df)
