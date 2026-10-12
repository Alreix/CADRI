"""Regression tests: refused JWTs must answer 401 outside of testing/debug mode.

Flask-RESTX only forwards exceptions to the app-level handlers registered by
flask_jwt_extended when PROPAGATE_EXCEPTIONS is enabled. It used to be enabled
implicitly by TESTING/DEBUG only, so these errors passed every test but became
500s in production. Each test therefore switches TESTING and DEBUG off.
"""

from datetime import timedelta

import pytest
from flask_jwt_extended import create_access_token

from app.config import BaseConfig, ProductionConfig
from tests.helpers.auth_helpers import auth_headers


@pytest.fixture()
def production_like_app(app, monkeypatch):
    monkeypatch.setitem(app.config, "TESTING", False)
    monkeypatch.setitem(app.config, "DEBUG", False)
    return app


def test_propagate_exceptions_is_enabled_for_every_environment():
    assert BaseConfig.PROPAGATE_EXCEPTIONS is True
    assert ProductionConfig.PROPAGATE_EXCEPTIONS is True


def test_missing_token_returns_401(production_like_app, client):
    response = client.get("/me")

    assert response.status_code == 401


def test_expired_token_returns_401(production_like_app, client, admin_user):
    with production_like_app.app_context():
        expired_token = create_access_token(
            identity=str(admin_user.id), expires_delta=timedelta(minutes=-5)
        )

    response = client.get("/me", headers=auth_headers(expired_token))

    assert response.status_code == 401


def test_revoked_token_returns_401(production_like_app, client, admin_user, admin_token):
    logout_response = client.post("/auth/logout", headers=auth_headers(admin_token))
    assert logout_response.status_code == 200

    response = client.get("/me", headers=auth_headers(admin_token))

    assert response.status_code == 401
