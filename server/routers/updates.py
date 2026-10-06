"""Application update API routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from server.auth.middleware import require_active_client
from server.registry.models import Client
from server.updates.manifest import ManifestUnavailableError
from server.updates.service import get_manifest

router = APIRouter(prefix="/api/v1/updates", tags=["updates"])


@router.get("/manifest", response_model=None)
async def fetch_manifest(
    client: Client = Depends(require_active_client),  # noqa: B008
) -> JSONResponse:
    """Return release metadata to an authenticated active client.

    Args:
        client: Authenticated active client requesting the manifest.

    Returns:
        The manifest JSON, or a structured 503 error when unavailable.
    """
    try:
        manifest = await get_manifest()
    except ManifestUnavailableError:
        return JSONResponse(
            status_code=503,
            content={"error": "manifest_unavailable"},
        )
    return JSONResponse(content=manifest.model_dump(mode="json"))
