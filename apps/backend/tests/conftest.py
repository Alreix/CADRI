"""Shared pytest fixtures for the CADRI backend test suite.

The fixtures in this module keep test data centralised and reusable across the
unit, integration, and API layers. They model the core CADRI vocabulary used
throughout the backend: admin, responsable, agent, roles, and services.
"""

from __future__ import annotations

import os

os.environ["FLASK_ENV"] = "testing"
os.environ["TEST_DATABASE_URL"] = "postgresql://cadri_user:cadri_password@127.0.0.1:5432/cadri_db"
os.environ["SECRET_KEY"] = "cadri-test-secret-key"
os.environ["JWT_SECRET_KEY"] = "cadri-test-jwt-secret-key-with-strong-length"
os.environ["FRONTEND_URL"] = "http://localhost:5173"

import pytest
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.role import Role
from app.models.service import Service
from app.models.user import User


@pytest.fixture()
def app(monkeypatch):
    """Create a fresh Flask app backed by the configured test database."""

    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        "postgresql://cadri_user:cadri_password@127.0.0.1:5432/cadri_db",
    )
    monkeypatch.setenv("SECRET_KEY", "cadri-test-secret-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "cadri-test-jwt-secret-key-with-strong-length")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")

    from app import create_app

    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    flask_app.config.update(SQLALCHEMY_SESSION_OPTIONS={"expire_on_commit": False})

    context = flask_app.app_context()
    context.push()

    db.create_all()

    try:
        yield flask_app
    finally:
        db.session.remove()
        db.drop_all()
        context.pop()


@pytest.fixture()
def client(app):
    """Return a Flask test client bound to the temporary app."""

    return app.test_client()


@pytest.fixture()
def reference_data(app):
    """Seed the reference CADRI roles and services used across tests."""

    admin_role = Role(
        name="admin",
        label="Admin",
        description="Full access to user and mission management.",
    )
    responsable_role = Role(
        name="responsable",
        label="Responsable",
        description="Manages missions and creates agent accounts.",
    )
    agent_role = Role(
        name="agent",
        label="Agent",
        description="Consults and updates assigned missions.",
    )

    roads_service = Service(
        name="roads",
        label="Voirie",
        description="Road maintenance operations.",
    )
    events_service = Service(
        name="events",
        label="Événementiel",
        description="Events operations.",
    )

    db.session.add_all(
        [
            admin_role,
            responsable_role,
            agent_role,
            roads_service,
            events_service,
        ]
    )
    db.session.commit()

    return {
        "roles": {
            "admin": admin_role,
            "responsable": responsable_role,
            "agent": agent_role,
        },
        "services": {
            "roads": roads_service,
            "events": events_service,
        },
    }


@pytest.fixture()
def user_factory(app, reference_data):
    """Create realistic CADRI users for the test suite."""

    def _create_user(
        *,
        first_name: str = "Test",
        last_name: str = "User",
        email: str = "test.user@cadri.local",
        role_name: str = "agent",
        service_name: str = "roads",
        password: str | None = "Password1",
        is_active: bool = True,
    ) -> User:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_id=reference_data["roles"][role_name].id,
            service_id=reference_data["services"][service_name].id,
            is_active=is_active,
        )

        if password is not None:
            user.set_password(password)

        db.session.add(user)
        db.session.commit()
        return user

    return _create_user


@pytest.fixture()
def admin_user(user_factory):
    """Return a reusable active admin user."""

    return user_factory(
        email="admin@cadri.local",
        role_name="admin",
        service_name="roads",
        password="AdminPass1",
        is_active=True,
    )


@pytest.fixture()
def responsable_user(user_factory):
    """Return a reusable active responsable user."""

    return user_factory(
        email="responsable@cadri.local",
        role_name="responsable",
        service_name="roads",
        password="ResponsablePass1",
        is_active=True,
    )


@pytest.fixture()
def agent_user(user_factory):
    """Return a reusable active agent user."""

    return user_factory(
        email="agent@cadri.local",
        role_name="agent",
        service_name="roads",
        password="AgentPass1",
        is_active=True,
    )


@pytest.fixture()
def access_token_factory(app):
    """Create real JWT access tokens through Flask-JWT-Extended."""

    def _create_access_token(identity):
        return create_access_token(identity=str(identity))

    return _create_access_token


@pytest.fixture()
def auth_headers_factory(access_token_factory):
    """Build Authorization headers for JWT-protected requests."""

    def _make_headers(identity):
        token = access_token_factory(identity)
        return {"Authorization": f"Bearer {token}"}

    return _make_headers