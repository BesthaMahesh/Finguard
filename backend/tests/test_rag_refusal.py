import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security.jwt_auth import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "analyst", "role": "analyst", "user_id": "usr-analyst-01"})
    return {"Authorization": f"Bearer {token}"}

def test_rag_refusal_on_unsupported_out_of_scope_query(auth_headers):
    """
    When an analyst asks a question not supported by indexed policies,
    the assistant must withhold answer and return explicit Insufficient Policy Evidence refusal.
    """
    payload = {
        "message": "What is the secret recipe for Martian pizza crust and orbital mechanics?"
    }
    response = client.post("/api/v1/assistant/chat", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "cannot answer this question from the indexed policies" in data["reply"]
    # Citations must be empty for unsupported queries
    assert len(data.get("citations", [])) == 0

def test_rag_supported_policy_query(auth_headers):
    """
    When an analyst asks about rapid liquidation or FATF Recommendation 16,
    the assistant should provide citations with document, section, and page references.
    """
    payload = {
        "message": "What are the rules and threshold procedures for rapid liquidation under AML-04?"
    }
    response = client.post("/api/v1/assistant/chat", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data.get("citations", [])) > 0
    # Must have document_id and section
    first_c = data["citations"][0]
    assert "document_id" in first_c
    assert "section" in first_c

