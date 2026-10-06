"""HTTP tests for authenticated release-manifest delivery."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.database import connection as database_connection
from server.main import app
from server.registry.models import Tier
from server.registry.service import ProvisionResult, provision_client
from server.updates import manifest as manifest_module


@pytest.fixture
def api_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Provide an API client backed by an isolated database and releases directory."""
    database_path = tmp_path / "updates-test.db"
    monkeypatch.setattr(database_connection, "DB_PATH", database_path)
    database_connection.init_db()

    releases_directory = tmp_path / "releases"
    releases_directory.mkdir()
    monkeypatch.setattr(manifest_module, "MANIFEST_PATH", releases_directory / "latest.json")

    with TestClient(app) as test_client:
        yield test_client


async def _provision_updates_client() -> ProvisionResult:
    """Create the active client used by update-manifest endpoint tests."""
    return await provision_client(
        slug="updates-test-client",
        business_name="Updates Test Guesthouse",
        contact_name=None,
        contact_phone=None,
        tier=Tier.CORE,
    )


def _client_headers(token: str) -> dict[str, str]:
    """Build authorization headers for a provisioned client."""
    return {"Authorization": f"Bearer {token}"}


def _write_manifest(manifest_path: Path) -> dict[str, int | str]:
    """Write a valid release manifest and return the data written."""
    manifest: dict[str, int | str] = {
        "manifest_version": 1,
        "latest_version": "1.2.3",
        "min_supported_version": "1.0.0",
        "released_at": "2026-10-05T10:00:00Z",
        "release_notes": "Stability and performance improvements.",
        "download_url": "https://example.com/arystos-setup.msi",
        "checksum": "a" * 64,
        "signature": "test-signature",
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


async def test_manifest_returns_for_active_client(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Return the validated manifest to an active authenticated client."""
    provision_result = await _provision_updates_client()
    manifest_path = tmp_path / "releases" / "latest.json"
    expected_manifest = _write_manifest(manifest_path)

    response = api_client.get(
        "/api/v1/updates/manifest",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 200
    assert response.json() == expected_manifest


async def test_manifest_returns_503_when_missing(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Return a structured 503 when the release manifest does not exist."""
    provision_result = await _provision_updates_client()
    manifest_path = tmp_path / "releases" / "latest.json"
    assert not manifest_path.exists()

    response = api_client.get(
        "/api/v1/updates/manifest",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 503
    assert response.json() == {"error": "manifest_unavailable"}


async def test_manifest_returns_503_when_malformed(
    api_client: TestClient,
    tmp_path: Path,
) -> None:
    """Return a structured 503 when the release manifest is malformed."""
    provision_result = await _provision_updates_client()
    manifest_path = tmp_path / "releases" / "latest.json"
    manifest_path.write_text("{not valid JSON", encoding="utf-8")

    response = api_client.get(
        "/api/v1/updates/manifest",
        headers=_client_headers(provision_result.raw_token),
    )

    assert response.status_code == 503
    assert response.json() == {"error": "manifest_unavailable"}
