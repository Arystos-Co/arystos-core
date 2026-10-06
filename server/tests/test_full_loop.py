"""Full-loop integration tests for the completed server foundation."""

import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.database import connection as database_connection
from server.main import app, handle_unhandled_exception
from server.registry import repository
from server.registry.models import Status, Tier
from server.registry.service import ProvisionResult, provision_client
from server.routers import client as client_router


@pytest.fixture
def database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Initialize an isolated SQLite database for one full-loop test."""
    path = tmp_path / "full-loop-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", path)
    database_connection.init_db()
    return path


@pytest.fixture
def api_client(database_path: Path) -> Iterator[TestClient]:
    """Provide a TestClient connected to the initialized test database."""
    with TestClient(app) as test_client:
        yield test_client


async def _provision_test_client() -> ProvisionResult:
    """Provision a client with the standard test profile."""
    return await provision_client(
        slug="full-loop-client",
        business_name="Full Loop Guesthouse",
        contact_name=None,
        contact_phone=None,
        tier=Tier.CORE,
    )


def _client_headers(token: str) -> dict[str, str]:
    """Build the Authorization header for a provisioned client."""
    return {"Authorization": f"Bearer {token}"}


async def _change_status_and_record_audit(
    slug: str,
    current_status: Status,
    new_status: Status,
) -> None:
    """Persist a status transition and its audit record using available repositories."""
    timestamp = datetime.now(UTC).isoformat()
    offboarded_at = timestamp if new_status is Status.OFFBOARDED else None
    rows_updated = await repository.update_status(
        slug,
        new_status.value,
        offboarded_at,
        timestamp,
    )
    assert rows_updated == 1
    await repository.insert_audit_entry(
        str(uuid4()),
        "test-admin",
        "client.status_changed",
        slug,
        current_status.value,
        new_status.value,
        None,
        None,
        timestamp,
    )


async def test_full_loop_provision_status_suspend_reactivate(api_client: TestClient) -> None:
    """Provision, check, suspend, reactivate, and verify audit records."""
    provision_result = await _provision_test_client()
    headers = _client_headers(provision_result.raw_token)

    active_response = api_client.get("/api/v1/client/status", headers=headers)
    assert active_response.status_code == 200
    assert active_response.json()["status"] == Status.ACTIVE.value

    await _change_status_and_record_audit(
        provision_result.slug,
        Status.ACTIVE,
        Status.SUSPENDED,
    )
    suspended_response = api_client.get("/api/v1/client/status", headers=headers)
    assert suspended_response.status_code == 200
    assert suspended_response.json()["status"] == Status.SUSPENDED.value

    await _change_status_and_record_audit(
        provision_result.slug,
        Status.SUSPENDED,
        Status.ACTIVE,
    )
    reactivated_response = api_client.get("/api/v1/client/status", headers=headers)
    assert reactivated_response.status_code == 200
    assert reactivated_response.json()["status"] == Status.ACTIVE.value

    audit_entries = await repository.list_recent_audit_entries()
    assert len(audit_entries) >= 2


async def test_full_loop_offboard_and_reactivate(database_path: Path) -> None:
    """Verify offboarding timestamps are set and cleared on reactivation."""
    provision_result = await _provision_test_client()

    await repository.update_status(
        provision_result.slug,
        Status.OFFBOARDED.value,
        datetime.now(UTC).isoformat(),
        datetime.now(UTC).isoformat(),
    )
    offboarded_client = await repository.get_client_by_slug(provision_result.slug)
    assert offboarded_client is not None
    assert offboarded_client.offboarded_at is not None

    await repository.update_status(
        provision_result.slug,
        Status.ACTIVE.value,
        None,
        datetime.now(UTC).isoformat(),
    )
    reactivated_client = await repository.get_client_by_slug(provision_result.slug)
    assert reactivated_client is not None
    assert reactivated_client.offboarded_at is None


async def test_delivery_rejects_suspended_client(api_client: TestClient) -> None:
    """Reject installer downloads after the authenticated client is suspended."""
    provision_result = await _provision_test_client()
    await repository.update_status(
        provision_result.slug,
        Status.SUSPENDED.value,
        None,
        datetime.now(UTC).isoformat(),
    )

    response = api_client.get(
        "/api/v1/delivery/installer",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 403


async def test_admin_endpoints_reject_client_token(api_client: TestClient) -> None:
    """Reject a client token when it is used to access administrator endpoints."""
    provision_result = await _provision_test_client()

    response = api_client.get(
        "/api/v1/admin/clients",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 401


async def test_status_endpoint_reads_x_app_version(api_client: TestClient) -> None:
    """Persist a valid version header reported by a provisioned client."""
    provision_result = await _provision_test_client()

    response = api_client.get(
        "/api/v1/client/status",
        headers={
            **_client_headers(provision_result.raw_token),
            "X-App-Version": "1.2.0",
        },
    )

    assert response.status_code == 200
    client_record = await repository.get_client_by_slug(provision_result.slug)
    assert client_record is not None
    assert client_record.app_version == "1.2.0"


async def test_status_endpoint_handles_missing_manifest(
    api_client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the fallback minimum version when the release manifest is missing."""
    monkeypatch.setattr(client_router, "MANIFEST_PATH", tmp_path / "missing-latest.json")
    provision_result = await _provision_test_client()

    response = api_client.get(
        "/api/v1/client/status",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 200
    assert response.json()["app_version_required"] == "0.0.0"


def test_health_endpoint_returns_ok() -> None:
    """Serve health without client authentication or a database check."""
    with TestClient(app) as test_client:
        response = test_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unhandled_exception_is_logged_and_sanitized(caplog: pytest.LogCaptureFixture) -> None:
    """Log the exception traceback while returning no implementation details."""
    test_app = FastAPI()
    test_app.add_exception_handler(Exception, handle_unhandled_exception)

    @test_app.get("/test-error")
    async def raise_test_error() -> None:
        raise RuntimeError("sensitive internal detail")

    with (
        TestClient(test_app, raise_server_exceptions=False) as test_client,
        caplog.at_level(logging.ERROR, logger="server.main"),
    ):
        response = test_client.get("/test-error")

    assert response.status_code == 500
    assert response.json() == {"error": "server_error"}
    assert "Traceback (most recent call last)" in caplog.text
    assert "sensitive internal detail" in caplog.text
    assert "sensitive internal detail" not in response.text


def test_cors_denies_cross_origin_access() -> None:
    """Do not return CORS permission for any cross-origin request."""
    with TestClient(app) as test_client:
        response = test_client.get("/api/health", headers={"Origin": "https://example.com"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
