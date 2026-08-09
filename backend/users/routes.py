"""Admin user-management routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from deps import require_admin
from models import User
from schemas import (
    ApiResponse,
    ResetPasswordRequest,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from users import service as user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=ApiResponse[List[UserPublic]])
def list_users(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = user_service.list_users(db, search=search)
    return ApiResponse(
        success=True,
        data=[UserPublic.model_validate(u.to_public_dict()) for u in users],
    )


@router.post("", response_model=ApiResponse[UserPublic], status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = user_service.create_user(db, payload)
    return ApiResponse(success=True, data=UserPublic.model_validate(user.to_public_dict()))


@router.patch("/{user_id}", response_model=ApiResponse[UserPublic])
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    user = user_service.update_user(db, user_id, payload, actor)
    return ApiResponse(success=True, data=UserPublic.model_validate(user.to_public_dict()))


@router.delete("/{user_id}", response_model=ApiResponse[dict])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_admin),
):
    user_service.delete_user(db, user_id, actor)
    return ApiResponse(success=True, data={"deleted": True, "id": user_id})


@router.post("/{user_id}/reset-password", response_model=ApiResponse[UserPublic])
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = user_service.reset_password(db, user_id, payload)
    return ApiResponse(success=True, data=UserPublic.model_validate(user.to_public_dict()))
