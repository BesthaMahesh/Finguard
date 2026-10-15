from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    email: str
    role: str
    full_name: str

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserProfileResponse(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

class UserStatusUpdateRequest(BaseModel):
    is_active: bool

class PasswordResetRequest(BaseModel):
    new_password: str

class UserManagementItem(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
