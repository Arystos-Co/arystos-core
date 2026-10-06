"""Business rules for administrator payment-status changes."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from server.access.service import ClientNotFoundError
from server.registry import repository
from server.registry.models import PaymentStatus


@dataclass(frozen=True)
class PaymentChangeResult:
    """Result returned after a client's payment status changes."""

    slug: str
    payment_status: PaymentStatus


async def set_payment_status(
    slug: str,
    new_status: PaymentStatus,
    actor: str,
    ip_address: str | None,
) -> PaymentChangeResult:
    """Change client payment status and append its audit record atomically.

    Args:
        slug: Slug of the client to update.
        new_status: Payment status to assign.
        actor: Administrator performing the change.
        ip_address: Requester's IP address, if available.

    Returns:
        The slug and new payment status after the change.

    Raises:
        ClientNotFoundError: If no client has the requested slug.
    """
    client = await repository.get_client_by_slug(slug)
    if client is None:
        raise ClientNotFoundError(f"Client not found: {slug}")

    timestamp = datetime.now(UTC).isoformat()
    # Keep the payment change and its audit record in one atomic transaction.
    async with repository.transaction() as connection:
        async with connection.execute(
            """
            UPDATE clients
            SET payment_status = ?, updated_at = ?
            WHERE slug = ?
            """,
            (new_status.value, timestamp, slug),
        ) as cursor:
            if cursor.rowcount == 0:
                raise ClientNotFoundError(f"Client not found: {slug}")
        await repository.insert_audit_entry(
            str(uuid4()),
            actor,
            "client.payment_status_changed",
            slug,
            client.payment_status.value,
            new_status.value,
            None,
            ip_address,
            timestamp,
            connection=connection,
        )

    return PaymentChangeResult(slug=slug, payment_status=new_status)
