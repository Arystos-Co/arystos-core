"""Async database access for client registry and audit records."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import aiosqlite

from server.database.connection import get_async_connection
from server.registry.models import AuditEntry, Client


async def insert_client(
    client_id: str,
    slug: str,
    business_name: str,
    contact_name: str | None,
    contact_phone: str | None,
    token_hash: str,
    tier: str,
    connection: aiosqlite.Connection | None = None,
) -> None:
    """Insert a client with active status and pending payment status.

    Args:
        client_id: Client UUID represented as text.
        slug: Unique client slug.
        business_name: Client business name.
        contact_name: Optional contact name.
        contact_phone: Optional contact phone number.
        token_hash: Hashed client token.
        tier: Client tier.
        connection: Optional active transaction connection.

    Returns:
        None.

    Raises:
        aiosqlite.Error: If the client row cannot be inserted or committed.
    """
    created_at = datetime.now(UTC).isoformat()
    query = """
        INSERT INTO clients (
            id, slug, business_name, contact_name, contact_phone, token_hash,
            tier, status, payment_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    parameters = (
        client_id,
        slug,
        business_name,
        contact_name,
        contact_phone,
        token_hash,
        tier,
        "active",
        "pending",
        created_at,
        created_at,
    )

    if connection is not None:
        await connection.execute(query, parameters)
        return

    async with get_async_connection() as active_connection:
        # Insert the client and initialize its required database fields.
        await active_connection.execute(query, parameters)
        await active_connection.commit()


async def get_client_by_slug(slug: str) -> Client | None:
    """Fetch a client by slug and map the row to a Client model.

    Args:
        slug: Slug of the client to fetch.

    Returns:
        The matching Client, or None if no client has that slug.

    Raises:
        aiosqlite.Error: If the query fails.
        Pydantic ValidationError: If the database row cannot be parsed as a Client.
    """
    async with get_async_connection() as connection:
        # Find a client by its unique slug.
        async with connection.execute(
            "SELECT * FROM clients WHERE slug = ?",
            (slug,),
        ) as cursor:
            row = await cursor.fetchone()
        return Client.model_validate(dict(row)) if row is not None else None


async def get_client_by_token_hash(token_hash: str) -> Client | None:
    """Fetch a client by token hash and map the row to a Client model.

    Args:
        token_hash: Token hash of the client to fetch.

    Returns:
        The matching Client, or None if no client has that token hash.

    Raises:
        aiosqlite.Error: If the query fails.
        Pydantic ValidationError: If the database row cannot be parsed as a Client.
    """
    async with get_async_connection() as connection:
        # Find a client by its unique token hash.
        async with connection.execute(
            "SELECT * FROM clients WHERE token_hash = ?",
            (token_hash,),
        ) as cursor:
            row = await cursor.fetchone()
        return Client.model_validate(dict(row)) if row is not None else None


async def update_last_sync(
    client_id: str,
    app_version: str | None,
    updated_at: str,
) -> None:
    """Update a client's last sync time and optionally its app version.

    Args:
        client_id: UUID of the client to update.
        app_version: New app version, or None to keep the existing version.
        updated_at: Timestamp to store for the sync and row update.

    Returns:
        None.

    Raises:
        aiosqlite.Error: If the update or commit fails.
    """
    async with get_async_connection() as connection:
        # Update the sync timestamp, app version when provided, and row timestamp.
        await connection.execute(
            """
            UPDATE clients
            SET last_sync_at = ?, app_version = COALESCE(?, app_version), updated_at = ?
            WHERE id = ?
            """,
            (updated_at, app_version, updated_at, client_id),
        )
        await connection.commit()


async def update_status(
    slug: str,
    new_status: str,
    offboarded_at: str | None,
    updated_at: str,
) -> int:
    """Update a client's status and return the number of affected rows.

    Args:
        slug: Slug of the client to update.
        new_status: Status to store.
        offboarded_at: Offboarding timestamp, or None.
        updated_at: Timestamp to store for the row update.

    Returns:
        Number of rows affected by the update.

    Raises:
        aiosqlite.Error: If the update or commit fails.
    """
    async with get_async_connection() as connection:
        # Update status and associated timestamps for the matching client.
        async with connection.execute(
            """
            UPDATE clients
            SET status = ?, offboarded_at = ?, updated_at = ?
            WHERE slug = ?
            """,
            (new_status, offboarded_at, updated_at, slug),
        ) as cursor:
            rows_affected = cursor.rowcount
        await connection.commit()
        return rows_affected


async def list_clients() -> list[Client]:
    """Fetch all clients ordered by creation time, newest first.

    Returns:
        Client models ordered by descending creation timestamp.

    Raises:
        aiosqlite.Error: If the query fails.
        Pydantic ValidationError: If a database row cannot be parsed as a Client.
    """
    async with get_async_connection() as connection:
        # Fetch client rows in descending creation-time order.
        async with connection.execute("SELECT * FROM clients ORDER BY created_at DESC") as cursor:
            rows = await cursor.fetchall()
        return [Client.model_validate(dict(row)) for row in rows]


async def update_payment_status(
    slug: str,
    new_status: str,
    updated_at: str,
) -> int:
    """Update a client's payment status and return the number of affected rows.

    Args:
        slug: Slug of the client to update.
        new_status: Payment status to store.
        updated_at: Timestamp to store for the row update.

    Returns:
        Number of rows affected by the update.

    Raises:
        aiosqlite.Error: If the update or commit fails.
    """
    async with get_async_connection() as connection:
        # Update payment status and timestamp for the matching client.
        async with connection.execute(
            "UPDATE clients SET payment_status = ?, updated_at = ? WHERE slug = ?",
            (new_status, updated_at, slug),
        ) as cursor:
            rows_affected = cursor.rowcount
        await connection.commit()
        return rows_affected


async def insert_audit_entry(
    entry_id: str,
    actor: str,
    action: str,
    target_slug: str,
    old_value: str | None,
    new_value: str | None,
    reason: str | None,
    ip_address: str | None,
    timestamp: str,
    connection: aiosqlite.Connection | None = None,
) -> None:
    """Insert an audit record.

    Args:
        entry_id: UUID of the audit entry represented as text.
        actor: Actor who performed the action.
        action: Action recorded in the audit log.
        target_slug: Slug of the affected client.
        old_value: Previous value, if available.
        new_value: New value, if available.
        reason: Optional reason for the action.
        ip_address: Optional actor IP address.
        timestamp: Timestamp of the audit action.
        connection: Optional active transaction connection.

    Returns:
        None.

    Raises:
        aiosqlite.Error: If the audit row cannot be inserted or committed.
    """
    query = """
        INSERT INTO audit_log (
            id, actor, action, target_slug, old_value, new_value, reason,
            ip_address, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    parameters = (
        entry_id,
        actor,
        action,
        target_slug,
        old_value,
        new_value,
        reason,
        ip_address,
        timestamp,
    )

    if connection is not None:
        await connection.execute(query, parameters)
        return

    async with get_async_connection() as active_connection:
        # Append the supplied event to the audit log.
        await active_connection.execute(query, parameters)
        await active_connection.commit()


async def list_recent_audit_entries(limit: int = 100) -> list[AuditEntry]:
    """Fetch the newest audit entries up to the requested limit.

    Args:
        limit: Maximum number of audit entries to fetch.

    Returns:
        AuditEntry models ordered by descending timestamp.

    Raises:
        aiosqlite.Error: If the query fails.
        Pydantic ValidationError: If a database row cannot be parsed as an AuditEntry.
    """
    async with get_async_connection() as connection:
        # Fetch the newest audit entries while applying the requested row limit.
        async with connection.execute(
            "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
        return [AuditEntry.model_validate(dict(row)) for row in rows]


@asynccontextmanager
async def transaction() -> AsyncIterator[aiosqlite.Connection]:
    """Yield a connection and commit or roll back its transaction.

    Returns:
        An async iterator yielding the active aiosqlite connection.

    Raises:
        BaseException: Re-raises any exception from the context body after rollback.
        aiosqlite.Error: If connecting, committing, or rolling back fails.
    """
    async with get_async_connection() as connection:
        try:
            yield connection
            await connection.commit()
        except BaseException:
            await connection.rollback()
            raise
