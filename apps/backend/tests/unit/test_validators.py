"""Unit tests for input validators."""

import pytest

from app.utils.exceptions import ValidationError
from app.utils.validators import validate_email, validate_password


def test_validate_email_returns_normalized_email():
    assert validate_email(" TEST@Example.com ") == "test@example.com"


def test_validate_email_raises_error_for_invalid_email():
    with pytest.raises(ValidationError):
        validate_email("not-an-email")


def test_validate_email_raises_error_for_empty_value():
    with pytest.raises(ValidationError):
        validate_email("")


def test_validate_password_accepts_valid_password():
    assert validate_password("StrongPass1") == "StrongPass1"


def test_validate_password_rejects_short_password():
    with pytest.raises(ValidationError):
        validate_password("Aa1")


def test_validate_password_rejects_without_uppercase():
    with pytest.raises(ValidationError):
        validate_password("strongpass1")


def test_validate_password_rejects_without_lowercase():
    with pytest.raises(ValidationError):
        validate_password("STRONGPASS1")


def test_validate_password_rejects_without_number():
    with pytest.raises(ValidationError):
        validate_password("StrongPass")
