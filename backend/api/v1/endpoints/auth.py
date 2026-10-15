import uuid
import json
import time
from collections import defaultdict
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.db.models import User, AuditEvent
from backend.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserStatusUpdateRequest,
    PasswordResetRequest,
    UserManagementItem
)
from backend.security.jwt_auth import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    require_admin
)

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])

# In-memory sliding window rate limiter for login attempts (5 attempts / 60 seconds per identifier)
_login_failed_attempts = defaultdict(list)

def _check_rate_limit(identifier: str, max_attempts: int = 5, window_seconds: int = 60):
    now = time.time()
    valid_attempts = [t for t in _login_failed_attempts[identifier] if now - t < window_seconds]
    _login_failed_attempts[identifier] = valid_attempts
    if len(valid_attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 60 seconds before trying again."
        )

def _record_failure(identifier: str):
    _login_failed_attempts[identifier].append(time.time())

def _clear_failures(identifier: str):
    if identifier in _login_failed_attempts:
        del _login_failed_attempts[identifier]

def _record_audit_log(
    db: Session,
    actor_id: str,
    actor_role: str,
    action: str,
    target_type: str,
    target_id: str,
    outcome: str = "SUCCESS",
    details: dict = None
):
    try:
        ev = AuditEvent(
            correlation_id=str(uuid.uuid4()),
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            outcome=outcome,
            details_json=json.dumps(details or {}),
            timestamp=datetime.utcnow()
        )
        db.add(ev)
        db.commit()
    except Exception as e:
        db.rollback()
        # Non-fatal log failure

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    identifier = form_data.username.strip().lower()

    # Rate limiting protection against credential stuffing / brute force
    _check_rate_limit(identifier)

    # Query user by email or username
    user = db.query(User).filter(
        (User.email.ilike(identifier)) | (User.username.ilike(identifier))
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        _record_failure(identifier)
        _record_audit_log(
            db,
            actor_id=identifier,
            actor_role="UNKNOWN",
            action="LOGIN_FAILED",
            target_type="AUTH",
            target_id=identifier,
            outcome="FAILURE",
            details={"reason": "Invalid credentials provided"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        _record_audit_log(
            db,
            actor_id=user.username,
            actor_role=user.role,
            action="LOGIN_DENIED",
            target_type="AUTH",
            target_id=user.id,
            outcome="DENIED",
            details={"reason": "Account is deactivated"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Please contact an administrator.",
        )

    # Clear previous failure records on successful login
    _clear_failures(identifier)

    token = create_access_token(data={"sub": user.id, "role": user.role, "username": user.username})

    _record_audit_log(
        db,
        actor_id=user.username,
        actor_role=user.role,
        action="LOGIN_SUCCESS",
        target_type="AUTH",
        target_id=user.id,
        outcome="SUCCESS"
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user: dict = Depends(get_current_user)):
    return UserProfileResponse(
        id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        email=user["email"],
        role=user["role"],
        is_active=user["is_active"]
    )

@router.post("/logout")
def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _record_audit_log(
        db,
        actor_id=current_user["username"],
        actor_role=current_user["role"],
        action="LOGOUT",
        target_type="AUTH",
        target_id=current_user["id"],
        outcome="SUCCESS"
    )
    return {"message": "Successfully logged out."}

# Administrator User Management Endpoints
@router.get("/users", response_model=List[UserManagementItem])
def list_users(
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserManagementItem(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at
        )
        for u in users
    ]

@router.patch("/users/{user_id}/status", response_model=UserManagementItem)
def update_user_status(
    user_id: str,
    payload: UserStatusUpdateRequest,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if user_id == admin_user["id"] and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security safeguard: You cannot disable your own administrator account."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    old_status = user.is_active
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)

    _record_audit_log(
        db,
        actor_id=admin_user["username"],
        actor_role=admin_user["role"],
        action="USER_STATUS_CHANGE",
        target_type="USER",
        target_id=user.id,
        outcome="SUCCESS",
        details={"old_status": old_status, "new_status": user.is_active, "target_username": user.username}
    )

    return UserManagementItem(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    )

@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: str,
    payload: PasswordResetRequest,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if len(payload.new_password.strip()) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 4 characters in length."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    user.hashed_password = hash_password(payload.new_password.strip())
    db.commit()

    _record_audit_log(
        db,
        actor_id=admin_user["username"],
        actor_role=admin_user["role"],
        action="PASSWORD_RESET",
        target_type="USER",
        target_id=user.id,
        outcome="SUCCESS",
        details={"target_username": user.username}
    )

    return {"message": f"Password for user '{user.username}' has been updated successfully."}
