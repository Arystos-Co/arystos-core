"""Tests for authentication token utilities."""

import re

from server.auth.token import extract_bearer, generate_token, hash_token, tokens_equal


def test_generate_token_returns_64_hex_chars() -> None:
    """Generated token should be 32 random bytes encoded as hexadecimal."""
    token = generate_token()

    assert len(token) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", token) is not None


def test_hash_token_is_deterministic() -> None:
    """Hashing the same token repeatedly should produce the same digest."""
    assert hash_token("client-secret") == hash_token("client-secret")


def test_hash_token_different_for_different_inputs() -> None:
    """Different raw tokens should produce different digests."""
    assert hash_token("first-secret") != hash_token("second-secret")


def test_tokens_equal_returns_true_for_equal() -> None:
    """Equal tokens should compare as equal."""
    assert tokens_equal("same-token", "same-token")


def test_tokens_equal_returns_false_for_unequal() -> None:
    """Different tokens should compare as unequal."""
    assert not tokens_equal("first-token", "second-token")


def test_extract_bearer_valid() -> None:
    """A valid Bearer authorization header should return its token."""
    assert extract_bearer("Bearer token-value") == "token-value"


def test_extract_bearer_missing() -> None:
    """A missing authorization header should return None."""
    assert extract_bearer(None) is None


def test_extract_bearer_wrong_scheme() -> None:
    """A non-Bearer authorization scheme should return None."""
    assert extract_bearer("Basic credentials") is None


def test_extract_bearer_empty_token() -> None:
    """A Bearer scheme without a token should return None."""
    assert extract_bearer("Bearer ") is None
