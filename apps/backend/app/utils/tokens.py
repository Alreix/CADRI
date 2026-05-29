"""Token utilities for generating and hashing short-lived tokens.

These helpers are used to create URL-safe tokens (for account activation and
password resets) and to produce a deterministic hash suitable for storage and
comparison. Keep hashing here so algorithm choices remain centralized.
"""

import hashlib
import secrets


def generate_raw_token(length: int = 32) -> str:
    """Return a URL-safe random token.

    The `length` parameter specifies the number of random bytes passed to
    `secrets.token_urlsafe`. The resulting string is safe to include in URLs.
    """

    return secrets.token_urlsafe(length)


def hash_token(raw_token: str) -> str:
    """Return a hex SHA3-256 digest of the provided token string.

    The hex digest is suitable for storing in the database and comparing using
    constant-time comparison functions when verifying tokens.
    """

    return hashlib.sha3_256(raw_token.encode("utf-8")).hexdigest()
