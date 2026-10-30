from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRoleSchema:
    """Constants for user roles."""
    ADMIN: ClassVar[str] = "admin"
    OPERATOR: ClassVar[str] = "operator"


# --- Login ---

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(AuthTokens):
    pass


# --- User ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="operator")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 letra maiúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 número")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "operator"):
            raise ValueError("Role deve ser 'admin' ou 'operator'")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("admin", "operator"):
            raise ValueError("Role deve ser 'admin' ou 'operator'")
        return v


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


# --- Password Reset ---

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 letra maiúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 número")
        return v


# --- Refresh ---

class RefreshRequest(BaseModel):
    refresh_token: str


# --- Setup ---

class SetupAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 letra maiúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("Senha deve conter pelo menos 1 número")
        return v
