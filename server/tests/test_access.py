"""Integration tests for client status changes and their audit records."""

import sqlite3
from pathlib import Path

import pytest

from server.access.service import (
    AlreadyOffboardedError,
    set_client_status,
)
from server.database import connection as database_connection
from server.registry import repository
from server.registry.models import Status, Tier
from server.registry.service import provision_client


@pytest.fixture
def status_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Initialize an isolated registry database for status-change tests."""
    database_path = tmp_path / "status-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", database_path)
    database_connection.init_db()
    return database_path


async def _provision_status_test_client() -> str:
    """Provision and return the slug used by a status-change test."""
    result = await provision_client(
        "status-test-client",
        "Status Test Guesthouse",
        None,
        None,
        Tier.CORE,
    )
    return result.slug


@pytest.mark.usefixtures("status_database")
async def test_set_status_active_to_suspended() -> None:
    """Suspend an active client and persist the new status."""
    slug = await _provision_status_test_client()

    result = await set_client_status(slug, Status.SUSPENDED, "admin", None)

    client = await repository.get_client_by_slug(slug)
    assert result.status is Status.SUSPENDED
    assert client is not None
    assert client.status is Status.SUSPENDED


@pytest.mark.usefixtures("status_database")
async def test_set_status_suspended_to_active() -> None:
    """Reactivate a suspended client and persist the new status."""
    slug = await _provision_status_test_client()
    await set_client_status(slug, Status.SUSPENDED, "admin", None)

    result = await set_client_status(slug, Status.ACTIVE, "admin", None)

    assert result.status is Status.ACTIVE


@pytest.mark.usefixtures("status_database")
async def test_set_status_active_to_offboarded_sets_offboarded_at() -> None:
    """Set the offboarding timestamp when an active client is offboarded."""
    slug = await _provision_status_test_client()

    await set_client_status(slug, Status.OFFBOARDED, "admin", None)

    client = await repository.get_client_by_slug(slug)
    assert client is not None
    assert client.offboarded_at is not None


@pytest.mark.usefixtures("status_database")
async def test_set_status_offboarded_to_active_within_retention_clears_offboarded_at() -> None:
    """Clear the offboarding timestamp when a recently offboarded client returns."""
    slug = await _provision_status_test_client()
    await set_client_status(slug, Status.OFFBOARDED, "admin", None)

    await set_client_status(slug, Status.ACTIVE, "admin", None)

    client = await repository.get_client_by_slug(slug)
    assert client is not None
    assert client.offboarded_at is None


@pytest.mark.usefixtures("status_database")
async def test_set_status_offboarded_to_offboarded_raises() -> None:
    """Reject a second offboarding request for an already-offboarded client."""
    slug = await _provision_status_test_client()
    await set_client_status(slug, Status.OFFBOARDED, "admin", None)

    with pytest.raises(AlreadyOffboardedError):
        await set_client_status(slug, Status.OFFBOARDED, "admin", None)


@pytest.mark.usefixtures("status_database")
async def test_set_status_inserts_audit_entry() -> None:
    """Record the actor, transition, and request IP in the audit log."""
    slug = await _provision_status_test_client()

    await set_client_status(slug, Status.SUSPENDED, "operator", "203.0.113.8")

    audit_entries = await repository.list_recent_audit_entries()
    status_entries = [entry for entry in audit_entries if entry.action == "client.status_changed"]
    assert len(status_entries) == 1
    assert status_entries[0].actor == "operator"
    assert status_entries[0].old_value == Status.ACTIVE.value
    assert status_entries[0].new_value == Status.SUSPENDED.value
    assert status_entries[0].ip_address == "203.0.113.8"


@pytest.mark.usefixtures("status_database")
async def test_set_status_rolls_back_on_audit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Roll back the status update when inserting its audit row fails."""
    slug = await _provision_status_test_client()

    async def fail_audit_insert(*args: object, **kwargs: object) -> None:
        """Simulate an audit-table failure."""
        raise RuntimeError("audit insert failed")

    monkeypatch.setattr(repository, "insert_audit_entry", fail_audit_insert)
    with pytest.raises(RuntimeError, match="audit insert failed"):
        await set_client_status(slug, Status.SUSPENDED, "admin", None)

    client = await repository.get_client_by_slug(slug)
    assert client is not None
    assert client.status is Status.ACTIVE
    with sqlite3.connect(database_connection.DB_PATH) as connection:
        audit_count = connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert audit_count == 1
