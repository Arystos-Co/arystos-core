"""Load and cache the latest published release manifest."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from time import monotonic
from typing import Final

from pydantic import ValidationError

from server.routers.schemas import ManifestResponse

MANIFEST_PATH: Final[Path] = Path(__file__).resolve().parents[1] / "releases" / "latest.json"
MANIFEST_CACHE_TTL_SECONDS: Final[int] = 60


class ManifestUnavailableError(Exception):
    """Raised when the release manifest is missing or malformed."""


@dataclass(frozen=True)
class _ManifestCacheEntry:
    """A validated manifest and the time at which its cached value expires."""

    path: Path
    response: ManifestResponse
    expires_at: float


_cache_lock = Lock()
_cached_manifest: _ManifestCacheEntry | None = None


def _read_manifest(manifest_path: Path) -> ManifestResponse:
    """Read a manifest file and validate its contents against the API schema.

    Args:
        manifest_path: Path to the JSON manifest file.

    Returns:
        The validated manifest response.

    Raises:
        ManifestUnavailableError: If the file cannot be read or validated.
    """
    try:
        manifest_contents = manifest_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ManifestUnavailableError("release manifest cannot be read") from error

    try:
        return ManifestResponse.model_validate_json(manifest_contents)
    except ValidationError as error:
        raise ManifestUnavailableError("release manifest is malformed") from error


async def load_manifest() -> ManifestResponse:
    """Load the latest release manifest, reusing a valid result for 60 seconds.

    Returns:
        The validated manifest response.

    Raises:
        ManifestUnavailableError: If the manifest file is missing or malformed.
    """
    global _cached_manifest

    manifest_path = MANIFEST_PATH
    with _cache_lock:
        cache_entry = _cached_manifest
        if (
            cache_entry is not None
            and cache_entry.path == manifest_path
            and monotonic() < cache_entry.expires_at
        ):
            return cache_entry.response

    manifest = await asyncio.to_thread(_read_manifest, manifest_path)
    with _cache_lock:
        cache_entry = _cached_manifest
        # Another request may have populated the cache while this file was read.
        if (
            cache_entry is not None
            and cache_entry.path == manifest_path
            and monotonic() < cache_entry.expires_at
        ):
            return cache_entry.response
        _cached_manifest = _ManifestCacheEntry(
            path=manifest_path,
            response=manifest,
            expires_at=monotonic() + MANIFEST_CACHE_TTL_SECONDS,
        )
    return manifest
