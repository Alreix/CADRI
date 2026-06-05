"""Unit tests for password hashing helpers."""

from app.utils.security import check_password, hash_password


def test_hash_password_returns_string():
    password_hash = hash_password("StrongPass1")
    assert isinstance(password_hash, str)
    assert password_hash != "StrongPass1"


def test_check_password_returns_true_for_valid_password():
    password_hash = hash_password("StrongPass1")
    assert check_password("StrongPass1", password_hash) is True


def test_check_password_returns_false_for_invalid_password():
    password_hash = hash_password("StrongPass1")
    assert check_password("WrongPass1", password_hash) is False
