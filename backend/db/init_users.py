import os
import sys
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.db.session import engine, SessionLocal, Base
from backend.db.models import User, AuditEvent
from backend.security.jwt_auth import hash_password, verify_password

def init_default_accounts():
    """
    Idempotent initialization of required development & enterprise accounts.
    Provisions:
    1. Standard User: user@finguard.local / username: user, role: USER, password: 12345
    2. Administrator: admin@finguard.local / username: admin, role: ADMIN, password: 123456
    Also preserves legacy demo users for backward compatibility with existing tests.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Default accounts configuration
        default_accounts = [
            {
                "username": "user",
                "email": "user@finguard.local",
                "full_name": "Financial Risk Analyst",
                "role": "USER",
                "is_active": True,
                "password": os.environ.get("DEFAULT_USER_PASSWORD", "12345"),
            },
            {
                "username": "admin",
                "email": "admin@finguard.local",
                "full_name": "Enterprise Risk Administrator",
                "role": "ADMIN",
                "is_active": True,
                "password": os.environ.get("DEFAULT_ADMIN_PASSWORD", "123456"),
            },
            # Backward-compatibility legacy accounts for tests
            {
                "username": "analyst",
                "email": "sarah.chen@finguard.internal",
                "full_name": "Sarah Chen (Risk Analyst)",
                "role": "USER",
                "is_active": True,
                "password": "analyst123",
            },
            {
                "username": "investigator",
                "email": "marcus.vance@finguard.internal",
                "full_name": "Marcus Vance (Senior Investigator)",
                "role": "USER",
                "is_active": True,
                "password": "investigator123",
            },
            {
                "username": "auditor",
                "email": "elena.rostova@finguard.internal",
                "full_name": "Elena Rostova (Compliance Auditor)",
                "role": "USER",
                "is_active": True,
                "password": "auditor123",
            },
        ]

        created_count = 0
        updated_count = 0

        for acc in default_accounts:
            existing_user = db.query(User).filter(
                (User.email == acc["email"]) | (User.username == acc["username"])
            ).first()

            if not existing_user:
                new_user = User(
                    username=acc["username"],
                    email=acc["email"],
                    full_name=acc["full_name"],
                    role=acc["role"],
                    is_active=acc["is_active"],
                    hashed_password=hash_password(acc["password"]),
                    created_at=datetime.utcnow()
                )
                db.add(new_user)
                created_count += 1
            else:
                # Update role if legacy or ensure password hash is salted and matches target password
                if existing_user.username in ("user", "admin"):
                    existing_user.role = acc["role"]
                    existing_user.full_name = acc["full_name"]
                    existing_user.email = acc["email"]
                    if not verify_password(acc["password"], existing_user.hashed_password):
                        existing_user.hashed_password = hash_password(acc["password"])
                        updated_count += 1
                elif not existing_user.hashed_password or "$" not in existing_user.hashed_password:
                    existing_user.hashed_password = hash_password(acc["password"])
                    updated_count += 1

        db.commit()
        print(f"[FinGuard Auth] Account initialization complete: {created_count} created, {updated_count} updated.")
    except Exception as e:
        db.rollback()
        print(f"[FinGuard Auth] Error initializing accounts: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_default_accounts()
