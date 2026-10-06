"""Client-facing API routes."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from fastapi import APIRouter, Depends, Header

from server.auth.middleware import require_client
from server.registry import repository
from server.registry.models import Client, Status
from server.routers.schemas import StatusResponse

router = APIRouter(prefix="/api/v1/client", tags=["client"])
MANIFEST_PATH: Final[Path] = Path(__file__).resolve().parents[1] / "releases" / "latest.json"
SEMVER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
STATUS_MESSAGES: Final[dict[Status, str | None]] = {
    Status.ACTIVE: None,
    Status.SUSPENDED: "Your account has been suspended. Contact ARYSTOS.",
    Status.OFFBOARDED: "This account has been permanently deactivated.",
}


def _is_valid_semver(version: str) -> bool:
    """Return whether a string is a valid three-part semantic version."""
    match = SEMVER_PATTERN.fullmatch(version)
    if match is None:
        return False

    prerelease = match.group(4)
    if prerelease is None:
        return True
    return all(
        not (identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"))
        for identifier in prerelease.split(".")
    )


def _read_min_supported_version() -> str:
    """Read the minimum supported version, defaulting when no usable manifest exists."""
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "0.0.0"

    if not isinstance(manifest, dict):
        return "0.0.0"
    min_supported_version = manifest.get("min_supported_version")
    return min_supported_version if isinstance(min_supported_version, str) else "0.0.0"


async def get_client_status(
    client: Client = Depends(require_client),  # noqa: B008
    x_app_version: str | None = Header(default=None, alias="X-App-Version"),
) -> StatusResponse:
    """Return client account state and record this status check.

    Args:
        client: Authenticated client registry record.
        x_app_version: Optional semantic version reported by the client.

    Returns:
        The client's status and the minimum supported application version.
    """
    app_version = (
        x_app_version if x_app_version is not None and _is_valid_semver(x_app_version) else None
    )
    timestamp = datetime.now(UTC).isoformat()
    await repository.update_last_sync(str(client.id), app_version, timestamp)

    return StatusResponse(
        status=client.status,
        business_name=client.business_name,
        tier=client.tier,
        app_version_required=_read_min_supported_version(),
        message=STATUS_MESSAGES[client.status],
    )


router.add_api_route(
    "/status",
    get_client_status,
    methods=["GET"],
    response_model=StatusResponse,
)
