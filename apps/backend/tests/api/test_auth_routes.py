"""API tests for authentication routes."""

from app.extensions import db
from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from tests.helpers.auth_helpers import auth_headers


def test_auth_health_is_public(client):
    response = client.get("/auth/health")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Auth routes working"


def test_login_success_returns_access_token_and_refresh_cookie(client, admin_user):
    response = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "StrongPass1"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Login successful"
    assert data["access_token"]
    assert data["user"]["email"] == admin_user.email
    assert "refresh_token=" in response.headers.get("Set-Cookie", "")


def test_login_rejects_inactive_user(client, user_factory, roles_services):
    inactive_user = user_factory(
        email="inactive@cadri.test",
        role=roles_services["agent_role"],
        is_active=False,
    )

    response = client.post(
        "/auth/login",
        json={"email": inactive_user.email, "password": "StrongPass1"},
    )

    assert response.status_code == 403


def test_refresh_rotates_refresh_token(client, admin_user):
    login_response = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "StrongPass1"},
    )
    assert login_response.status_code == 200

    refresh_response = client.post("/auth/refresh")

    assert refresh_response.status_code == 200
    assert refresh_response.get_json()["access_token"]
    assert "refresh_token=" in refresh_response.headers.get("Set-Cookie", "")


def test_logout_revokes_refresh_token(client, admin_user):
    login_response = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "StrongPass1"},
    )
    assert login_response.status_code == 200

    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 200
    assert logout_response.get_json()["message"] == "Logout successful"


def test_activate_account_with_valid_token(client, user_factory, roles_services):
    user = user_factory(
        email="activate@cadri.test",
        role=roles_services["agent_role"],
        is_active=False,
    )
    token, raw_token = AccountActivationToken.create_for_user(user.id)
    db.session.add(token)
    db.session.commit()

    response = client.post(
        "/auth/activate-account",
        json={"token": raw_token, "password": "NewStrongPass1"},
    )

    assert response.status_code == 200
    db.session.refresh(user)
    db.session.refresh(token)
    assert user.is_active is True
    assert user.check_password("NewStrongPass1") is True
    assert token.used_at is not None


def test_forgot_password_creates_token_for_active_user(client, admin_user, monkeypatch):
    sent_emails = []

    def fake_send_password_reset_email(email, raw_token):
        sent_emails.append((email, raw_token))

    monkeypatch.setattr(
        EmailService,
        "send_password_reset_email",
        staticmethod(fake_send_password_reset_email),
    )

    response = client.post("/auth/forgot-password", json={"email": admin_user.email})

    assert response.status_code == 200
    assert sent_emails
    assert PasswordResetToken.query.count() == 1


def test_reset_password_with_valid_token(client, admin_user):
    token, raw_token = PasswordResetToken.create_for_user(admin_user.id)
    db.session.add(token)
    db.session.commit()

    response = client.post(
        "/auth/reset-password",
        json={"token": raw_token, "password": "ResetStrongPass1"},
    )

    assert response.status_code == 200

    refreshed_user = UserRepository.get_by_id(admin_user.id)
    db.session.refresh(token)

    assert refreshed_user.check_password("ResetStrongPass1") is True
    assert token.used_at is not None


def test_change_password_revokes_existing_refresh_token(client, admin_user, admin_token):
    login_response = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "StrongPass1"},
    )
    assert login_response.status_code == 200

    response = client.patch(
        "/auth/change-password",
        headers=auth_headers(admin_token),
        json={"current_password": "StrongPass1", "new_password": "ChangedPass1"},
    )

    assert response.status_code == 200

    refreshed_user = UserRepository.get_by_id(admin_user.id)
    stored_tokens = RefreshToken.query.filter_by(user_id=admin_user.id).all()

    assert refreshed_user.check_password("ChangedPass1") is True
    assert stored_tokens
    assert all(token.is_revoked() for token in stored_tokens) is True
