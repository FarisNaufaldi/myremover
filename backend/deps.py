"""FastAPI dependencies: auth, admin, DB."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole


def _session_user_id(request: Request) -> Optional[int]:
    raw = request.session.get("user_id")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    user_id = _session_user_id(request)
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        return None
    # Invalidate stale sessions after password reset / disable / role changes
    sv = request.session.get("session_version")
    if sv is None or int(sv) != int(user.session_version):
        request.session.clear()
        return None
    if not user.is_active:
        request.session.clear()
        return None
    return user


def require_auth(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user


def require_admin(user: User = Depends(require_auth)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user
