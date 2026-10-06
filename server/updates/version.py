"""Semantic-version parsing and comparison helpers."""

import re
from typing import Final

SEMVER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
)


def parse_semver(s: str) -> tuple[int, int, int]:
    """Parse a strict major.minor.patch version into three integers.

    Args:
        s: Semantic version string with three non-negative integer components.

    Returns:
        The major, minor, and patch components as integers.

    Raises:
        ValueError: If the input is not a three-part version without leading zeros.
    """
    if not isinstance(s, str):
        raise ValueError("semantic version must be a string")

    match = SEMVER_PATTERN.fullmatch(s)
    if match is None:
        raise ValueError(f"invalid semantic version: {s!r}")

    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def compare_semver(a: str, b: str) -> int:
    """Compare two strict major.minor.patch versions.

    Args:
        a: First semantic version.
        b: Second semantic version.

    Returns:
        -1 when a is older, 0 when versions are equal, and 1 when a is newer.

    Raises:
        ValueError: If either version is malformed.
    """
    first_version = parse_semver(a)
    second_version = parse_semver(b)
    return (first_version > second_version) - (first_version < second_version)
