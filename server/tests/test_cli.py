"""Integration tests for the command-line interfaces."""

import asyncio
import sys
from pathlib import Path

import pytest

from server.cli import list_clients, manage_client, provision_client
from server.database import connection as database_connection
from server.registry import repository
from server.registry.models import Tier
from server.registry.service import provision_client as create_client


@pytest.fixture
def cli_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialize the schema in a temporary database for one CLI test."""
    database_path = tmp_path / "cli-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", database_path)
    database_connection.init_db()


def _set_arguments(monkeypatch: pytest.MonkeyPatch, arguments: list[str]) -> None:
    """Replace process arguments with those for a CLI invocation."""
    monkeypatch.setattr(sys, "argv", arguments)


def test_provision_client_creates_client(
    cli_database: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Provision a client from CLI arguments and verify its database record."""
    _set_arguments(
        monkeypatch,
        [
            "provision_client",
            "--slug",
            "pearlsky",
            "--business",
            "PearlSky Guesthouse",
            "--contact-name",
            "A. Contact",
            "--contact-phone",
            "+27123456789",
            "--tier",
            "core",
        ],
    )

    provision_client.main()

    output = capsys.readouterr().out
    client = asyncio.run(repository.get_client_by_slug("pearlsky"))
    assert client is not None
    assert "slug: pearlsky" in output
    assert f"client_id: {client.id}" in output
    assert "raw_token: " in output


def test_provision_client_rejects_duplicate_slug(
    cli_database: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exit with code 1 when provisioning an already-registered slug."""
    arguments = [
        "provision_client",
        "--slug",
        "pearlsky",
        "--business",
        "PearlSky Guesthouse",
        "--tier",
        "core",
    ]
    _set_arguments(monkeypatch, arguments)
    provision_client.main()

    with pytest.raises(SystemExit) as error:
        provision_client.main()

    assert error.value.code == 1


def test_list_clients_prints_table(
    cli_database: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Print a client table containing every registered client."""
    asyncio.run(create_client("pearlsky", "PearlSky Guesthouse", None, None, Tier.CORE))
    asyncio.run(create_client("mountainview", "Mountain View Lodge", None, None, Tier.CORE))
    _set_arguments(monkeypatch, ["list_clients"])

    list_clients.main()

    output = capsys.readouterr().out
    assert "SLUG" in output
    assert "BUSINESS" in output
    assert "TIER" in output
    assert "STATUS" in output
    assert "APP_VERSION" in output
    assert "LAST_SYNC" in output
    assert "PAYMENT" in output
    assert "pearlsky" in output
    assert "mountainview" in output


def test_list_clients_reports_empty_registry(
    cli_database: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Print the documented message when the registry has no clients."""
    _set_arguments(monkeypatch, ["list_clients"])

    list_clients.main()

    assert capsys.readouterr().out == "No clients found.\n"


def test_manage_client_suspends_and_reactivates(
    cli_database: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Suspend and reactivate a client through the status-management CLI."""
    asyncio.run(create_client("pearlsky", "PearlSky Guesthouse", None, None, Tier.CORE))

    _set_arguments(
        monkeypatch,
        ["manage_client", "status", "--slug", "pearlsky", "--value", "suspended"],
    )
    manage_client.main()
    suspended_client = asyncio.run(repository.get_client_by_slug("pearlsky"))
    assert suspended_client is not None
    assert suspended_client.status.value == "suspended"
    assert "suspended" in capsys.readouterr().out

    _set_arguments(
        monkeypatch,
        ["manage_client", "status", "--slug", "pearlsky", "--value", "active"],
    )
    manage_client.main()
    active_client = asyncio.run(repository.get_client_by_slug("pearlsky"))
    assert active_client is not None
    assert active_client.status.value == "active"
    assert "active" in capsys.readouterr().out


def test_manage_client_changes_payment_status(
    cli_database: None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Update and persist a client's payment status through the CLI."""
    asyncio.run(create_client("pearlsky", "PearlSky Guesthouse", None, None, Tier.CORE))
    _set_arguments(
        monkeypatch,
        ["manage_client", "payment", "--slug", "pearlsky", "--value", "paid"],
    )

    manage_client.main()

    client = asyncio.run(repository.get_client_by_slug("pearlsky"))
    assert client is not None
    assert client.payment_status.value == "paid"
    assert capsys.readouterr().out == "Client pearlsky payment status set to paid.\n"
