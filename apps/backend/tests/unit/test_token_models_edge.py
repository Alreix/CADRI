"""Additional unit tests for token model edge cases."""

from datetime import datetime, timedelta, timezone

from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken


def test_account_activation_token_expired_and_used_states(admin_user):
    token, raw_token = AccountActivationToken.create_for_user(
        admin_user.id,
        expires_in_hours=-1,
    )

    assert token.verify_token(raw_token) is True
    assert token.is_expired() is True
    assert token.is_used() is False

    token.mark_as_used()

    assert token.is_used() is True


def test_password_reset_token_expired_and_used_states(admin_user):
    token, raw_token = PasswordResetToken.create_for_user(
        admin_user.id,
        expires_in_hours=-1,
    )

    assert token.verify_token(raw_token) is True
    assert token.is_expired() is True
    assert token.is_used() is False

    token.mark_as_used()

    assert token.is_used() is True


def test_refresh_token_invalid_when_expired_revoked_or_replaced(admin_user):
    expired_token, raw_token = RefreshToken.create_for_user(
        admin_user.id,
        expires_in_days=-1,
    )

    assert expired_token.verify_token(raw_token) is True
    assert expired_token.is_expired() is True
    assert expired_token.is_valid() is False

    valid_token, new_raw_token = RefreshToken.create_for_user(admin_user.id)
    assert valid_token.is_valid() is True

    valid_token.rotate(new_raw_token)

    assert valid_token.is_revoked() is True
    assert valid_token.is_replaced() is True
    assert valid_token.is_valid() is False


def test_refresh_token_can_be_revoked(admin_user):
    token, _ = RefreshToken.create_for_user(admin_user.id)

    assert token.is_revoked() is False

    token.revoke()

    assert token.is_revoked() is True
    assert token.is_valid() is False
