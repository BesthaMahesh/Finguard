import pytest
import pandas as pd
from backend.data.validator import DataValidator
from backend.data.profiler import DataProfiler

def test_paysim_schema_validation_success():
    valid_df = pd.DataFrame([{
        "step": 1,
        "type": "PAYMENT",
        "amount": 100.0,
        "nameOrig": "C123",
        "oldbalanceOrg": 500.0,
        "newbalanceOrig": 400.0,
        "nameDest": "M456",
        "oldbalanceDest": 0.0,
        "newbalanceDest": 0.0,
        "isFraud": 0,
        "isFlaggedFraud": 0
    }])
    is_valid, errors = DataValidator.validate_schema(valid_df)
    assert is_valid is True
    assert len(errors) == 0

def test_paysim_schema_validation_missing_columns():
    invalid_df = pd.DataFrame([{"step": 1, "amount": 100.0}])
    is_valid, errors = DataValidator.validate_schema(invalid_df)
    assert is_valid is False
    assert len(errors) > 0

def test_data_records_integrity():
    df = pd.DataFrame([
        {"step": 1, "type": "TRANSFER", "amount": 250.0, "oldbalanceOrg": 500.0, "newbalanceOrig": 250.0, "oldbalanceDest": 0.0, "newbalanceDest": 250.0},
        {"step": 2, "type": "CASH_OUT", "amount": -10.0, "oldbalanceOrg": 10.0, "newbalanceOrig": 20.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0}
    ])
    report = DataValidator.validate_records(df)
    assert report["is_valid"] is False
    assert any("Negative amount" in issue for issue in report["issues"])

def test_data_profiler_output():
    df = pd.DataFrame([
        {"step": 1, "type": "PAYMENT", "amount": 100.0, "isFraud": 0},
        {"step": 2, "type": "TRANSFER", "amount": 5000.0, "isFraud": 1}
    ])
    profile = DataProfiler.profile_dataframe(df)
    assert profile["total_transactions"] == 2
    assert profile["total_frauds"] == 1
    assert profile["fraud_rate_pct"] == 50.0
