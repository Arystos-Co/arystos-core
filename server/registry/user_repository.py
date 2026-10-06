"""Async persistence for dashboard users and sessions."""

from server.database.connection import get_async_connection
from server.registry.user_models import User


async def insert_user(
    user_id: str,
    username: str,
    password_hash: str,
    role: str,
    active: int,
    created_at: str,
    updated_at: str,
) -> None:
    """Persist a new user record in the database."""
    async with get_async_connection() as connection:
        await connection.execute(
            """
            INSERT INTO users (
                id, username, password_hash, role, active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, password_hash, role, active, created_at, updated_at),
        )
        await connection.commit()


async def get_user_by_username(username: str) -> User | None:
    """Return a user matching a username, if present."""
    async with get_async_connection() as connection:
        async with connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ) as cursor:
            row = await cursor.fetchone()
        return User.model_validate(dict(row)) if row is not None else None


async def get_user_by_id(user_id: str) -> User | None:
    """Return a user matching an internal identifier, if present."""
    async with get_async_connection() as connection:
        async with connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
        return User.model_validate(dict(row)) if row is not None else None


async def list_users() -> list[User]:
    """Return all users ordered newest-first."""
    async with get_async_connection() as connection:
        async with connection.execute(
            "SELECT * FROM users ORDER BY created_at DESC",
        ) as cursor:
            rows = await cursor.fetchall()
        return [User.model_validate(dict(row)) for row in rows]


async def update_user_role(user_id: str, role: str, updated_at: str) -> int:
    """Update a user's role and return the affected row count."""
    async with get_async_connection() as connection:
        async with connection.execute(
            "UPDATE users SET role = ?, updated_at = ? WHERE id = ?",
            (role, updated_at, user_id),
        ) as cursor:
            rows_affected = cursor.rowcount
        await connection.commit()
        return rows_affected


async def update_user_active(user_id: str, active: int, updated_at: str) -> int:
    """Update a user's active flag and return the affected row count."""
    async with get_async_connection() as connection:
        async with connection.execute(
            "UPDATE users SET active = ?, updated_at = ? WHERE id = ?",
            (active, updated_at, user_id),
        ) as cursor:
            rows_affected = cursor.rowcount
        await connection.commit()
        return rows_affected


async def update_last_login(user_id: str, timestamp: str) -> None:
    """Persist the user's last login timestamp."""
    async with get_async_connection() as connection:
        await connection.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (timestamp, timestamp, user_id),
        )
        await connection.commit()


async def update_password_hash(user_id: str, password_hash: str, updated_at: str) -> int:
    """Update the user's password hash and return the affected row count."""
    async with get_async_connection() as connection:
        async with connection.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (password_hash, updated_at, user_id),
        ) as cursor:
            rows_affected = cursor.rowcount
        await connection.commit()
        return rows_affected
