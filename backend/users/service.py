"""User management service (admin-only operations)."""

from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from auth.password import hash_password
from models import User, UserRole, utcnow
from schemas import ResetPasswordRequest, UserCreate, UserUpdate


def list_users(db: Session, search: Optional[str] = None) -> List[User]:
    q = db.query(User)
    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        q = q.filter(
            or_(
                func.lower(User.name).like(term),
                func.lower(User.username).like(term),
            )
        )
    return q.order_by(User.created_at.desc()).all()


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _count_active_admins(db: Session, exclude_id: Optional[int] = None) -> int:
    q = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True))
    if exclude_id is not None:
        q = q.filter(User.id != exclude_id)
    return q.count()


def create_user(db: Session, payload: UserCreate) -> User:
    existing = db.query(User).filter(User.username == payload.username.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )

    user = User(
        name=payload.name.strip(),
        username=payload.username.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate, actor: User) -> User:
    user = get_user_or_404(db, user_id)
    data = payload.model_dump(exclude_unset=True)

    if "username" in data and data["username"]:
        clash = (
            db.query(User)
            .filter(User.username == data["username"].lower(), User.id != user.id)
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken.",
            )
        user.username = data["username"].lower()

    if "name" in data and data["name"] is not None:
        user.name = data["name"].strip()

    # Role / active flags — protect last active admin
    new_role = data.get("role", user.role)
    new_active = data.get("is_active", user.is_active)
    if isinstance(new_role, str):
        new_role = UserRole(new_role)

    becoming_non_admin = (
        user.role == UserRole.ADMIN
        and (new_role != UserRole.ADMIN or new_active is False)
    )
    if becoming_non_admin and _count_active_admins(db, exclude_id=user.id) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote or disable the last active admin.",
        )

    if "role" in data and data["role"] is not None:
        user.role = data["role"] if isinstance(data["role"], UserRole) else UserRole(data["role"])
    if "is_active" in data and data["is_active"] is not None:
        user.is_active = bool(data["is_active"])
        # Bump session version so disabled users lose live sessions immediately
        if not user.is_active:
            user.session_version = int(user.session_version) + 1

    user.updated_at = utcnow()
    db.commit()
    db.refresh(user)
    return user


def reset_password(db: Session, user_id: int, payload: ResetPasswordRequest) -> User:
    user = get_user_or_404(db, user_id)
    user.password_hash = hash_password(payload.password)
    user.session_version = int(user.session_version) + 1
    user.updated_at = utcnow()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, actor: User) -> None:
    user = get_user_or_404(db, user_id)
    if user.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )
    if user.role == UserRole.ADMIN and user.is_active:
        if _count_active_admins(db, exclude_id=user.id) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last active admin.",
            )
    db.delete(user)
    db.commit()
