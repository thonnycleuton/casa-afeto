"""Auth API endpoints: login, refresh, logout, password reset, setup."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.schemas import (
    AuthTokens,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    ResetPasswordRequest,
    SetupAdminRequest,
    UserProfileResponse,
)
from app.auth.service import (
    get_current_user,
    login,
    logout,
    refresh_tokens,
    request_password_reset,
    reset_password,
    create_first_admin,
    get_user_profile,
)
from app.auth.models import User
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
)
def api_login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and return JWT tokens."""
    return login(db, request)


@router.post(
    "/refresh",
    response_model=AuthTokens,
    status_code=status.HTTP_200_OK,
    summary="Renovar tokens",
)
def api_refresh(
    request: RefreshRequest,
    db: Session = Depends(get_db),
) -> AuthTokens:
    """Renew access token using refresh token."""
    return refresh_tokens(db, request.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
)
def api_logout(
    request: RefreshRequest,
    db: Session = Depends(get_db),
) -> None:
    """Revoke refresh token."""
    logout(db, request.refresh_token)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Perfil do usuário",
)
def api_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Get the current user's profile."""
    return get_user_profile(db, current_user)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar recuperação de senha",
)
def api_forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Request a password reset email."""
    request_password_reset(db, request)
    return {"message": "Se o email existir, um link de recuperação será enviado."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Redefinir senha",
)
def api_reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Reset password using a recovery token."""
    reset_password(db, request)
    return {"message": "Senha redefinida com sucesso."}


@router.post(
    "/setup/create-admin",
    status_code=status.HTTP_201_CREATED,
    summary="Criar primeiro admin (setup)",
)
def api_setup_admin(
    request: SetupAdminRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Create the first admin user. Only works if no users exist."""
    create_first_admin(db, request)
    return {"message": "Administrador criado com sucesso. Setup concluído."}
