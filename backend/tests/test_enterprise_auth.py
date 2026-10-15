import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.security.jwt_auth import hash_password, verify_password, create_access_token
from backend.security.rbac import verify_role_permission, UserRole
from backend.db.session import SessionLocal
from backend.db.models import User, AuditEvent
from backend.api.v1.endpoints.auth import _clear_failures

client = TestClient(app)

def test_password_hashing_and_verification():
    raw_pass = "SecurePass123!"
    hashed = hash_password(raw_pass)
    assert "$" in hashed
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False

def test_two_accounts_authentication():
    # 1. Standard User
    user_res = client.post("/api/v1/auth/token", json={"username": "user@finguard.local", "password": "12345"})
    assert user_res.status_code == 200, user_res.text
    user_data = user_res.json()
    assert user_data["username"] == "user"
    assert user_data["role"].upper() == "USER"
    assert "access_token" in user_data

    # Profile check with user token
    user_profile = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_data['access_token']}"})
    assert user_profile.status_code == 200
    assert user_profile.json()["email"] == "user@finguard.local"

    # 2. Administrator
    admin_res = client.post("/api/v1/auth/token", json={"username": "admin@finguard.local", "password": "123456"})
    assert admin_res.status_code == 200, admin_res.text
    admin_data = admin_res.json()
    assert admin_data["username"] == "admin"
    assert admin_data["role"].upper() in ("ADMIN", "ADMINISTRATOR")

    # Profile check with admin token
    admin_profile = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_data['access_token']}"})
    assert admin_profile.status_code == 200
    assert admin_profile.json()["email"] == "admin@finguard.local"

def test_login_failure_generic_error():
    _clear_failures("nonexistent@finguard.local")
    res = client.post("/api/v1/auth/token", json={"username": "nonexistent@finguard.local", "password": "wrong"})
    assert res.status_code == 401
    assert "Invalid email/username or password" in res.json()["detail"]

def test_login_rate_limiting():
    test_id = "ratelimit_test_user"
    _clear_failures(test_id)

    # 5 failed attempts
    for _ in range(5):
        res = client.post("/api/v1/auth/token", json={"username": test_id, "password": "wrongpassword"})
        assert res.status_code == 401

    # 6th attempt should be blocked by rate limiter
    res_blocked = client.post("/api/v1/auth/token", json={"username": test_id, "password": "wrongpassword"})
    assert res_blocked.status_code == 429
    assert "Too many failed login attempts" in res_blocked.json()["detail"]
    _clear_failures(test_id)

def test_role_based_permissions_user_vs_admin():
    # User permissions
    assert verify_role_permission(UserRole.USER, "view_dashboard") is True
    assert verify_role_permission(UserRole.USER, "view_transactions") is True
    assert verify_role_permission(UserRole.USER, "ask_ai_assistant") is True
    assert verify_role_permission(UserRole.USER, "manage_users") is False
    assert verify_role_permission(UserRole.USER, "system_config") is False

    # Admin permissions
    assert verify_role_permission(UserRole.ADMIN, "view_dashboard") is True
    assert verify_role_permission(UserRole.ADMIN, "manage_users") is True
    assert verify_role_permission(UserRole.ADMIN, "system_config") is True
    assert verify_role_permission(UserRole.ADMIN, "reindex_documents") is True

def test_admin_user_management_and_audit():
    # Login as admin
    admin_res = client.post("/api/v1/auth/token", json={"username": "admin@finguard.local", "password": "123456"})
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Login as regular user
    user_res = client.post("/api/v1/auth/token", json={"username": "user@finguard.local", "password": "12345"})
    user_token = user_res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Regular user cannot list users (requires admin)
    forbidden_list = client.get("/api/v1/auth/users", headers=user_headers)
    assert forbidden_list.status_code == 403

    # Admin can list users
    allowed_list = client.get("/api/v1/auth/users", headers=admin_headers)
    assert allowed_list.status_code == 200
    users_list = allowed_list.json()
    assert len(users_list) >= 2

    # Find the 'user' account
    target_user = next((u for u in users_list if u["username"] == "user"), None)
    assert target_user is not None

    # Admin can update user status and reset password
    reset_res = client.post(
        f"/api/v1/auth/users/{target_user['id']}/reset-password",
        headers=admin_headers,
        json={"new_password": "newpassword123"}
    )
    assert reset_res.status_code == 200

    # Verify user can login with new password
    login_new = client.post("/api/v1/auth/token", json={"username": "user@finguard.local", "password": "newpassword123"})
    assert login_new.status_code == 200

    # Reset back to default password '12345'
    client.post(
        f"/api/v1/auth/users/{target_user['id']}/reset-password",
        headers=admin_headers,
        json={"new_password": "12345"}
    )

    # Check audit log contains recorded events
    db = SessionLocal()
    try:
        events = db.query(AuditEvent).filter(AuditEvent.action.in_(["PASSWORD_RESET", "LOGIN_SUCCESS"])).all()
        assert len(events) > 0
    finally:
        db.close()
