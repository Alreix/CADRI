"""Additional API tests for authentication error and edge cases."""

from app.extensions import db
from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.repositories.refresh_token_repository import RefreshTokenRepository
from tests.helpers.auth_helpers import auth_headers


def test_login_rejects_wrong_password(client, admin_user):
    response = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "WrongPass1"},
    )

    assert response.status_code == 401


def test_refresh_without_cookie_is_rejected(client):
    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_logout_without_cookie_is_rejected(client):
    response = client.post("/auth/logout")

    assert response.status_code == 401


def test_activate_account_with_unknown_token_returns_404(client):
    response = client.post(
        "/auth/activate-account",
        json={"token": "unknown-token", "password": "NewStrongPass1!"},
    )

    assert response.status_code == 404


def test_activate_account_with_used_token_returns_410(client, inactive_user):
    token, raw_token = AccountActivationToken.create_for_user(inactive_user.id)
    token.mark_as_used()
    db.session.add(token)
    db.session.commit()

    response = client.post(
        "/auth/activate-account",
        json={"token": raw_token, "password": "NewStrongPass1!"},
    )

    assert response.status_code == 410


def test_forgot_password_for_inactive_user_does_not_create_token(client, inactive_user):
    response = client.post(
        "/auth/forgot-password",
        json={"email": inactive_user.email},
    )

    assert response.status_code == 200
    assert PasswordResetToken.query.count() == 0


def test_reset_password_with_unknown_token_returns_404(client):
    response = client.post(
        "/auth/reset-password",
        json={"token": "unknown-token", "password": "ResetStrongPass1!"},
    )

    assert response.status_code == 404


def test_reset_password_with_used_token_returns_410(client, admin_user):
    token, raw_token = PasswordResetToken.create_for_user(admin_user.id)
    token.mark_as_used()
    db.session.add(token)
    db.session.commit()

    response = client.post(
        "/auth/reset-password",
        json={"token": raw_token, "password": "ResetStrongPass1!"},
    )

    assert response.status_code == 410


def test_change_password_with_wrong_current_password_is_rejected(
    client,
    admin_token,
):
    response = client.patch(
        "/auth/change-password",
        headers=auth_headers(admin_token),
        json={
            "current_password": "WrongPass1",
            "new_password": "NewStrongPass1!",
        },
    )

    assert response.status_code == 403


def test_change_password_with_weak_new_password_is_rejected(
    client,
    admin_token,
):
    response = client.patch(
        "/auth/change-password",
        headers=auth_headers(admin_token),
        json={
            "current_password": "StrongPass1",
            "new_password": "weak",
        },
    )

    assert response.status_code == 400


def test_login_revokes_previous_refresh_token(client, admin_user):
    first_login = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "StrongPass1"},
    )
    assert first_login.status_code == 200
    first_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)
    assert first_token is not None

    second_login = client.post(
        "/auth/login",
        json={"email": admin_user.email, "password": "StrongPass1"},
    )
    assert second_login.status_code == 200

    db.session.refresh(first_token)
    assert first_token.is_revoked() is True
