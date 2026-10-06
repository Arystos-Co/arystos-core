"""HTTP tests for the client status and unauthenticated health endpoints."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.auth.token import hash_token
from server.database import connection as database_connection
from server.routers import client as client_router

CLIENT_ID = "76ee8b2b-d4a8-4c31-9aca-2c1f2c2cfacf"
CLIENT_TOKEN = "test-client-token"
CLIENT_SLUG = "pearlsky"
AUTHORIZATION_HEADERS = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
TEST_TIMESTAMP = "2026-01-01T00:00:00+00:00"


@pytest.fixture
def api_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Create an isolated migrated SQLite database and FastAPI test client."""
    database_path = tmp_path / "client-status-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", database_path)
    database_connection.init_db()

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO clients (
                id, slug, business_name, token_hash, tier, status,
                payment_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                CLIENT_ID,
                CLIENT_SLUG,
                "PearlSky Guesthouse",
                hash_token(CLIENT_TOKEN),
                "core",
                "active",
                "paid",
                TEST_TIMESTAMP,
                TEST_TIMESTAMP,
            ),
        )

    test_app = FastAPI()
    test_app.include_router(client_router.router)
    with TestClient(test_app) as test_client:
        yield test_client


def _set_client_status(status: str, database_path: Path) -> None:
    """Set the fixture client's status in its isolated database."""
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE clients SET status = ? WHERE id = ?",
            (status, CLIENT_ID),
        )


def _read_client_app_version(database_path: Path) -> str | None:
    """Read the fixture client's application version from its isolated database."""
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT app_version FROM clients WHERE id = ?",
            (CLIENT_ID,),
        ).fetchone()
    return row[0] if row is not None else None


def test_status_returns_active_for_active_client(api_client: TestClient) -> None:
    """Return the active client status and null message."""
    response = api_client.get("/api/v1/client/status", headers=AUTHORIZATION_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "status": "active",
        "business_name": "PearlSky Guesthouse",
        "tier": "core",
        "app_version_required": "0.0.0",
        "message": None,
    }


def test_status_returns_200_and_suspended_for_suspended_client(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Return a successful status response for a suspended client."""
    _set_client_status("suspended", tmp_path / "client-status-test.db")

    response = api_client.get("/api/v1/client/status", headers=AUTHORIZATION_HEADERS)

    assert response.status_code == 200
    assert response.json()["status"] == "suspended"
    assert response.json()["message"] == "Your account has been suspended. Contact ARYSTOS."


def test_status_returns_200_and_offboarded_for_offboarded_client(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Return a successful status response for an offboarded client."""
    _set_client_status("offboarded", tmp_path / "client-status-test.db")

    response = api_client.get("/api/v1/client/status", headers=AUTHORIZATION_HEADERS)

    assert response.status_code == 200
    assert response.json()["status"] == "offboarded"
    assert response.json()["message"] == "This account has been permanently deactivated."


def test_status_returns_401_for_invalid_token(api_client: TestClient) -> None:
    """Reject a bearer token that does not exist in the client registry."""
    response = api_client.get(
        "/api/v1/client/status",
        headers={"Authorization": "Bearer unknown-token"},
    )

    assert response.status_code == 401


def test_status_returns_401_for_missing_token(api_client: TestClient) -> None:
    """Reject a status request without an Authorization header."""
    response = api_client.get("/api/v1/client/status")

    assert response.status_code == 401


def test_status_reads_x_app_version_header(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Persist a valid application version reported by a status check."""
    response = api_client.get(
        "/api/v1/client/status",
        headers={**AUTHORIZATION_HEADERS, "X-App-Version": "1.2.0"},
    )

    assert response.status_code == 200
    assert _read_client_app_version(tmp_path / "client-status-test.db") == "1.2.0"


def test_status_handles_missing_manifest(
    api_client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use the fallback minimum version when the manifest does not exist."""
    monkeypatch.setattr(client_router, "MANIFEST_PATH", tmp_path / "missing-latest.json")

    response = api_client.get("/api/v1/client/status", headers=AUTHORIZATION_HEADERS)

    assert response.status_code == 200
    assert response.json()["app_version_required"] == "0.0.0"
