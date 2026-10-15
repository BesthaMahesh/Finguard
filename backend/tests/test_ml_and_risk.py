import pytest
from backend.ml.model_service import model_service
from backend.security.rbac import verify_role_permission, UserRole

def test_model_inference_and_risk_scoring():
    tx = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 250000.0,
        "name_orig": "C10001",
        "old_balance_org": 250000.0,
        "new_balance_orig": 0.0,
        "name_dest": "C20002",
        "old_balance_dest": 0.0,
        "new_balance_dest": 0.0
    }
    result = model_service.predict_transaction(tx)
    assert "fraud_probability" in result
    assert "risk_score" in result
    assert "risk_level" in result
    assert result["risk_score"] >= 65.0
    assert result["requires_human_review"] is True
    assert len(result["rule_flags"]) > 0

def test_merchant_safeguard_low_risk():
    tx = {
        "step": 1,
        "type": "PAYMENT",
        "amount": 25.0,
        "name_orig": "C10001",
        "old_balance_org": 1000.0,
        "new_balance_orig": 975.0,
        "name_dest": "M99999",
        "old_balance_dest": 0.0,
        "new_balance_dest": 0.0
    }
    result = model_service.predict_transaction(tx)
    assert result["risk_level"] == "LOW"
    assert result["requires_human_review"] is False

def test_rbac_permissions():
    assert verify_role_permission(UserRole.ANALYST, "view_transactions") is True
    assert verify_role_permission(UserRole.ANALYST, "update_disposition") is False
    assert verify_role_permission(UserRole.INVESTIGATOR, "update_disposition") is True
    assert verify_role_permission(UserRole.AUDITOR, "view_audit_trail") is True
    assert verify_role_permission(UserRole.AUDITOR, "run_risk_analysis") is False
    assert verify_role_permission(UserRole.ADMINISTRATOR, "manage_users") is True
