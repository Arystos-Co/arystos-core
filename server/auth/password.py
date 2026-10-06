"""Password hashing helpers for ARYSTOS user accounts."""

import bcrypt


def hash_password(plain: str) -> str:
    """Hash a plaintext password using bcrypt with a cost factor of 12.

    Args:
        plain: Plaintext password to hash.

    Returns:
        bcrypt hash string suitable for storage.
    """
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Validate a plaintext password against a bcrypt hash.

    Args:
        plain: Plaintext password to verify.
        hashed: Stored bcrypt hash.

    Returns:
        True when the supplied plaintext value matches the stored hash.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
