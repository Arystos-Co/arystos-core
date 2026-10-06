"""Unit tests for client provisioning validation."""

import pytest

from server.registry.service import ValidationError, validate_lengths, validate_slug


def test_validate_slug_accepts_valid() -> None:
    """Accept a lowercase slug with valid length and characters."""
    validate_slug("pearlsky-2")


def test_validate_slug_rejects_uppercase() -> None:
    """Reject uppercase characters in a slug."""
    with pytest.raises(ValidationError):
        validate_slug("Pearlsky")


def test_validate_slug_rejects_leading_hyphen() -> None:
    """Reject a slug beginning with a hyphen."""
    with pytest.raises(ValidationError):
        validate_slug("-pearlsky")


def test_validate_slug_rejects_trailing_hyphen() -> None:
    """Reject a slug ending with a hyphen."""
    with pytest.raises(ValidationError):
        validate_slug("pearlsky-")


def test_validate_slug_rejects_too_short() -> None:
    """Reject a slug shorter than three characters."""
    with pytest.raises(ValidationError):
        validate_slug("ab")


def test_validate_slug_rejects_too_long() -> None:
    """Reject a slug longer than 63 characters."""
    with pytest.raises(ValidationError):
        validate_slug(f"a{'b' * 62}c")


def test_validate_lengths_accepts_valid() -> None:
    """Accept values at or below every configured maximum length."""
    validate_lengths("PearlSky Guesthouse", "A. Contact", "+27123456789")


def test_validate_lengths_rejects_long_business_name() -> None:
    """Reject a business name longer than 255 characters."""
    with pytest.raises(ValidationError):
        validate_lengths("B" * 256, None, None)
