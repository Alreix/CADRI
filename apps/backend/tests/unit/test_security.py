"""Unit tests for password hashing helpers."""

from __future__ import annotations

from app.utils.security import check_password, hash_password


def test_hash_password_generates_verifiable_hash(app):
    password = "AdminPass1"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert check_password(password, hashed_password)
    assert not check_password("WrongPass1", hashed_password)
