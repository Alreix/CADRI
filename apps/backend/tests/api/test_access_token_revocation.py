"""Security regression tests for access-token revocation and invalidation."""

from datetime import datetime, timedelta, timezone

import pytest
from flask_jwt_extended import create_access_token, decode_token

from app.extensions import db
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.token_blocklist import TokenBlocklist
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from tests.helpers.auth_helpers import auth_headers


def _login(client, user, password="StrongPass1"):
    """Log in through the public API and return its decoded JSON payload."""

    response = client.post(
        "/auth/login", json={"email": user.email, "password": password}
    )
    assert response.status_code == 200
    return response.get_json()


def test_logout_blocklists_access_jti_and_revokes_refresh_token(client, admin_user):
    """Logout must terminate both credentials without persisting raw values."""

    login = _login(client, admin_user)
    access_token = login["access_token"]
    payload = decode_token(access_token)

    before_logout = client.get("/me", headers=auth_headers(access_token))
    logout = client.post("/auth/logout", headers=auth_headers(access_token))

    assert before_logout.status_code == 200
    assert logout.status_code == 200
    assert "refresh_token=;" in logout.headers.get("Set-Cookie", "")

    blocked = TokenBlocklist.query.filter_by(jti=payload["jti"]).one()
    refresh_tokens = RefreshToken.query.filter_by(user_id=admin_user.id).all()
    assert blocked.token_type == "access"
    assert blocked.user_id == admin_user.id
    assert access_token not in blocked.jti
    assert all(token.is_revoked() for token in refresh_tokens)
    assert client.get("/me", headers=auth_headers(access_token)).status_code == 401
    assert client.post("/auth/refresh").status_code == 401


def test_logout_is_idempotent_and_does_not_revoke_another_access_token(
    client, admin_user
):
    """Repeated logout must not violate JTI uniqueness or affect fresh JWTs."""

    first_login = _login(client, admin_user)
    first_access = first_login["access_token"]
    assert client.post("/auth/logout", headers=auth_headers(first_access)).status_code == 200
    assert client.post("/auth/logout", headers=auth_headers(first_access)).status_code == 200
    assert TokenBlocklist.query.count() == 1

    second_login = _login(client, admin_user)
    assert client.get(
        "/me", headers=auth_headers(second_login["access_token"])
    ).status_code == 200


def test_logout_without_access_token_still_terminates_refresh_session(
    client, admin_user
):
    """A missing access JWT must not trap an otherwise revocable session."""

    _login(client, admin_user)
    stored_token = RefreshTokenRepository.get_latest_for_user(admin_user.id)

    response = client.post("/auth/logout")

    assert response.status_code == 200
    db.session.refresh(stored_token)
    assert stored_token.is_revoked()


def test_logout_with_expired_access_token_still_revokes_both_credentials(
    app, client, admin_user
):
    """Logout accepts signed expired JWT metadata while ending the refresh session."""

    _login(client, admin_user)
    with app.app_context():
        expired_access = create_access_token(
            identity=str(admin_user.id), expires_delta=timedelta(seconds=-1)
        )
        payload = decode_token(expired_access, allow_expired=True)

    response = client.post("/auth/logout", headers=auth_headers(expired_access))

    assert response.status_code == 200
    assert TokenBlocklist.query.filter_by(jti=payload["jti"]).one_or_none() is not None
    assert client.post("/auth/refresh").status_code == 401


def test_password_change_invalidates_old_access_and_refresh_tokens(
    client, admin_user
):
    """Changing a password globally invalidates credentials issued beforehand."""

    login = _login(client, admin_user)
    old_access = login["access_token"]
    response = client.patch(
        "/auth/change-password",
        headers=auth_headers(old_access),
        json={
            "current_password": "StrongPass1",
            "new_password": "ChangedPass1!",
        },
    )

    assert response.status_code == 200
    assert admin_user.tokens_valid_after is not None
    assert client.get("/me", headers=auth_headers(old_access)).status_code == 401
    assert client.post("/auth/refresh").status_code == 401

    new_login = _login(client, admin_user, "ChangedPass1!")
    assert client.get(
        "/me", headers=auth_headers(new_login["access_token"])
    ).status_code == 200


