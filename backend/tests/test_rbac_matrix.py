import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security.jwt_auth import create_access_token

client = TestClient(app)

def make_headers(username: str, role: str):
    token = create_access_token({"sub": username, "role": role, "user_id": f"usr-{username}"})
    return {"Authorization": f"Bearer {token}"}

def test_analyst_role_permissions():
    """
    Analyst: Can view transactions and query assistant, but CANNOT submit disposition reviews or manage users.
    """
    headers = make_headers("analyst", "analyst")

    # Allowed: view transactions
    tx_resp = client.get("/api/v1/transactions?limit=5", headers=headers)
    assert tx_resp.status_code == 200

    # Forbidden: submit review disposition
    review_resp = client.post(
        "/api/v1/investigations/CASE-FG-000199/review",
        json={"disposition": "ESCALATE_TO_SAR", "disposition_notes": "Analyst test notes"},
        headers=headers
    )
    assert review_resp.status_code == 403

    # Forbidden: access admin endpoints
    admin_resp = client.get("/api/v1/auth/users", headers=headers)
    assert admin_resp.status_code == 403

def test_investigator_role_permissions():
    """
    Investigator: Can view cases and submit investigator dispositions, but CANNOT manage platform users.
    """
    headers = make_headers("investigator", "investigator")

    # Allowed: view investigations
    cases_resp = client.get("/api/v1/investigations", headers=headers)
    assert cases_resp.status_code == 200

    # Allowed: submit disposition review
    review_resp = client.post(
        "/api/v1/investigations/CASE-FG-000199/review",
        json={"disposition": "ESCALATE_TO_SAR", "disposition_notes": "Investigator SAR Escalation verified by Marcus Vance."},
        headers=headers
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["disposition"] == "ESCALATE_TO_SAR"

    # Forbidden: system administration
    admin_resp = client.get("/api/v1/auth/users", headers=headers)
    assert admin_resp.status_code == 403

def test_auditor_role_permissions():
    """
    Auditor: Can view audit logs and verify cryptographic chain, but CANNOT submit disposition reviews or alter users.
    """
    headers = make_headers("auditor", "auditor")

    # Allowed: view audit logs
    audit_resp = client.get("/api/v1/audit", headers=headers)
    assert audit_resp.status_code == 200

    # Allowed: verify cryptographic chain integrity
    verify_resp = client.post("/api/v1/audit/verify-chain", headers=headers)
    assert verify_resp.status_code == 200
    assert "chain_intact" in verify_resp.json()

    # Forbidden: submit investigator disposition
    review_resp = client.post(
        "/api/v1/investigations/CASE-FG-000199/review",
        json={"disposition": "ESCALATE_TO_SAR", "disposition_notes": "Auditor attempt to edit case"},
        headers=headers
    )
    assert review_resp.status_code == 403

def test_administrator_role_permissions():
    """
    Administrator: Has full system access across all layers.
    """
    headers = make_headers("admin", "administrator")

    # Allowed: manage users
    users_resp = client.get("/api/v1/auth/users", headers=headers)
    assert users_resp.status_code == 200

    # Allowed: audit verification
    verify_resp = client.post("/api/v1/audit/verify-chain", headers=headers)
    assert verify_resp.status_code == 200
