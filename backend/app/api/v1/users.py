"""Users API endpoints: CRUD for user management (admin only)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import UserCreate, UserResponse, UserUpdate
from app.auth.service import (
    create_user,
    deactivate_user,
    get_user,
    list_users,
    require_admin,
    update_user,
)
from app.core.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar usuários",
)
def api_list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    """List all users (admin only)."""
    return list_users(db, skip=skip, limit=limit)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário",
)
def api_create_user(
    request: UserCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create a new user (admin only)."""
    return create_user(db, request)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Detalhe do usuário",
)
def api_get_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Get a user by ID (admin only)."""
    return get_user(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Atualizar usuário",
)
def api_update_user(
    user_id: int,
    request: UserUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Update a user (admin only)."""
    return update_user(db, user_id, request)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="Desativar usuário",
)
def api_deactivate_user(
    user_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Deactivate a user (soft delete, admin only)."""
    return deactivate_user(db, user_id)
