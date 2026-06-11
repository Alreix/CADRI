"""Integration tests for AuthService."""

from app.models.password_reset_token import PasswordResetToken
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService


def test_auth_service_login_creates_refresh_token(admin_user):
    result = AuthService.login(admin_user.email, "StrongPass1")

    assert result["access_token"]
    assert result["refresh_token"]
    assert result["user"]["email"] == admin_user.email

    stored_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)

    assert stored_token is not None
    assert stored_token.user_id == admin_user.id
    assert stored_token.is_revoked() is False


def test_auth_service_request_password_reset_creates_token(admin_user, monkeypatch):
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

