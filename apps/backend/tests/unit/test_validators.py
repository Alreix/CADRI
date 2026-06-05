"""Unit tests for input validators."""

from __future__ import annotations

import pytest

from app.utils.exceptions import ValidationError
from app.utils.validators import validate_email, validate_password


def test_validate_email_normalizes_and_returns_lowercase():
    assert validate_email("  Admin.User@CADRI.Local  ") == "admin.user@cadri.local"


@pytest.mark.parametrize(
    "invalid_email",
    [None, "", "not-an-email", "missing-at-sign.local", "name@missing-tld"],
)
def test_validate_email_rejects_invalid_values(invalid_email):
    with pytest.raises(ValidationError):
        validate_email(invalid_email)


@pytest.mark.parametrize(
    "password, expected_message",
    [
        (None, "Password is required."),
        ("", "Password is required."),
        ("Short1", "Password must be at least 8 characters long."),
        ("alllowercase1", "Password must contain at least one uppercase letter."),
        ("ALLUPPERCASE1", "Password must contain at least one lowercase letter."),
        ("NoNumberHere", "Password must contain at least one number."),
    ],
)
def test_validate_password_rejects_policy_violations(password, expected_message):
    with pytest.raises(ValidationError, match=expected_message):
        validate_password(password)


def test_validate_password_returns_original_password_when_valid():
    password = "StrongPass1"

    assert validate_password(password) == password
