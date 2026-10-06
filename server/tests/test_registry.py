"""Integration tests for registry service and repository behavior."""

import sqlite3
from pathlib import Path

import pytest

from server.auth.token import hash_token
from server.database import connection as database_connection
from server.registry import repository
from server.registry.models import Tier
from server.registry.service import DuplicateSlugError, provision_client


@pytest.fixture
def registry_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Create the registry and audit tables in a temporary SQLite database."""
    database_path = tmp_path / "registry-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", database_path)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE clients (
                id TEXT PRIMARY KEY,
                slug TEXT NOT NULL UNIQUE,
                business_name TEXT NOT NULL,
                contact_name TEXT,
                contact_phone TEXT,
                token_hash TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL CHECK (tier IN ('core','growth','advanced')),
                status TEXT NOT NULL CHECK (status IN ('active','suspended','offboarded')),
                app_version TEXT,
                last_sync_at TEXT,
                last_update_at TEXT,
                payment_status TEXT NOT NULL CHECK (
                    payment_status IN ('paid','pending','overdue')
                ),
                contract_start TEXT,
                offboarded_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE UNIQUE INDEX idx_clients_token_hash ON clients(token_hash);
            CREATE UNIQUE INDEX idx_clients_slug ON clients(slug);
            CREATE INDEX idx_clients_status ON clients(status);
            CREATE INDEX idx_clients_last_sync ON clients(last_sync_at);
            CREATE INDEX idx_clients_offboarded ON clients(offboarded_at);

            CREATE TABLE audit_log (
                id TEXT PRIMARY KEY,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                target_slug TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                ip_address TEXT,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX idx_audit_target_time ON audit_log(target_slug, timestamp);
            CREATE INDEX idx_audit_time ON audit_log(timestamp);
            """
        )


@pytest.mark.usefixtures("registry_database")
async def test_provision_client_inserts_row() -> None:
    """Persist a client and the corresponding provisioning audit entry."""
    result = await provision_client(
        "pearlsky",
        "PearlSky Guesthouse",
        "A. Contact",
        "+27123456789",
        Tier.CORE,
    )

    client = await repository.get_client_by_slug(result.slug)
    assert client is not None
    assert str(client.id) == result.client_id
    assert client.business_name == "PearlSky Guesthouse"
    assert client.tier is Tier.CORE
    assert client.token_hash == hash_token(result.raw_token)

    audit_entries = await repository.list_recent_audit_entries()
    assert len(audit_entries) == 1
    assert audit_entries[0].target_slug == result.slug


@pytest.mark.usefixtures("registry_database")
async def test_provision_client_rejects_duplicate_slug() -> None:
    """Translate a duplicate slug database constraint into a domain error."""
    details = ("pearlsky", "PearlSky Guesthouse", None, None, Tier.CORE)
    await provision_client(*details)

    with pytest.raises(DuplicateSlugError):
        await provision_client(*details)


@pytest.mark.usefixtures("registry_database")
async def test_provision_client_returns_raw_token_once() -> None:
    """Return the generated raw token while persisting only its hash."""
    result = await provision_client(
        "pearlsky",
        "PearlSky Guesthouse",
        None,
        None,
        Tier.GROWTH,
    )

    assert result.raw_token
    assert result.raw_token != hash_token(result.raw_token)
    client = await repository.get_client_by_token_hash(hash_token(result.raw_token))
    assert client is not None
    assert client.token_hash == hash_token(result.raw_token)


@pytest.mark.usefixtures("registry_database")
async def test_get_client_by_token_hash_returns_client() -> None:
    """Find a provisioned client by the hash of its raw token."""
    result = await provision_client(
        "pearlsky",
        "PearlSky Guesthouse",
        None,
        None,
        Tier.ADVANCED,
    )

    client = await repository.get_client_by_token_hash(hash_token(result.raw_token))

    assert client is not None
    assert client.slug == result.slug


@pytest.mark.usefixtures("registry_database")
async def test_get_client_by_token_hash_returns_none_for_unknown() -> None:
    """Return None when no client has the requested token hash."""
    client = await repository.get_client_by_token_hash(hash_token("unknown-token"))

    assert client is None