def test_password_reset_invalidates_old_access_and_refresh_tokens(
    client, admin_user
):
    """A successful one-time reset globally invalidates existing sessions."""

    login = _login(client, admin_user)
    old_access = login["access_token"]
    token, raw_token = PasswordResetToken.create_for_user(admin_user.id)
    db.session.add(token)
    db.session.commit()

    response = client.post(
        "/auth/reset-password",
        json={"token": raw_token, "password": "ResetStrongPass1!"},
    )

    assert response.status_code == 200
    assert token.is_used()
    assert client.get("/me", headers=auth_headers(old_access)).status_code == 401
    assert client.post("/auth/refresh").status_code == 401


def test_tokens_valid_after_handles_before_after_and_null(app, client, admin_user):
    """The blocklist callback compares numeric JWT iat values deterministically."""

    now = datetime.now(timezone.utc).timestamp()
    with app.app_context():
        old_access = create_access_token(
            identity=str(admin_user.id),
            additional_claims={"iat": now - 10},
        )
        new_access = create_access_token(
            identity=str(admin_user.id),
            additional_claims={"iat": now},
        )

    admin_user.tokens_valid_after = datetime.fromtimestamp(now - 5, tz=timezone.utc)
    db.session.commit()
    assert client.get("/me", headers=auth_headers(old_access)).status_code == 401
    assert client.get("/me", headers=auth_headers(new_access)).status_code == 200

    admin_user.tokens_valid_after = None
    db.session.commit()
    assert client.get("/me", headers=auth_headers(old_access)).status_code == 200


def test_deleted_user_access_token_is_rejected(client, admin_user, admin_token):
    """A validly signed JWT cannot authenticate after its user is deleted."""

    db.session.delete(admin_user)
    db.session.commit()

    assert client.get("/me", headers=auth_headers(admin_token)).status_code == 401


def test_password_change_rolls_back_every_security_mutation(
    monkeypatch, admin_user
):
    """A late password-change failure must preserve all persisted prior state."""

    login = AuthService.login(admin_user.email, "StrongPass1")
    user_id = admin_user.id
    refresh_id = RefreshTokenRepository.get_latest_for_user(user_id).id
    original_password_hash = admin_user.password_hash
    original_valid_after = admin_user.tokens_valid_after

    def fail_refresh_revocation(user_id, *, commit=True):
        """Raise after user mutations have been flushed but before commit."""

        assert commit is False
        raise RuntimeError("injected refresh revocation failure")

    monkeypatch.setattr(
        RefreshTokenRepository,
        "revoke_all_for_user",
        staticmethod(fail_refresh_revocation),
    )

    with pytest.raises(RuntimeError, match="injected refresh revocation failure"):
        AuthService.change_password(user_id, "StrongPass1", "ChangedPass1!")

    db.session.expire_all()
    persisted_user = UserRepository.get_by_id(user_id)
    persisted_refresh = RefreshTokenRepository.get_by_id(refresh_id)
    assert persisted_user.password_hash == original_password_hash
    assert persisted_user.check_password("StrongPass1")
    assert not persisted_user.check_password("ChangedPass1!")
    assert persisted_user.tokens_valid_after == original_valid_after
    assert not persisted_refresh.is_revoked()
    assert login["refresh_token"]


def test_password_reset_rolls_back_every_security_mutation(
    monkeypatch, admin_user
):
    """A late reset failure must leave password, token, and session reusable."""

    login = AuthService.login(admin_user.email, "StrongPass1")
    user_id = admin_user.id
    refresh_id = RefreshTokenRepository.get_latest_for_user(user_id).id
    reset_token, raw_reset_token = PasswordResetToken.create_for_user(user_id)
    db.session.add(reset_token)
    db.session.commit()
    reset_token_id = reset_token.id
    original_password_hash = admin_user.password_hash
    original_valid_after = admin_user.tokens_valid_after

    def fail_refresh_revocation(user_id, *, commit=True):
        """Raise after reset mutations have been flushed but before commit."""

        assert commit is False
        raise RuntimeError("injected refresh revocation failure")

    monkeypatch.setattr(
        RefreshTokenRepository,
        "revoke_all_for_user",
        staticmethod(fail_refresh_revocation),
    )

    with pytest.raises(RuntimeError, match="injected refresh revocation failure"):
        AuthService.reset_password(raw_reset_token, "ResetStrongPass1!")

    db.session.expire_all()
    persisted_user = UserRepository.get_by_id(user_id)
    persisted_reset = db.session.get(PasswordResetToken, reset_token_id)
    persisted_refresh = RefreshTokenRepository.get_by_id(refresh_id)
    assert persisted_user.password_hash == original_password_hash
    assert persisted_user.check_password("StrongPass1")
    assert not persisted_user.check_password("ResetStrongPass1!")
    assert persisted_user.tokens_valid_after == original_valid_after
    assert not persisted_reset.is_used()
    assert not persisted_refresh.is_revoked()
    assert login["refresh_token"]


