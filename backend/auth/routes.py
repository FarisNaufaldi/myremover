"""Authentication routes: login, logout, session."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.password import verify_password
from config import get_settings
from database import get_db
from deps import get_current_user_optional
from middleware.rate_limit import LoginLockout
from models import User
from schemas import ApiResponse, LoginRequest, SessionData, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])

settings = get_settings()
_login_lockout = LoginLockout(
    max_failures=settings.login_max_failures,
    lockout_seconds=settings.login_lockout_seconds,
)


def _client_key(request: Request, username: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{username.lower()}"


def _format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours} hour{'s' if hours != 1 else ''}"
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    return f"{secs} second{'s' if secs != 1 else ''}"


@router.post("/login", response_model=ApiResponse[UserPublic])
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    key = _client_key(request, payload.username)

    lock = _login_lockout.status(key)
    if lock.locked:
        wait = _format_duration(lock.remaining_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Too many failed login attempts. "
                f"Please try again in {wait}."
            ),
        )

    user = (
        db.query(User)
        .filter(User.username == payload.username.strip().lower())
        .first()
    )

    password_ok = bool(user and verify_password(payload.password, user.password_hash))

    if not password_ok:
        after = _login_lockout.register_failure(key)
        if after.locked:
            wait = _format_duration(after.remaining_seconds)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Too many failed login attempts. "
                    f"Please try again in {wait}."
                ),
            )
        remaining = max(0, settings.login_max_failures - after.failures)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                f"Invalid username or password. "
                f"{remaining} attempt{'s' if remaining != 1 else ''} remaining "
                f"before a {_format_duration(settings.login_lockout_seconds)} lockout."
            ),
        )

    if not user.is_active:
        # Count disable as not a password-brute-force success path; do not reset lockout counter
        # but also don't burn attempts for disabled users if password was correct
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is currently disabled.",
        )

    _login_lockout.reset(key)
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["session_version"] = user.session_version

    return ApiResponse(success=True, data=UserPublic.model_validate(user.to_public_dict()))


@router.post("/logout", response_model=ApiResponse[dict])
def logout(request: Request):
    request.session.clear()
    return ApiResponse(success=True, data={"logged_out": True})


@router.get("/session", response_model=ApiResponse[SessionData])
def session(
    user: User | None = Depends(get_current_user_optional),
):
    if user is None:
        return ApiResponse(
            success=True,
            data=SessionData(authenticated=False, user=None),
        )
    return ApiResponse(
        success=True,
        data=SessionData(
            authenticated=True,
            user=UserPublic.model_validate(user.to_public_dict()),
        ),
    )
