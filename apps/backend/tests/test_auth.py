from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.repositories.account_activation_token_repository import (
    AccountActivationTokenRepository,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.services.email_service import EmailService


def test_auth_health_route(client):
    response = client.get("/auth/health")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Auth routes working"


def test_login_success(client, admin_user):
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@cadri.local",
            "password": "StrongPass1",
        },
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["message"] == "Login successful"
    assert "access_token" in data
    assert "user" in data
    assert "Set-Cookie" in response.headers


def test_login_fails_with_wrong_password(client, admin_user):
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@cadri.local",
            "password": "WrongPass1",
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid credentials."


def test_login_fails_for_inactive_user(client, inactive_user):
    response = client.post(
        "/auth/login",
        json={
            "email": "inactive@cadri.local",
            "password": "StrongPass1",
        },
    )

    assert response.status_code == 403


def test_activate_account_success(client, inactive_user):
    token, raw_token = AccountActivationToken.create_for_user(inactive_user.id, 24)
    AccountActivationTokenRepository.create(token)

    response = client.post(
        "/auth/activate-account",
        json={
            "token": raw_token,
            "password": "StrongPass1",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Account activated successfully"


def test_forgot_password_returns_generic_message(client, admin_user, monkeypatch):
    def fake_send_password_reset_email(user_email, raw_token):
        return None

    monkeypatch.setattr(
        EmailService,
        "send_password_reset_email",
        fake_send_password_reset_email,
    )

    response = client.post(
        "/auth/forgot-password",
        json={"email": "admin@cadri.local"},
    )

    assert response.status_code == 200
    assert "message" in response.get_json()


def test_reset_password_success(client, admin_user):
    token, raw_token = PasswordResetToken.create_for_user(admin_user.id, 2)
    PasswordResetTokenRepository.create(token)

    response = client.post(
        "/auth/reset-password",
        json={
            "token": raw_token,
            "password": "NewStrongPass1",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Password reset successfully"


def test_change_password_success(client, admin_user, admin_access_token):
    response = client.patch(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json={
            "current_password": "StrongPass1",
            "new_password": "NewStrongPass1",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Password changed successfully"