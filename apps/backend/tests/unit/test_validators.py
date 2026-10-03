"""Unit tests for validation helpers."""

import pytest

from app.utils.exceptions import ValidationError
from app.utils.validators import (
    parse_integer,
    parse_iso_datetime,
    validate_email,
    validate_password,
)


def test_validate_email_normalizes_email():
    assert validate_email("  USER@Example.COM  ") == "user@example.com"


@pytest.mark.parametrize("email", ["", "invalid", "missing-at.example.com"])
def test_validate_email_rejects_invalid_values(email):
    with pytest.raises(ValidationError):
        validate_email(email)


@pytest.mark.parametrize("password", ["StrongPass1!", "AnotherPass2!"])
def test_validate_password_accepts_valid_passwords(password):
    assert validate_password(password) == password


@pytest.mark.parametrize(
    "password",
    ["short", "lowercase1", "NOLOWERCASE1", "NoNumber", "StrongPass1"],
)
def test_validate_password_rejects_weak_passwords(password):
    with pytest.raises(ValidationError):
        validate_password(password)


@pytest.mark.parametrize("parser", [parse_integer, parse_iso_datetime])
@pytest.mark.parametrize("value", [None, [], {}, "invalid"])
def test_parsers_convert_expected_errors_to_validation_errors(parser, value):
    """Convert both invalid types and invalid strings into useful validation errors."""
    with pytest.raises(ValidationError, match="test_field") as caught:
        parser(value, "test_field")
    assert isinstance(caught.value.__cause__, (TypeError, ValueError))


@pytest.mark.parametrize("value", ["1", " 1 ", "+1", "01"])
def test_integer_parser_preserves_existing_valid_forms(value):
    """Preserve the integer string forms already accepted by the routes."""
    assert parse_integer(value, "page") == 1
