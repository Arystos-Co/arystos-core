"""Business logic for published application updates."""

from server.routers.schemas import ManifestResponse
from server.updates.manifest import load_manifest


async def get_manifest() -> ManifestResponse:
    """Return the latest validated release manifest.

    Returns:
        The latest release manifest.

    Raises:
        ManifestUnavailableError: If the manifest file is missing or malformed.
    """
    return await load_manifest()
