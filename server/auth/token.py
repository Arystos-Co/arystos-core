"""Token generation, hashing, comparison, and Authorization header parsing."""

import hashlib
import secrets


def generate_token() -> str:
    """Return a 64-char hex string from 32 CSPRNG bytes."""
    return secrets.token_hex(32)


def hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of a raw token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def tokens_equal(a: str, b: str) -> bool:
    """Constant-time comparison. Never use == on tokens."""
    return secrets.compare_digest(a, b)


def extract_bearer(authorization_header: str | None) -> str | None:
    """
    Parse '******' from an Authorization header.
    Return None if header is missing, malformed, or scheme is not Bearer.
    """
    if authorization_header is None:
        return None

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]
