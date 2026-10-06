"""Async persistence for dashboard sessions."""

from server.database.connection import get_async_connection
from server.registry.user_models import Session


async def insert_session(
    session_id: str,
    user_id: str,
    token_hash: str,
    created_at: str,
    expires_at: str,
) -> None:
    """Create a new session row for a user token."""
    async with get_async_connection() as connection:
        await connection.execute(
            """
            INSERT INTO sessions (id, user_id, token_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, token_hash, created_at, expires_at),
        )
        await connection.commit()


async def get_session_by_token_hash(token_hash: str) -> Session | None:
    """Return the session matching a hashed bearer token, if present."""
    async with get_async_connection() as connection:
        async with connection.execute(
            "SELECT * FROM sessions WHERE token_hash = ?",
            (token_hash,),
        ) as cursor:
            row = await cursor.fetchone()
        return Session.model_validate(dict(row)) if row is not None else None


async def delete_session(session_id: str) -> None:
    """Delete a specific session record."""
    async with get_async_connection() as connection:
        await connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await connection.commit()


async def delete_sessions_for_user(user_id: str) -> None:
    """Delete all session rows belonging to a user."""
    async with get_async_connection() as connection:
        await connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        await connection.commit()
