"""Integration tests for AuthService."""

from app.extensions import db
from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.exceptions import AuthenticationError


def test_login_returns_session_payload_and_creates_refresh_token(admin_user):
    result = AuthService.login(admin_user.email, "StrongPass1")

    assert result["access_token"]
    assert result["refresh_token"]
    assert result["user"]["email"] == admin_user.email

    stored_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)

    assert stored_token is not None
    assert stored_token.user_id == admin_user.id
    assert stored_token.is_revoked() is False


def test_login_rejects_invalid_password(admin_user):
    try:
        AuthService.login(admin_user.email, "WrongPassword1")
        assert False
    except AuthenticationError as error:
        assert error.status_code == 401


def test_logout_revokes_refresh_token(admin_user):
    login_result = AuthService.login(admin_user.email, "StrongPass1")

    stored_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)

    assert stored_token is not None
    assert stored_token.is_revoked() is False

    result = AuthService.logout(login_result["refresh_token"])

    assert result["message"] == "Logout successful"

    db.session.refresh(stored_token)
    assert stored_token.is_revoked() is True


def test_change_password_updates_user_password(agent_user):
    result = AuthService.change_password(
        agent_user.id,
        "StrongPass1",
        "NewAgentPass1!",
    )

    assert result["message"] == "Password changed successfully"

    user = UserRepository.get_by_id(agent_user.id)

    assert user.check_password("NewAgentPass1!") is True


def test_request_password_reset_creates_token_and_sends_email(admin_user, monkeypatch):
    sent_emails = []

    def fake_send_password_reset_email(email, raw_token):
        sent_emails.append((email, raw_token))

    monkeypatch.setattr(
        EmailService,
        "send_password_reset_email",
        staticmethod(fake_send_password_reset_email),
    )

    result = AuthService.request_password_reset(admin_user.email)

    assert result["message"] == "If the account exists, a reset email has been sent"
    assert PasswordResetToken.query.count() == 1
    assert sent_emails
    assert sent_emails[0][0] == admin_user.email
    assert sent_emails[0][1]


def test_refresh_session_rotates_refresh_token(admin_user):
    login_result = AuthService.login(admin_user.email, "StrongPass1")

    first_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)

    assert first_token is not None
    assert first_token.is_revoked() is False

    result = AuthService.refresh_session(login_result["refresh_token"])

    assert result["access_token"]
    assert result["refresh_token"]

    db.session.refresh(first_token)
    assert first_token.is_revoked() is True

    second_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)

    assert second_token is not None
    assert second_token.id != first_token.id
    assert second_token.is_revoked() is False


def test_activate_account_marks_user_active_and_consumes_token(inactive_user):
    user = UserRepository.get_by_id(inactive_user.id)

    token, raw_token = AccountActivationToken.create_for_user(user.id)
    db.session.add(token)
    db.session.commit()

    result = AuthService.activate_account(raw_token, "ActivatedPass1!")

    assert result["message"] == "Account activated successfully"

    db.session.refresh(user)
    db.session.refresh(token)

    assert user.is_active is True
    assert user.check_password("ActivatedPass1!") is True
    assert token.used_at is not None


def test_reset_password_marks_token_used_and_updates_password(admin_user):
    user = UserRepository.get_by_id(admin_user.id)

    token, raw_token = PasswordResetToken.create_for_user(user.id)
    db.session.add(token)
    db.session.commit()

    result = AuthService.reset_password(raw_token, "ResetStrongPass1!")

    assert result["message"] == "Password reset successfully"

    db.session.refresh(user)
    db.session.refresh(token)

    assert user.check_password("ResetStrongPass1!") is True
    assert token.used_at is not None
