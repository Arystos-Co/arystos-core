"""Business rules for user authentication and management."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from server.auth.password import hash_password, verify_password
from server.auth.token import generate_token, hash_token
from server.registry import repository
from server.registry.session_repository import delete_sessions_for_user, get_session_by_token_hash
from server.registry.user_models import User, UserPublic, UserRole
from server.registry.user_repository import (
    get_user_by_id,
    get_user_by_username,
    insert_user,
    list_users,
    update_last_login,
    update_password_hash,
    update_user_active,
    update_user_role,
)

USERNAME_PATTERN = re.compile(r"^[a-z0-9_-]{3,64}$")
MIN_PASSWORD_LENGTH = 12


class AuthenticationError(Exception):
    """Raised when a login or session check fails."""


class DuplicateUsernameError(Exception):
    """Raised when a username already exists."""


class PasswordTooShortError(Exception):
    """Raised when a password is shorter than the minimum allowed length."""


class UsernameInvalidError(Exception):
    """Raised when a username fails validation."""


class LastOwnerError(Exception):
    """Raised when attempting to deactivate the final active owner."""


class UserNotFoundError(Exception):
    """Raised when a requested user cannot be found."""


@dataclass(frozen=True)
class LoginResult:
    """Session token and resolved user profile returned on login."""

    token: str
    user: UserPublic


def _validate_username(username: str) -> None:
    """Validate a dashboard username against the server policy."""
    if not isinstance(username, str) or USERNAME_PATTERN.fullmatch(username) is None:
        raise UsernameInvalidError(
            "username must be 3-64 chars: lowercase letters, digits, hyphen, underscore"
        )


def _validate_password(password: str) -> None:
    """Validate a password length for dashboard accounts."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordTooShortError("password must be at least 12 characters")


def _public_user(user: User) -> UserPublic:
    """Convert a persisted user record into its public representation."""
    return UserPublic.model_validate({
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "active": user.active,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    })


async def login(username: str, password: str) -> LoginResult:
    """Authenticate a username and password and return a fresh session token."""
    user = await get_user_by_username(username)
    if user is None:
        raise AuthenticationError("invalid_credentials")
    if user.active != 1:
        raise AuthenticationError("invalid_credentials")
    if not verify_password(password, user.password_hash):
        raise AuthenticationError("invalid_credentials")

    raw_token = generate_token()
    token_hash = hash_token(raw_token)
    created_at = datetime.now(UTC).isoformat()
    expires_at = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    session_id = str(uuid4())

    from server.registry import session_repository

    await session_repository.insert_session(session_id, user.id, token_hash, created_at, expires_at)
    await update_last_login(user.id, created_at)
    return LoginResult(token=raw_token, user=_public_user(user))


async def logout(session_token: str) -> None:
    """Delete the matching user session when supplied a valid raw token."""
    token_hash = hash_token(session_token)
    session = await get_session_by_token_hash(token_hash)
    if session is None:
        return
    from server.registry import session_repository

    await session_repository.delete_session(session.id)


async def authenticate(session_token: str) -> UserPublic:
    """Resolve a session token to a public user profile or raise an error."""
    token_hash = hash_token(session_token)
    session = await get_session_by_token_hash(token_hash)
    if session is None:
        raise AuthenticationError("invalid_credentials")

    now = datetime.now(UTC).isoformat()
    if session.expires_at < now:
        from server.registry import session_repository

        await session_repository.delete_session(session.id)
        raise AuthenticationError("expired_session")

    user = await get_user_by_id(session.user_id)
    if user is None or user.active != 1:
        if user is not None:
            from server.registry import session_repository

            await session_repository.delete_session(session.id)
        raise AuthenticationError("invalid_credentials")
    return _public_user(user)


