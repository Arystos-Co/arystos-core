"""HTTP integration tests for administrator endpoints."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.auth import middleware as auth_middleware
from server.database import connection as database_connection
from server.main import app
from server.registry import repository
from server.registry.models import PaymentStatus, Status, Tier
from server.registry.service import provision_client

ADMIN_TOKEN = "admin-integration-test-token"
ADMIN_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}


@pytest.fixture
def admin_api_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Create an authenticated administrator client backed by an isolated database."""
    database_path = tmp_path / "admin-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", database_path)
    monkeypatch.setattr(auth_middleware, "ADMIN_TOKEN", ADMIN_TOKEN)
    database_connection.init_db()

    with TestClient(app) as test_client:
        yield test_client


async def _provision_admin_test_client() -> str:
    """Provision and return the slug used by administrator route tests."""
    result = await provision_client(
        "admin-test-client",
        "Admin Test Guesthouse",
        "Admin Test Contact",
        None,
        Tier.GROWTH,
    )
    return result.slug


async def test_admin_clients_endpoint_omits_token_hash(
    admin_api_client: TestClient,
) -> None:
    """Return client summaries without exposing credential hashes."""
    slug = await _provision_admin_test_client()

    response = admin_api_client.get("/api/v1/admin/clients", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json()[0]["slug"] == slug
    assert "token_hash" not in response.json()[0]


async def test_admin_client_detail_endpoint_returns_client_details(
    admin_api_client: TestClient,
) -> None:
    """Return contact and lifecycle details for a client slug."""
    slug = await _provision_admin_test_client()

    response = admin_api_client.get(f"/api/v1/admin/clients/{slug}", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json()["contact_name"] == "Admin Test Contact"
    assert "token_hash" not in response.json()


async def test_admin_audit_endpoint_returns_recent_entries(
    admin_api_client: TestClient,
) -> None:
    """Return recent audit entries to an authenticated administrator."""
    slug = await _provision_admin_test_client()

    response = admin_api_client.get("/api/v1/admin/audit", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json()[0]["target_slug"] == slug
    assert response.json()[0]["action"] == "client.provisioned"


async def test_admin_status_and_payment_endpoints_record_changes(
    admin_api_client: TestClient,
) -> None:
    """Persist status and payment changes with audit entries and request IPs."""
    slug = await _provision_admin_test_client()

    status_response = admin_api_client.post(
        f"/api/v1/admin/clients/{slug}/status",
        headers=ADMIN_HEADERS,
        json={"status": Status.SUSPENDED.value},
    )
    payment_response = admin_api_client.post(
        f"/api/v1/admin/clients/{slug}/payment",
        headers=ADMIN_HEADERS,
        json={"payment_status": PaymentStatus.OVERDUE.value},
    )

    assert status_response.status_code == 200
    assert status_response.json() == {"slug": slug, "status": Status.SUSPENDED.value}
    assert payment_response.status_code == 200
    assert payment_response.json() == {
        "slug": slug,
        "payment_status": PaymentStatus.OVERDUE.value,
    }
    client = await repository.get_client_by_slug(slug)
    assert client is not None
    assert client.status is Status.SUSPENDED
    assert client.payment_status is PaymentStatus.OVERDUE

    audit_entries = await repository.list_recent_audit_entries()
    action_values = {entry.action: entry for entry in audit_entries}
    assert action_values["client.status_changed"].ip_address == "testclient"
    assert action_values["client.payment_status_changed"].ip_address == "testclient"


async def test_admin_status_endpoint_returns_canonical_validation_error(
    admin_api_client: TestClient,
) -> None:
    """Return the documented error shape for a status outside the allowed values."""
    response = admin_api_client.post(
        "/api/v1/admin/clients/unknown/status",
        headers=ADMIN_HEADERS,
        json={"status": "invalid"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": "invalid_input",
        "detail": "status must be one of: active, suspended, offboarded",
    }


async def test_admin_payment_endpoint_returns_not_found_for_unknown_client(
    admin_api_client: TestClient,
) -> None:
    """Return the canonical not-found response for an unknown client slug."""
    response = admin_api_client.post(
        "/api/v1/admin/clients/unknown/payment",
        headers=ADMIN_HEADERS,
        json={"payment_status": PaymentStatus.PAID.value},
    )

    assert response.status_code == 404
    assert response.json() == {"error": "client_not_found"}


async def test_admin_regenerate_token_endpoint_rotates_client_token(
    admin_api_client: TestClient,
) -> None:
    """Rotate a client's token for the configured admin operator."""
    slug = await _provision_admin_test_client()

    response = admin_api_client.post(
        f"/api/v1/admin/clients/{slug}/regenerate-token",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["slug"] == slug
    assert len(response.json()["raw_token"]) == 64


async def test_admin_client_audit_endpoint_filters_by_client_slug(
    admin_api_client: TestClient,
) -> None:
    """Return only the requested client's audit entries."""
    slug = await _provision_admin_test_client()

    response = admin_api_client.get(
        f"/api/v1/admin/clients/{slug}/audit",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()[0]["target_slug"] == slug
