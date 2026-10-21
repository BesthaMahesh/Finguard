import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)

def hash_password(plain_password: str) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a random 16-byte salt.
    Format: salt$iterations$derived_hex
    """
    salt = os.urandom(16).hex()
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac(
        'sha256',
        plain_password.encode('utf-8'),
        bytes.fromhex(salt),
        iterations
    ).hex()
    return f"{salt}${iterations}${derived}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against salted PBKDF2-HMAC-SHA256, with fallback for legacy SHA256 hashes.
    """
    if not hashed_password or not plain_password:
        return False

    parts = hashed_password.split("$")
    if len(parts) == 3:
        salt_hex, iter_str, expected_hash = parts
        try:
            iterations = int(iter_str)
            salt = bytes.fromhex(salt_hex)
            derived = hashlib.pbkdf2_hmac(
                'sha256',
                plain_password.encode('utf-8'),
                salt,
                iterations
            ).hex()
            return hmac.compare_digest(derived, expected_hash)
        except Exception:
            return False
    elif len(parts) == 2:
        salt_hex, expected_hash = parts
        try:
            salt = bytes.fromhex(salt_hex)
            derived = hashlib.pbkdf2_hmac(
                'sha256',
                plain_password.encode('utf-8'),
                salt,
                100_000
            ).hex()
            return hmac.compare_digest(derived, expected_hash)
        except Exception:
            return False
    else:
        # Legacy SHA256 hex fallback
        computed = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return hmac.compare_digest(computed, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, any]:
    """
    Validate incoming JWT and retrieve active user from database.
    In development environments, if no token is provided, fall back to default user to allow seamless exploration.
    """
    from backend.db.models import User

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        identifier: str = payload.get("sub")
        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )

        db = SessionLocal()
        try:
            # Match by id, username, or email
            user = db.query(User).filter(
                (User.id == identifier) | 
                (User.username == identifier) | 
                (User.email == identifier)
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User does not exist",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account has been disabled. Please contact an administrator."
                )

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active
            }
        finally:
            db.close()

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency ensuring the user possesses administrator role."""
    role = str(current_user.get("role", "")).upper()
    if role not in ("ADMIN", "ADMINISTRATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to perform this action."
        )
    return current_user
