"""HTTP tests for authenticated installer delivery."""

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.database import connection as database_connection
from server.delivery import service as delivery_service
from server.main import app
from server.registry.models import Tier
from server.registry.service import ProvisionResult, provision_client


@pytest.fixture
def api_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Provide an API client backed by an isolated SQLite database."""
    database_path = tmp_path / "delivery-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", database_path)
    database_connection.init_db()

    releases_dir = tmp_path / "releases"
    releases_dir.mkdir()
    manifest_path = tmp_path / "server-releases" / "latest.json"
    manifest_path.parent.mkdir()
    monkeypatch.setattr(delivery_service, "RELEASES_DIR", releases_dir)
    monkeypatch.setattr(delivery_service, "MANIFEST_PATH", manifest_path)

    with TestClient(app) as test_client:
        yield test_client


async def _provision_delivery_client() -> ProvisionResult:
    """Create the standard client used by delivery endpoint tests."""
    return await provision_client(
        slug="delivery-test-client",
        business_name="Delivery Test Guesthouse",
        contact_name=None,
        contact_phone=None,
        tier=Tier.CORE,
    )


def _client_headers(token: str) -> dict[str, str]:
    """Build an authorization header for a provisioned client."""
    return {"Authorization": f"Bearer {token}"}


def _write_manifest(manifest_path: Path, version: str) -> None:
    """Write a minimal latest-release manifest for an installer version."""
    manifest_path.write_text(
        json.dumps({"latest_version": version}),
        encoding="utf-8",
    )


async def test_delivery_streams_installer_for_active_client(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Stream the active client's installer and return its SHA-256 checksum."""
    provision_result = await _provision_delivery_client()
    version = "1.2.3"
    releases_dir = tmp_path / "releases"
    installer_path = releases_dir / f"arystos-{Tier.CORE.value}-{version}.msi"
    installer_content = b"test installer content"
    installer_path.write_bytes(installer_content)
    manifest_path = tmp_path / "server-releases" / "latest.json"
    _write_manifest(manifest_path, version)

    response = api_client.get(
        "/api/v1/delivery/installer",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.headers["content-disposition"] == (
        'attachment; filename="arystos-setup.msi"'
    )
    assert response.headers["x-checksum-sha256"] == hashlib.sha256(installer_content).hexdigest()
    assert response.content == installer_content


async def test_delivery_returns_503_when_installer_missing(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Return a structured 503 when the manifest's tier installer is absent."""
    provision_result = await _provision_delivery_client()
    _write_manifest(tmp_path / "server-releases" / "latest.json", "1.2.3")

    response = api_client.get(
        "/api/v1/delivery/installer",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 503
    assert response.json() == {"error": "installer_unavailable"}
