import pytest
from backend.ml.leakage_guard import LeakageGuard
from backend.ml.features import FEATURE_COLUMNS

def test_leakage_guard_rejects_target_columns():
    is_clean, violations = LeakageGuard.audit_features(["amount", "type", "isFraud"])
    assert is_clean is False
    assert len(violations) >= 1

def test_leakage_guard_approves_sanitized_features():
    is_clean, violations = LeakageGuard.audit_features(FEATURE_COLUMNS)
    assert is_clean is True
    assert len(violations) == 0

def test_leakage_guard_rejects_flagged_fraud():
    is_clean, violations = LeakageGuard.audit_features(["amount", "isFlaggedFraud"])
    assert is_clean is False
