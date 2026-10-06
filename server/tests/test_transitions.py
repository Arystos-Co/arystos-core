"""Unit tests for the client status transition rules."""

from datetime import UTC, datetime, timedelta

from server.access.service import is_valid_transition
from server.registry.models import Status


def test_active_to_suspended_valid() -> None:
    """Allow an active client to be suspended."""
    assert is_valid_transition(Status.ACTIVE, Status.SUSPENDED, None)


def test_active_to_offboarded_valid() -> None:
    """Allow an active client to be offboarded."""
    assert is_valid_transition(Status.ACTIVE, Status.OFFBOARDED, None)


def test_suspended_to_active_valid() -> None:
    """Allow a suspended client to be reactivated."""
    assert is_valid_transition(Status.SUSPENDED, Status.ACTIVE, None)


def test_suspended_to_offboarded_valid() -> None:
    """Allow a suspended client to be offboarded."""
    assert is_valid_transition(Status.SUSPENDED, Status.OFFBOARDED, None)


def test_offboarded_to_active_within_retention_valid() -> None:
    """Allow reactivation when offboarding occurred within the retention window."""
    offboarded_at = datetime.now(UTC) - timedelta(days=30)

    assert is_valid_transition(Status.OFFBOARDED, Status.ACTIVE, offboarded_at)


def test_offboarded_to_active_past_retention_invalid() -> None:
    """Reject reactivation when offboarding occurred outside the retention window."""
    offboarded_at = datetime.now(UTC) - timedelta(days=91)

    assert not is_valid_transition(Status.OFFBOARDED, Status.ACTIVE, offboarded_at)


def test_offboarded_to_suspended_invalid() -> None:
    """Reject a direct transition from offboarded to suspended."""
    assert not is_valid_transition(Status.OFFBOARDED, Status.SUSPENDED, None)


def test_offboarded_to_offboarded_invalid() -> None:
    """Reject an offboarding transition when already offboarded."""
    assert not is_valid_transition(Status.OFFBOARDED, Status.OFFBOARDED, None)
