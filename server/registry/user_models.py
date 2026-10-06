"""Pydantic models for dashboard users and authenticated sessions."""

from enum import StrEnum

from pydantic import BaseModel


class UserRole(StrEnum):
    """Application roles for dashboard users."""

    OWNER = "owner"
    OPERATOR = "operator"
    READ_ONLY = "read_only"


class User(BaseModel):
    """Stored database row for a dashboard user."""

    id: str
    username: str
    password_hash: str
    role: UserRole
    active: int
    last_login_at: str | None = None
    created_at: str
    updated_at: str


class Session(BaseModel):
    """Stored session record representing a bearer token."""

    id: str
    user_id: str
    token_hash: str
    created_at: str
    expires_at: str


class UserPublic(BaseModel):
    """Public user payload stripped of password information."""

    id: str
    username: str
    role: UserRole
    active: int
    last_login_at: str | None = None
    created_at: str
