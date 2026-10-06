"""Administrative user-management routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from server.auth.require_role import require_role
from server.registry.auth_service import (
    AuthenticationError,
    DuplicateUsernameError,
    LastOwnerError,
    PasswordTooShortError,
    UsernameInvalidError,
    UserNotFoundError,
    change_role,
    create_user,
    deactivate_user,
)
from server.registry.user_models import UserPublic, UserRole
from server.registry.user_repository import list_users

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


class UserCreateRequest(BaseModel):
    """Body used to create a dashboard user account."""

    username: str
    password: str
    role: Literal["owner", "operator", "read_only"]


class UserPatchRequest(BaseModel):
    """Body used to update a dashboard user's role or status."""

    role: Literal["owner", "operator", "read_only"] | None = None
    active: int | None = None


@router.get("", response_model=list[UserPublic])
async def list_admin_users(
    actor: UserPublic = Depends(require_role(UserRole.OWNER)),  # noqa: B008
) -> list[UserPublic]:
    """Return all persisted users without exposing password hashes."""
    users = await list_users()
    return [UserPublic.model_validate({
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "active": user.active,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }) for user in users]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
async def create_admin_user(
    body: UserCreateRequest,
    actor: UserPublic = Depends(require_role(UserRole.OWNER)),  # noqa: B008
) -> UserPublic:
    """Create a user account with a password-hash and a default active state."""
    try:
        return await create_user(actor, body.username, body.password, body.role)
    except AuthenticationError as exc:
        raise HTTPException(status_code=403, detail="forbidden") from exc
    except DuplicateUsernameError as exc:
        raise HTTPException(status_code=409, detail="duplicate_username") from exc
    except UsernameInvalidError as exc:
        raise HTTPException(status_code=422, detail="username_invalid") from exc
    except PasswordTooShortError as exc:
        raise HTTPException(status_code=422, detail="password_too_short") from exc


@router.patch("/{user_id}", response_model=UserPublic)
async def patch_admin_user(
    user_id: str,
    body: UserPatchRequest,
    actor: UserPublic = Depends(require_role(UserRole.OWNER)),  # noqa: B008
) -> UserPublic:
    """Update a user's role or active status, enforcing owner protections."""
    try:
        if body.role is not None:
            return await change_role(actor, user_id, body.role)
        if body.active is not None:
            return await deactivate_user(actor, user_id)
        raise HTTPException(status_code=422, detail="invalid_input")
    except AuthenticationError as exc:
        raise HTTPException(status_code=403, detail="forbidden") from exc
    except LastOwnerError as exc:
        raise HTTPException(status_code=409, detail="last_owner") from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="user_not_found") from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_user(
    user_id: str,
    actor: UserPublic = Depends(require_role(UserRole.OWNER)),  # noqa: B008
) -> None:
    """Soft-delete a user by deactivating their account and revoking sessions."""
    try:
        await deactivate_user(actor, user_id)
    except AuthenticationError as exc:
        raise HTTPException(status_code=403, detail="forbidden") from exc
    except LastOwnerError as exc:
        raise HTTPException(status_code=409, detail="last_owner") from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="user_not_found") from exc
