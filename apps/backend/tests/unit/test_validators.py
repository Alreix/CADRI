"""Unit tests for validation helpers."""

import pytest

from app.utils.exceptions import ValidationError
from app.utils.validators import validate_email, validate_password


def test_validate_email_normalizes_email():
    assert validate_email("  USER@Example.COM  ") == "user@example.com"


@pytest.mark.parametrize("email", ["", "invalid", "missing-at.example.com"])
def test_validate_email_rejects_invalid_values(email):
    with pytest.raises(ValidationError):
        validate_email(email)


@pytest.mark.parametrize("password", ["StrongPass1", "AnotherPass2"])
def test_validate_password_accepts_valid_passwords(password):
    assert validate_password(password) == password


@pytest.mark.parametrize("password", ["short", "lowercase1", "NOLOWERCASE1", "NoNumber"])
def test_validate_password_rejects_weak_passwords(password):
    with pytest.raises(ValidationError):
        validate_password(password)
