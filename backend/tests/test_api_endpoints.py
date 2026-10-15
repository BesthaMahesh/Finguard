import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

from backend.security.jwt_auth import create_access_token

@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "admin", "role": "ADMIN", "user_id": "usr-admin-01"})
    return {"Authorization": f"Bearer {token}"}

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["architecture_layers"] == 9

def test_readiness_endpoint():
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"

def test_dashboard_summary(auth_headers):
    response = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions_processed" in data
    assert "risk_level_distribution" in data
    assert "transaction_type_breakdown" in data

def test_transactions_list(auth_headers):
    response = client.get("/api/v1/transactions?limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 10

def test_models_evaluation(auth_headers):
    response = client.get("/api/v1/models/evaluation", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pr_auc" in data
    assert "roc_auc" in data
    assert "confusion_matrix" in data

def test_mcp_tools_listing(auth_headers):
    response = client.get("/api/v1/mcp/tools", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) >= 6

def test_auth_token_and_me():
    # Login with analyst
    login_resp = client.post("/api/v1/auth/token", json={"username": "analyst", "password": "analyst123"})
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data

    # Call /me with bearer token
    token = token_data["access_token"]
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "analyst"
    assert me_data["role"] == "analyst"
