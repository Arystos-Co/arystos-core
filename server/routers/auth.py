"""Authentication routes for dashboard user sessions."""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from server.auth.require_role import require_role
from server.auth.token import extract_bearer
from server.config import ADMIN_TOKEN
from server.registry import auth_service, user_repository
from server.registry.auth_service import (
    AuthenticationError,
    PasswordTooShortError,
    UsernameInvalidError,
)
from server.registry.user_models import UserPublic, UserRole

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Request payload submitted when a user logs in."""

    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    """Request payload for changing the current user's password."""

    old_password: str
    new_password: str


@router.post("/login")
async def login(request: LoginRequest) -> dict[str, object]:
    """Authenticate a user and return a short-lived session token."""
    try:
        result = await auth_service.login(request.username, request.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="invalid_credentials") from exc
    return {"token": result.token, "user": result.user.model_dump()}


@router.post("/logout")
async def logout(
    authorization: str | None = Header(default=None),
) -> None:
    """Delete a user session when one is present in the Authorization header."""
    raw_token = extract_bearer(authorization)
    if raw_token is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if raw_token == ADMIN_TOKEN:
        return
    await auth_service.logout(raw_token)


@router.get("/me", response_model=UserPublic)
async def me(
    user: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR, UserRole.READ_ONLY)),  # noqa: B008
) -> UserPublic:
    """Return the current authenticated user without exposing password data."""
    if user.id == "admin":
        return user
    stored_user = await user_repository.get_user_by_id(user.id)
    if stored_user is None:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    return UserPublic.model_validate({
        "id": stored_user.id,
        "username": stored_user.username,
        "role": stored_user.role,
        "active": stored_user.active,
        "last_login_at": stored_user.last_login_at,
        "created_at": stored_user.created_at,
    })


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    authorization: str | None = Header(default=None),
    user: UserPublic = Depends(require_role(UserRole.OWNER, UserRole.OPERATOR, UserRole.READ_ONLY)),  # noqa: B008
) -> None:
    """Change the current user's password and revoke other sessions."""
    if user.id == "admin":
        raise HTTPException(status_code=401, detail="invalid_credentials")
    raw_token = extract_bearer(authorization)
    if raw_token is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    stored_user = await user_repository.get_user_by_id(user.id)
    if stored_user is None:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    try:
        await auth_service.change_password(
            stored_user,
            request.old_password,
            request.new_password,
            raw_token,
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="invalid_credentials") from exc
    except PasswordTooShortError as exc:
        raise HTTPException(status_code=422, detail="password_too_short") from exc
    except UsernameInvalidError as exc:
        raise HTTPException(status_code=422, detail="username_invalid") from exc
