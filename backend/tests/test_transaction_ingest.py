import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security.jwt_auth import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "admin", "role": "ADMIN", "user_id": "usr-admin-01"})
    return {"Authorization": f"Bearer {token}"}

def test_add_transaction_valid(auth_headers):
    payload = {
        "step": 12,
        "type": "PAYMENT",
        "amount": 145.20,
        "name_orig": "C1234567890",
        "old_balance_org": 500.00,
        "new_balance_orig": 354.80,
        "name_dest": "M9876543210",
        "old_balance_dest": 0.00,
        "new_balance_dest": 0.00
    }
    response = client.post("/api/v1/transactions", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 145.20
    assert data["type"] == "PAYMENT"
    # Ground truth must be None/unknown for newly ingested live transactions
    assert data["is_fraud"] is None
    assert "id" in data

def test_add_transaction_negative_amount_rejected(auth_headers):
    payload = {
        "step": 1,
        "type": "TRANSFER",
        "amount": -500.00,
        "name_orig": "C123",
        "old_balance_org": 1000.0,
        "new_balance_orig": 1500.0,
        "name_dest": "C456",
        "old_balance_dest": 0.0,
        "new_balance_dest": 500.0
    }
    response = client.post("/api/v1/transactions", json=payload, headers=auth_headers)
    assert response.status_code == 422
    assert "greater than 0" in response.text

def test_add_transaction_impossible_ledger_rejected(auth_headers):
    payload = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 500.00,
        "name_orig": "C123",
        "old_balance_org": 1000.0,
        "new_balance_orig": 900.0,  # 1000 - 500 = 500, not 900!
        "name_dest": "C456",
        "old_balance_dest": 0.0,
        "new_balance_dest": 500.0
    }
    response = client.post("/api/v1/transactions", json=payload, headers=auth_headers)
    assert response.status_code == 422
    assert "ledger discrepancy" in response.text.lower()

def test_high_risk_auto_case_creation(auth_headers):
    """
    A full liquidation transfer over threshold must trigger HIGH/CRITICAL risk
    and automatically generate an investigation case docket.
    """
    payload = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 800000.00,
        "name_orig": "C999999",
        "old_balance_org": 800000.00,
        "new_balance_orig": 0.00,
        "name_dest": "C888888",
        "old_balance_dest": 0.00,
        "new_balance_dest": 800000.00
    }
    response = client.post("/api/v1/transactions", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["risk_level"] in ("HIGH", "CRITICAL")
    assert data["case_id"] is not None
    assert data["case_id"].startswith("CASE-")
