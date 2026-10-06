"""Installer delivery business logic."""

import json
from pathlib import Path

from server.config import RELEASES_DIR
from server.registry.models import Tier

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "releases" / "latest.json"


class InstallerUnavailableError(Exception):
    """Raised when an installer for a requested tier cannot be resolved."""


async def get_installer_path(tier: Tier) -> Path:
    """Resolve the tier's installer using the latest version in the release manifest.

    Args:
        tier: Client tier whose installer should be returned.

    Returns:
        The resolved installer file path.

    Raises:
        InstallerUnavailableError: If the manifest is unavailable or the installer is missing.
    """
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InstallerUnavailableError("release manifest is unavailable") from error

    if not isinstance(manifest, dict):
        raise InstallerUnavailableError("release manifest has an invalid shape")

    version = manifest.get("latest_version")
    if not isinstance(version, str) or not version or Path(version).name != version:
        raise InstallerUnavailableError("release manifest has no usable latest version")

    installer_path = RELEASES_DIR / f"arystos-{tier.value}-{version}.msi"
    if not installer_path.is_file():
        raise InstallerUnavailableError(f"installer is missing for tier {tier.value}")

    return installer_path
