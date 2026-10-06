"""Unit tests for strict semantic-version parsing and comparison."""

import pytest

from server.updates.version import compare_semver, parse_semver


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.2.3", (1, 2, 3)),
        ("0.0.0", (0, 0, 0)),
    ],
)
def test_parse_semver_valid(version: str, expected: tuple[int, int, int]) -> None:
    """Parse valid three-part semantic versions."""
    assert parse_semver(version) == expected


@pytest.mark.parametrize(
    "version",
    [
        "1.2",
        "1.2.3.4",
        "v1.2.3",
        "1.2.x",
        "1.02.3",
        "01.2.3",
        "1.2.03",
        "-1.2.3",
    ],
)
def test_parse_semver_invalid(version: str) -> None:
    """Reject malformed versions and versions with leading zeros."""
    with pytest.raises(ValueError):
        parse_semver(version)


def test_compare_semver_major() -> None:
    """Compare versions by their major component first."""
    assert compare_semver("2.0.0", "1.9.9") == 1
    assert compare_semver("1.9.9", "2.0.0") == -1


def test_compare_semver_minor() -> None:
    """Compare versions by their minor component when majors match."""
    assert compare_semver("1.3.0", "1.2.9") == 1
    assert compare_semver("1.2.9", "1.3.0") == -1


def test_compare_semver_patch() -> None:
    """Compare versions by their patch component when earlier parts match."""
    assert compare_semver("1.2.4", "1.2.3") == 1
    assert compare_semver("1.2.3", "1.2.4") == -1


def test_compare_semver_equal() -> None:
    """Return zero when both semantic versions are identical."""
    assert compare_semver("1.2.3", "1.2.3") == 0