async def create_user(
    actor: UserPublic,
    username: str,
    password: str,
    role: str,
) -> UserPublic:
    """Create a user account for a valid owner actor."""
    if actor.role is not UserRole.OWNER:
        raise AuthenticationError("forbidden")

    _validate_username(username)
    _validate_password(password)

    if await get_user_by_username(username) is not None:
        raise DuplicateUsernameError("duplicate_username")

    role_enum = UserRole(role)
    user_id = str(uuid4())
    timestamp = datetime.now(UTC).isoformat()
    password_hash = hash_password(password)
    await insert_user(user_id, username, password_hash, role_enum.value, 1, timestamp, timestamp)

    await repository.insert_audit_entry(
        str(uuid4()),
        actor.username,
        "user.created",
        username,
        None,
        role_enum.value,
        None,
        None,
        timestamp,
    )
    user = await get_user_by_id(user_id)
    if user is None:
        raise UserNotFoundError("user not found")
    return _public_user(user)


async def change_role(actor: UserPublic, user_id: str, new_role: str) -> UserPublic:
    """Change a user's role when the actor is an owner."""
    if actor.role is not UserRole.OWNER:
        raise AuthenticationError("forbidden")
    if actor.id == user_id:
        raise AuthenticationError("forbidden")

    role_enum = UserRole(new_role)
    timestamp = datetime.now(UTC).isoformat()
    user = await get_user_by_id(user_id)
    if user is None:
        raise UserNotFoundError("user not found")

    rows = await update_user_role(user_id, role_enum.value, timestamp)
    if rows == 0:
        raise UserNotFoundError("user not found")

    await repository.insert_audit_entry(
        str(uuid4()),
        actor.username,
        "user.role_changed",
        user.username,
        user.role.value,
        role_enum.value,
        None,
        None,
        timestamp,
    )
    refreshed = await get_user_by_id(user_id)
    if refreshed is None:
        raise UserNotFoundError("user not found")
    return _public_user(refreshed)


async def deactivate_user(actor: UserPublic, user_id: str) -> UserPublic:
    """Soft-deactivate a user while enforcing owner and last-owner rules."""
    if actor.role is not UserRole.OWNER:
        raise AuthenticationError("forbidden")
    if actor.id == user_id:
        raise AuthenticationError("forbidden")

    user = await get_user_by_id(user_id)
    if user is None:
        raise UserNotFoundError("user not found")

    active_owners = [
        entry
        for entry in await list_users()
        if entry.role is UserRole.OWNER and entry.active == 1
    ]
    if len(active_owners) == 1 and active_owners[0].id == user_id:
        raise LastOwnerError("last_owner")

    timestamp = datetime.now(UTC).isoformat()
    rows = await update_user_active(user_id, 0, timestamp)
    if rows == 0:
        raise UserNotFoundError("user not found")
    await delete_sessions_for_user(user_id)
    await repository.insert_audit_entry(
        str(uuid4()),
        actor.username,
        "user.deactivated",
        user.username,
        "1",
        "0",
        None,
        None,
        timestamp,
    )
    refreshed = await get_user_by_id(user_id)
    if refreshed is None:
        raise UserNotFoundError("user not found")
    return _public_user(refreshed)


async def change_password(
    user: User,
    old_password: str,
    new_password: str,
    session_token: str | None = None,
) -> None:
    """Change a user's password and invalidate other active sessions."""
    if not verify_password(old_password, user.password_hash):
        raise AuthenticationError("invalid_credentials")
    _validate_password(new_password)

    new_hash = hash_password(new_password)
    timestamp = datetime.now(UTC).isoformat()
    rows = await update_password_hash(user.id, new_hash, timestamp)
    if rows == 0:
        raise UserNotFoundError("user not found")

    from server.registry import session_repository

    if session_token is not None:
        token_hash = hash_token(session_token)
        session = await get_session_by_token_hash(token_hash)
        if session is not None:
            await session_repository.delete_sessions_for_user(user.id)
            await session_repository.insert_session(
                session.id,
                user.id,
                token_hash,
                session.created_at,
                session.expires_at,
            )
            await session_repository.delete_session(session.id)
        else:
            await delete_sessions_for_user(user.id)
    else:
        await delete_sessions_for_user(user.id)

    await repository.insert_audit_entry(
        str(uuid4()),
        user.username,
        "user.password_changed",
        user.username,
        None,
        None,
        None,
        None,
        timestamp,
    )
