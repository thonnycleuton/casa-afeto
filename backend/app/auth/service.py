"""Authentication service: login, tokens, password reset, user management."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.auth.models import PasswordResetToken, RefreshToken, User, UserRole
from app.auth.schemas import (
    AuthTokens,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SetupAdminRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserProfileResponse,
)
from app.auth.utils import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    hash_token,
    send_password_reset_email,
    verify_password,
)
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user from the JWT access token."""
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou desativado",
        )
    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to have admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem realizar esta ação",
        )
    return current_user


# --- Auth operations ---


def authenticate_user(
    db: Session, request: LoginRequest
) -> Optional[User]:
    """Verify email and password. Returns user if valid, None otherwise."""
    user = db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()

    if user is None:
        return None

    if not verify_password(request.password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user


def login(db: Session, request: LoginRequest) -> AuthTokens:
    """Authenticate user and return JWT tokens."""
    user = authenticate_user(db, request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
        )

    # Revoke all existing refresh tokens for this user
    db.execute(
        RefreshToken.__table__.update().where(
            RefreshToken.user_id == user.id
        ).values(is_revoked=True)
    )
    db.commit()

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    # Store refresh token hash
    token_hash = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    rt = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(rt)
    db.commit()

    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def refresh_tokens(
    db: Session, refresh_token_str: str
) -> AuthTokens:
    """Refresh access token using a valid refresh token."""
    payload = decode_token(refresh_token_str)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido",
        )

    token_hash = hash_token(refresh_token_str)
    stored = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    ).scalar_one_or_none()

    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização revogado ou expirado",
        )

    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou desativado",
        )

    # Revoke all refresh tokens for this user
    db.execute(
        RefreshToken.__table__.update().where(
            RefreshToken.user_id == user.id
        ).values(is_revoked=True)
    )
    db.commit()

    # Issue new tokens
    access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token(user.id)

    new_hash = hash_token(new_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=expires_at,
    )
    db.add(new_rt)
    db.commit()

    return AuthTokens(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


def logout(db: Session, refresh_token_str: str) -> None:
    """Revoke a refresh token."""
    token_hash = hash_token(refresh_token_str)
    rt = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()

    if rt:
        rt.is_revoked = True
        db.commit()


def get_user_profile(db: Session, user: User) -> UserProfileResponse:
    """Get the current user's profile."""
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


# --- Password reset ---


def request_password_reset(
    db: Session, request: ForgotPasswordRequest
) -> bool:
    """Create a password reset token and send email. Returns True if user exists."""
    user = db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()

    if user is None:
        # Don't reveal whether the email exists
        return False

    # Create reset token
    reset_token = create_reset_token()
    token_hash = hash_token(reset_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(prt)
    db.commit()

    # Send email with reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    try:
        send_password_reset_email(user.email, user.full_name, reset_link)
    except Exception:
        logger.exception("Failed to send password reset email to %s", user.email)
        # Don't fail the request if email fails; log and continue

    return True


def reset_password(
    db: Session, request: ResetPasswordRequest
) -> bool:
    """Reset password using a valid token. Returns True if successful."""
    token_hash = hash_token(request.token)
    prt = db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.is_used == False,  # noqa: E712
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
    ).scalar_one_or_none()

    if prt is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de recuperação inválido ou expirado",
        )

    user = db.get(User, prt.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não encontrado",
        )

    # Update password
    user.password_hash = hash_password(request.new_password)

    # Mark token as used
    prt.is_used = True

    # Revoke all refresh tokens for this user
    db.execute(
        RefreshToken.__table__.update().where(
            RefreshToken.user_id == user.id
        ).values(is_revoked=True)
    )

    db.commit()
    return True


# --- User management (admin only) ---


def create_user(
    db: Session, request: UserCreate
) -> UserResponse:
    """Create a new user (admin only)."""
    # Check for duplicate email
    existing = db.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com este email",
        )

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=request.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def list_users(
    db: Session, skip: int = 0, limit: int = 100
) -> list[UserResponse]:
    """List all users (admin only)."""
    users = db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    ).scalars().all()
    return [UserResponse.model_validate(u) for u in users]


def get_user(db: Session, user_id: int) -> UserResponse:
    """Get a user by ID (admin only)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return UserResponse.model_validate(user)


def update_user(
    db: Session, user_id: int, request: UserUpdate
) -> UserResponse:
    """Update a user (admin only)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    if request.full_name is not None:
        user.full_name = request.full_name
    if request.role is not None:
        user.role = request.role
    if request.is_active is not None:
        user.is_active = request.is_active

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def deactivate_user(
    db: Session, user_id: int, admin_user: Optional[User] = None
) -> UserResponse:
    """Deactivate a user (soft delete, admin only)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    if admin_user is not None and user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar a si mesmo",
        )

    user.is_active = False

    # Revoke all refresh tokens
    db.execute(
        RefreshToken.__table__.update().where(
            RefreshToken.user_id == user_id
        ).values(is_revoked=True)
    )

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


# --- Setup ---


def create_first_admin(
    db: Session, request: SetupAdminRequest
) -> UserResponse:
    """Create the first admin user. Only works if no users exist."""
    user_count = db.execute(select(func.count(User.id))).scalar_one()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup já concluído. Use o painel de administração para criar usuários.",
        )

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)