def test_logout_rolls_back_both_revocations_after_late_failure(
    monkeypatch, client, admin_user
):
    """A late logout failure must persist neither credential revocation."""

    login = _login(client, admin_user)
    access_token = login["access_token"]
    jti = decode_token(access_token)["jti"]
    refresh_id = RefreshTokenRepository.get_latest_for_user(admin_user.id).id
    original_update = RefreshTokenRepository.update

    def fail_refresh_update(*, commit=True):
        """Raise after access and refresh revocations have both been staged."""

        assert commit is False
        raise RuntimeError("injected refresh update failure")

    monkeypatch.setattr(
        RefreshTokenRepository,
        "update",
        staticmethod(fail_refresh_update),
    )

    with pytest.raises(RuntimeError, match="injected refresh update failure"):
        client.post("/auth/logout", headers=auth_headers(access_token))

    db.session.expire_all()
    assert TokenBlocklist.query.filter_by(jti=jti).one_or_none() is None
    assert not RefreshTokenRepository.get_by_id(refresh_id).is_revoked()

    monkeypatch.setattr(
        RefreshTokenRepository,
        "update",
        staticmethod(original_update),
    )
    response = client.post("/auth/logout", headers=auth_headers(access_token))
    db.session.expire_all()
    assert response.status_code == 200
    assert TokenBlocklist.query.filter_by(jti=jti).one_or_none() is not None
    assert RefreshTokenRepository.get_by_id(refresh_id).is_revoked()


def test_password_reset_rolls_back_when_final_commit_fails(
    monkeypatch, admin_user
):
    """A final commit failure must roll back every staged reset mutation."""

    AuthService.login(admin_user.email, "StrongPass1")
    user_id = admin_user.id
    refresh_id = RefreshTokenRepository.get_latest_for_user(user_id).id
    reset_token, raw_reset_token = PasswordResetToken.create_for_user(user_id)
    db.session.add(reset_token)
    db.session.commit()
    reset_token_id = reset_token.id
    original_password_hash = admin_user.password_hash
    original_valid_after = admin_user.tokens_valid_after
    original_commit = db.session.commit

    def fail_final_commit():
        """Raise instead of committing after all reset changes are flushed."""

        raise RuntimeError("injected final commit failure")

    monkeypatch.setattr(db.session, "commit", fail_final_commit)
    with pytest.raises(RuntimeError, match="injected final commit failure"):
        AuthService.reset_password(raw_reset_token, "ResetStrongPass1!")
    monkeypatch.setattr(db.session, "commit", original_commit)

    db.session.expire_all()
    persisted_user = UserRepository.get_by_id(user_id)
    persisted_reset = db.session.get(PasswordResetToken, reset_token_id)
    persisted_refresh = RefreshTokenRepository.get_by_id(refresh_id)
    assert persisted_user.password_hash == original_password_hash
    assert persisted_user.check_password("StrongPass1")
    assert not persisted_user.check_password("ResetStrongPass1!")
    assert persisted_user.tokens_valid_after == original_valid_after
    assert not persisted_reset.is_used()
    assert not persisted_refresh.is_revoked()


def test_admin_can_delete_user_with_blocklisted_access_token(
    client, admin_token, user_factory
):
    """Deleting a user removes existing blocklist rows without ORM errors."""

    target_user = user_factory(email="blocked-delete@cadri.test")
    login = _login(client, target_user)
    access_token = login["access_token"]
    jti = decode_token(access_token)["jti"]
    assert client.post(
        "/auth/logout", headers=auth_headers(access_token)
    ).status_code == 200
    assert TokenBlocklist.query.filter_by(jti=jti).one_or_none() is not None

    response = client.delete(
        f"/users/{target_user.id}", headers=auth_headers(admin_token)
    )

    assert response.status_code == 200
    assert UserRepository.get_by_id(target_user.id) is None
    assert TokenBlocklist.query.filter_by(jti=jti).one_or_none() is None
