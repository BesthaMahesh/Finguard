import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security.jwt_auth import create_access_token
from backend.db.session import SessionLocal
from backend.db.models import Transaction, InvestigationCase, Conversation, ConversationMessage, AuditEvent

client = TestClient(app)

@pytest.fixture
def admin_headers():
    token = create_access_token({"sub": "admin", "role": "ADMIN", "user_id": "usr-adm-test"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def user_headers():
    token = create_access_token({"sub": "user", "role": "USER", "user_id": "usr-std-test"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def other_user_headers():
    token = create_access_token({"sub": "analyst", "role": "USER", "user_id": "usr-analyst-001"})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Priority 1: Enterprise Authentication Tests
# ============================================================================

def test_login_valid_credentials():
    resp = client.post("/api/v1/auth/token", json={"username": "user", "password": "12345"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["username"] == "user"
    assert data["role"] == "USER"

    # Also verify /auth/me using the obtained bearer token
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "user"
    assert me_data["role"] == "USER"

def test_login_invalid_credentials():
    resp = client.post("/api/v1/auth/token", json={"username": "user", "password": "wrongpassword!"})
    assert resp.status_code == 401
    data = resp.json()
    assert "detail" in data or "error" in data

def test_login_missing_fields():
    resp = client.post("/api/v1/auth/token", json={"username": ""})
    assert resp.status_code in (400, 422)


# ============================================================================
# Priority 2 & 7: Transaction Inspection & Details Tests
# ============================================================================

def test_transaction_inspect_valid_id(user_headers):
    # Query transaction 1
    resp = client.get("/api/v1/transactions/1", headers=user_headers)
    assert resp.status_code == 200
    tx = resp.json()
    assert tx["id"] == 1
    assert "amount" in tx
    assert "type" in tx
    assert "name_orig" in tx
    assert "name_dest" in tx
    assert "is_fraud" in tx  # Ground truth
    assert "fraud_probability" in tx  # Model prediction
    assert "risk_score" in tx
    assert "risk_level" in tx
    assert "rule_flags" in tx
    assert "investigation" in tx  # Associated investigation (can be None or dict)
    assert "audit_history" in tx

def test_transaction_inspect_invalid_id(user_headers):
    resp = client.get("/api/v1/transactions/999999999", headers=user_headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ============================================================================
# Priority 3 & 8: Investigation Disposition Submission Tests
# ============================================================================

def test_investigation_review_submission(admin_headers):
    # Fetch first available case
    list_resp = client.get("/api/v1/investigations?limit=1", headers=admin_headers)
    assert list_resp.status_code == 200
    cases = list_resp.json()["items"]
    assert len(cases) > 0
    case_id = cases[0]["id"]

    # Submit valid review
    review_payload = {
        "disposition": "ESCALATE_TO_SAR",
        "disposition_notes": "Audited review: High volume anomalous liquidation confirmed."
    }
    resp = client.post(f"/api/v1/investigations/{case_id}/review", json=review_payload, headers=admin_headers)
    assert resp.status_code == 200
    updated_case = resp.json()
    assert updated_case["disposition"] == "ESCALATE_TO_SAR"
    assert updated_case["reviewed_by"] == "admin"
    assert updated_case["status"] == "CLOSED_RESOLVED"

def test_investigation_review_alias_normalization(admin_headers):
    list_resp = client.get("/api/v1/investigations?limit=1", headers=admin_headers)
    case_id = list_resp.json()["items"][0]["id"]

    # Submit with frontend alias CONFIRMED_FRAUD_FREEZE
    payload = {
        "disposition": "CONFIRMED_FRAUD_FREEZE",
        "disposition_notes": "Entity account frozen under four-eyes protocol."
    }
    resp = client.post(f"/api/v1/investigations/{case_id}/review", json=payload, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["disposition"] == "FREEZE_ACCOUNT"

def test_investigation_review_invalid_input(admin_headers):
    list_resp = client.get("/api/v1/investigations?limit=1", headers=admin_headers)
    case_id = list_resp.json()["items"][0]["id"]

    # Invalid disposition
    resp = client.post(f"/api/v1/investigations/{case_id}/review", json={"disposition": "INVALID_ACTION", "disposition_notes": "Valid note here"}, headers=admin_headers)
    assert resp.status_code == 422

    # Short notes (< 5 chars)
    resp = client.post(f"/api/v1/investigations/{case_id}/review", json={"disposition": "FREEZE_ACCOUNT", "disposition_notes": "ok"}, headers=admin_headers)
    assert resp.status_code == 422

def test_investigation_review_idempotency(admin_headers):
    list_resp = client.get("/api/v1/investigations?limit=1", headers=admin_headers)
    case_id = list_resp.json()["items"][0]["id"]
    payload = {
        "disposition": "FREEZE_ACCOUNT",
        "disposition_notes": "Idempotent submission check."
    }
    resp1 = client.post(f"/api/v1/investigations/{case_id}/review", json=payload, headers=admin_headers)
    resp2 = client.post(f"/api/v1/investigations/{case_id}/review", json=payload, headers=admin_headers)
    assert resp1.status_code == 200
    assert resp2.status_code == 200


# ============================================================================
# Priority 4 & 5: Risk Assistant Chat Persistence & User Isolation Tests
# ============================================================================

def test_assistant_conversation_persistence(user_headers, other_user_headers):
    # 1. Create a conversation for user
    create_resp = client.post("/api/v1/assistant/conversations", json={"title": "Test ATO Investigation"}, headers=user_headers)
    assert create_resp.status_code == 200
    conv_id = create_resp.json()["id"]

    # 2. List conversations for user
    list_resp = client.get("/api/v1/assistant/conversations", headers=user_headers)
    assert list_resp.status_code == 200
    conv_ids = [c["id"] for c in list_resp.json()["conversations"]]
    assert conv_id in conv_ids

    # 3. Send chat message linked to this conversation
    chat_resp = client.post(
        "/api/v1/assistant/chat",
        json={"message": "What is the four-eyes principle?", "conversation_id": conv_id},
        headers=user_headers
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "reply" in data
    assert data["conversation_id"] == conv_id

    # 4. Fetch conversation detail with messages
    hist_resp = client.get(f"/api/v1/assistant/conversations/{conv_id}", headers=user_headers)
    assert hist_resp.status_code == 200
    msgs = hist_resp.json()["messages"]
    assert len(msgs) >= 2  # user + assistant
    assert msgs[0]["sender"] == "user"
    assert msgs[1]["sender"] == "assistant"

    # 5. User Ownership Isolation: other user cannot view this conversation
    isolated_resp = client.get(f"/api/v1/assistant/conversations/{conv_id}", headers=other_user_headers)
    assert isolated_resp.status_code == 403

    # 6. Delete conversation
    del_resp = client.delete(f"/api/v1/assistant/conversations/{conv_id}", headers=user_headers)
    assert del_resp.status_code == 200


# ============================================================================
# Priority 6: System Health & Observability Permission Tier Tests
# ============================================================================

def test_system_health_user_tier(user_headers):
    # Standard USER should get standard health status gracefully without crashing
    resp = client.get("/api/v1/observability/summary", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_tier"] == "STANDARD_HEALTH"
    assert data["service_status"] == "HEALTHY"
    assert "notice" in data
    assert len(data["recent_traces"]) == 0  # Traces restricted for standard user

def test_system_health_admin_tier(admin_headers):
    # ADMIN gets administrative telemetry with traces
    resp = client.get("/api/v1/observability/summary", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_tier"] == "ADMINISTRATIVE_TELEMETRY"
    assert "recent_traces" in data

def test_system_health_unauthorized():
    # Without token, must return 401
    resp = client.get("/api/v1/observability/summary")
    assert resp.status_code == 401
