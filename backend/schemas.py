"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import UserRole

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        return v.strip()


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    role: UserRole
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SessionData(BaseModel):
    authenticated: bool
    user: Optional[UserPublic] = None


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=8, max_length=256)
    role: UserRole = UserRole.USER

    @field_validator("name", "username")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

    @field_validator("username")
    @classmethod
    def username_chars(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, _ and -")
        return v.lower()


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    username: Optional[str] = Field(None, min_length=2, max_length=64)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    @field_validator("name", "username")
    @classmethod
    def strip_optional(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v

    @field_validator("username")
    @classmethod
    def username_chars(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, _ and -")
        return v.lower()


class ResetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=256)


class RemoveBackgroundMeta(BaseModel):
    width: int
    height: int
    filename: str
    original_filename: str
    content_type: str
    size_bytes: int


class HealthData(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str
