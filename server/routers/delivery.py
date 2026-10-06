"""Installer delivery API routes."""

import hashlib
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from server.auth.middleware import require_active_client
from server.delivery.service import InstallerUnavailableError, get_installer_path
from server.registry.models import Client

router = APIRouter(prefix="/api/v1/delivery", tags=["delivery"])


def _calculate_sha256(installer_path: Path) -> str:
    """Calculate a file's SHA-256 digest without loading the whole installer into memory.

    Args:
        installer_path: Installer file whose digest should be calculated.

    Returns:
        Lowercase hexadecimal SHA-256 digest of the file.
    """
    digest = hashlib.sha256()
    with installer_path.open("rb") as installer_file:
        while chunk := installer_file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _stream_file(installer_path: Path) -> Iterator[bytes]:
    """Yield installer bytes in chunks and close the file after streaming completes.

    Args:
        installer_path: Installer file to stream.

    Yields:
        Consecutive chunks of the installer file.
    """
    with installer_path.open("rb") as installer_file:
        while chunk := installer_file.read(1024 * 1024):
            yield chunk


@router.get("/installer", response_model=None)
async def download_installer(
    request: Request,
    client: Client = Depends(require_active_client),  # noqa: B008
) -> Response:
    """Stream the authenticated client's tier installer with its checksum.

    Args:
        request: Incoming HTTP request, used to record the download IP.
        client: Authenticated active client requesting the installer.

    Returns:
        A streamed installer response or a structured unavailable response.
    """
    try:
        installer_path = await get_installer_path(client.tier)
    except InstallerUnavailableError:
        return JSONResponse(
            status_code=503,
            content={"error": "installer_unavailable"},
        )

    checksum = _calculate_sha256(installer_path)
    client_ip = request.client.host if request.client is not None else "unknown"
    print(
        json.dumps(
            {
                "event": "installer_download",
                "client_slug": client.slug,
                "tier": client.tier.value,
                "timestamp": datetime.now(UTC).isoformat(),
                "ip": client_ip,
            },
            separators=(",", ":"),
        ),
        flush=True,
    )

    return StreamingResponse(
        _stream_file(installer_path),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="arystos-setup.msi"',
            "X-Checksum-SHA256": checksum,
        },
    )
