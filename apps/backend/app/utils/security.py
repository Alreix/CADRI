"""Password hashing helpers used across the authentication layer.

This module centralizes password hashing/verification so the rest of the
application does not need to know the hashing algorithm or configuration.
"""

from app.extensions import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password and return the encoded string.

    The project uses Flask-Bcrypt stored in `app.extensions.bcrypt`. The return
    value is a UTF-8 string that can be stored in the database.
    """

    return bcrypt.generate_password_hash(password).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    """Compare a plaintext password against a stored bcrypt hash.

    Returns True for a match, False otherwise.
    """

    return bcrypt.check_password_hash(password_hash, password)
