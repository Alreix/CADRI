"""Integration tests for the CADRI authentication service."""

from __future__ import annotations

import pytest
from unittest.mock import patch

from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.repositories.account_activation_token_repository import (
    AccountActivationTokenRepository,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.exceptions import AuthenticationError
from app.utils.tokens import hash_token


def test_login_returns_session_payload_and_creates_refresh_token(admin_user):
    result = AuthService.login(admin_user.email, "AdminPass1")

    assert result["message"] == "Login successful"
    assert result["access_token"]
    assert result["refresh_token"]
    assert result["user"]["email"] == admin_user.email
    assert result["user"]["role"] == "admin"
    assert result["user"]["service"]["name"] == "roads"

    stored_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)
    assert stored_token is not None
    assert stored_token.verify_token(result["refresh_token"])
    assert not stored_token.is_revoked()


def test_login_rejects_invalid_password(admin_user):
    with pytest.raises(AuthenticationError):
        AuthService.login(admin_user.email, "WrongPass1")


def test_logout_revokes_refresh_token(admin_user):
    token, raw_token = RefreshToken.create_for_user(admin_user.id)
    RefreshTokenRepository.create(token)

    result = AuthService.logout(raw_token)

    assert result["message"] == "Logout successful"
    assert RefreshTokenRepository.get_by_token_hash(hash_token(raw_token)).is_revoked()


def test_change_password_updates_user_password(agent_user):
    result = AuthService.change_password(agent_user.id, "AgentPass1", "NewAgentPass1")

    assert result["message"] == "Password changed successfully"
    assert UserRepository.get_by_id(agent_user.id).check_password("NewAgentPass1")


def test_request_password_reset_creates_token_and_sends_email(agent_user):
    sent_payload = {}

    def fake_send_password_reset_email(user_email, raw_token):
        sent_payload["user_email"] = user_email
        sent_payload["raw_token"] = raw_token

    with patch.object(EmailService, "send_password_reset_email", side_effect=fake_send_password_reset_email):
        result = AuthService.request_password_reset(agent_user.email)

    assert result["message"] == "If the account exists, a reset email has been sent"
    assert sent_payload["user_email"] == agent_user.email
    assert sent_payload["raw_token"]

    stored_token = PasswordResetTokenRepository.get_latest_for_user(agent_user.id)
    assert stored_token is not None
    assert stored_token.verify_token(sent_payload["raw_token"])


def test_refresh_session_rotates_refresh_token(admin_user):
    token, raw_token = RefreshToken.create_for_user(admin_user.id)
    RefreshTokenRepository.create(token)

    result = AuthService.refresh_session(raw_token)

    assert result["access_token"]
    assert result["refresh_token"]


def test_activate_account_marks_user_active_and_consumes_token(user_factory):
    user = user_factory(
        email="pending@cadri.local",
        role_name="agent",
        password=None,
        is_active=False,
    )

    token, raw_token = AccountActivationToken.create_for_user(user.id)
    AccountActivationTokenRepository.create(token)

    result = AuthService.activate_account(raw_token, "NewPass1")

    assert result["message"] == "Account activated successfully"
    assert UserRepository.get_by_id(user.id).is_active


def test_reset_password_marks_token_used_and_updates_password(user_factory):
    user = user_factory(
        email="reset-flow@cadri.local",
        role_name="agent",
        password="OldPass1",
        is_active=True,
    )

    token, raw_token = PasswordResetToken.create_for_user(user.id)
    PasswordResetTokenRepository.create(token)

    result = AuthService.reset_password(raw_token, "NewPass1")

    assert result["message"] == "Password reset successfully"
    assert UserRepository.get_by_id(user.id).check_password("NewPass1")
