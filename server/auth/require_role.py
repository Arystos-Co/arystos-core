"""Role-aware authentication dependencies for FastAPI routes."""

import secrets
from collections.abc import Awaitable, Callable

from fastapi import Header, HTTPException

from server import config as config_module
from server.auth import middleware as auth_middleware
from server.auth.token import extract_bearer
from server.registry.auth_service import AuthenticationError, authenticate
from server.registry.user_models import UserPublic, UserRole

type RoleDependency = Callable[[str | None], Awaitable[UserPublic]]


def require_role(*allowed: UserRole) -> RoleDependency:
    """Return a dependency that enforces one of the permitted roles.

    Args:
        allowed: Roles that may access the protected route.

    Returns:
        A FastAPI dependency that validates the Authorization header and either
        returns the authenticated user or raises an HTTP 401/403 error.
    """

    async def dependency(
        authorization: str | None = Header(default=None),
    ) -> UserPublic:
        """Resolve the caller and enforce the allowed role set."""
        raw = extract_bearer(authorization)
        if raw is None:
            raise HTTPException(status_code=401, detail="Authentication required.")

        admin_token = getattr(auth_middleware, "ADMIN_TOKEN", config_module.ADMIN_TOKEN)
        if secrets.compare_digest(raw, admin_token):
            return UserPublic(
                id="admin",
                username="admin",
                role=UserRole.OWNER,
                active=1,
                created_at="",
            )

        try:
            user = await authenticate(raw)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail="invalid_credentials") from exc
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        return user

    return dependency
