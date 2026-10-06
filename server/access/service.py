"""Business rules for client status changes."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from server.registry import repository
from server.registry.models import Status

VALID_TRANSITIONS: dict[tuple[Status, Status], bool | str] = {
    (Status.ACTIVE, Status.SUSPENDED): True,
    (Status.ACTIVE, Status.OFFBOARDED): True,
    (Status.SUSPENDED, Status.ACTIVE): True,
    (Status.SUSPENDED, Status.OFFBOARDED): True,
    (Status.OFFBOARDED, Status.ACTIVE): "if_within_retention",
    (Status.OFFBOARDED, Status.SUSPENDED): False,
    (Status.OFFBOARDED, Status.OFFBOARDED): False,
}


class ClientNotFoundError(Exception):
    """Raised when a requested client does not exist."""


class AlreadyOffboardedError(Exception):
    """Raised when an already-offboarded client is offboarded again."""


class InvalidTransitionError(Exception):
    """Raised when a client status transition is not permitted."""


@dataclass(frozen=True)
class StatusChangeResult:
    """Result returned after a client's status changes."""

    slug: str
    status: Status


def is_valid_transition(
    from_status: Status,
    to_status: Status,
    offboarded_at: datetime | None,
) -> bool:
    """Return whether a client may move between the requested statuses.

    Args:
        from_status: Client's current status.
        to_status: Status to apply.
        offboarded_at: When the client was offboarded, if applicable.

    Returns:
        Whether this transition is allowed by the transition table.
    """
    transition = VALID_TRANSITIONS.get((from_status, to_status), False)
    if transition is True:
        return True
    if transition != "if_within_retention" or offboarded_at is None:
        return False

    current_time = datetime.now(UTC)
    if offboarded_at.tzinfo is None:
        offboarded_at = offboarded_at.replace(tzinfo=UTC)
    return current_time - timedelta(days=90) <= offboarded_at <= current_time


async def set_client_status(
    slug: str,
    new_status: Status,
    actor: str,
    ip_address: str | None,
) -> StatusChangeResult:
    """Change client status and append its audit record atomically.

    Args:
        slug: Slug of the client to update.
        new_status: Status to assign.
        actor: Administrator performing the change.
        ip_address: Requester's IP address, if available.

    Returns:
        The slug and new status after the change.

    Raises:
        ClientNotFoundError: If no client has the requested slug.
        AlreadyOffboardedError: If the client is already offboarded.
        InvalidTransitionError: If the requested transition is not allowed.
    """
    client = await repository.get_client_by_slug(slug)
    if client is None:
        raise ClientNotFoundError(f"Client not found: {slug}")
    if client.status is Status.OFFBOARDED and new_status is Status.OFFBOARDED:
        raise AlreadyOffboardedError(f"Client is already offboarded: {slug}")
    if not is_valid_transition(client.status, new_status, client.offboarded_at):
        detail = f"{client.status.value} -> {new_status.value} is not allowed"
        raise InvalidTransitionError(detail)

    timestamp = datetime.now(UTC).isoformat()
    if new_status is Status.OFFBOARDED:
        offboarded_at = timestamp
    elif client.status is Status.OFFBOARDED:
        offboarded_at = None
    else:
        offboarded_at = client.offboarded_at.isoformat() if client.offboarded_at else None

    # Keep the state change and its audit record in one atomic transaction.
    async with repository.transaction() as connection:
        async with connection.execute(
            """
            UPDATE clients
            SET status = ?, offboarded_at = ?, updated_at = ?
            WHERE slug = ?
            """,
            (new_status.value, offboarded_at, timestamp, slug),
        ) as cursor:
            if cursor.rowcount == 0:
                raise ClientNotFoundError(f"Client not found: {slug}")
        await repository.insert_audit_entry(
            str(uuid4()),
            actor,
            "client.status_changed",
            slug,
            client.status.value,
            new_status.value,
            None,
            ip_address,
            timestamp,
            connection=connection,
        )

    return StatusChangeResult(slug=slug, status=new_status)
