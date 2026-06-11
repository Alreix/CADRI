"""Shared pytest configuration for the CADRI backend.

The tests are designed to run inside the backend Docker container with:

    docker compose exec backend pytest

Important safety rule:
    The test application must use TEST_DATABASE_URL / cadri_test_db.
    If the configured database URI does not look like a test database,
    the suite stops immediately to avoid wiping development data.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from flask_jwt_extended import create_access_token

# This must be set before create_app() reads app.config.get_config().
os.environ["FLASK_ENV"] = "testing"

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.account_activation_token import AccountActivationToken  # noqa: E402
from app.models.mission import Mission  # noqa: E402
from app.models.mission_assignment import MissionAssignment  # noqa: E402
from app.models.mission_service_link import MissionServiceLink  # noqa: E402
from app.models.password_reset_token import PasswordResetToken  # noqa: E402
from app.models.refresh_token import RefreshToken  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.service import Service  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils.constants import ADMIN_ROLE, AGENT_ROLE, RESPONSABLE_ROLE  # noqa: E402


@pytest.fixture(scope="session")
def app():
    """Create one Flask app configured for testing."""
    flask_app = create_app()

    database_uri = flask_app.config["SQLALCHEMY_DATABASE_URI"]
    if "test" not in database_uri and "cadri_test_db" not in database_uri:
        raise RuntimeError(
            "Tests are not using the test database. "
            f"Current database URI: {database_uri}"
        )

    with flask_app.app_context():
        db.drop_all()
        db.create_all()

    yield flask_app

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Return a Flask test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_database(app):
    """Start and end every test with empty business tables."""
    with app.app_context():
        _delete_all_rows()
        yield
        db.session.remove()
        _delete_all_rows()


def _delete_all_rows() -> None:
    """Delete rows in an order that respects foreign keys."""
    db.session.query(MissionAssignment).delete()
    db.session.query(MissionServiceLink).delete()
    db.session.query(Mission).delete()
    db.session.query(AccountActivationToken).delete()
    db.session.query(PasswordResetToken).delete()
    db.session.query(RefreshToken).delete()
    db.session.query(User).delete()
    db.session.query(Role).delete()
    db.session.query(Service).delete()
    db.session.commit()


@pytest.fixture()
def roles_services(app):
    """Create the controlled roles and services required by CADRI."""
    admin_role = Role(name=ADMIN_ROLE, label="Admin", description="Administrator")
    responsable_role = Role(
        name=RESPONSABLE_ROLE,
        label="Manager",
        description="Municipal service manager",
    )
    agent_role = Role(name=AGENT_ROLE, label="Agent", description="Field agent")

    green_spaces = Service(
        name="green_spaces",
        label="Green spaces",
        description="Green spaces department",
    )
    roads = Service(name="roads", label="Roads", description="Roads department")

    db.session.add_all([admin_role, responsable_role, agent_role, green_spaces, roads])
    db.session.commit()

    return {
        "admin_role": admin_role,
        "responsable_role": responsable_role,
        "agent_role": agent_role,
        "green_spaces": green_spaces,
        "roads": roads,
    }


@pytest.fixture()
def user_factory(roles_services):
    """Create users with the requested role and active state."""

    def _create_user(
        *,
        email: str,
        role: Role,
        service: Service | None = None,
        first_name: str = "Test",
        last_name: str = "User",
        password: str = "StrongPass1",
        is_active: bool = True,
    ) -> User:
        selected_service = service or roles_services["green_spaces"]
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_id=role.id,
            service_id=selected_service.id,
            is_active=is_active,
            activated_at=datetime.now(timezone.utc) if is_active else None,
        )
        if is_active:
            user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return _create_user


@pytest.fixture()
def admin_user(user_factory, roles_services):
    return user_factory(
        email="admin@cadri.test",
        role=roles_services["admin_role"],
        first_name="Ada",
        last_name="Admin",
    )


@pytest.fixture()
def responsable_user(user_factory, roles_services):
    return user_factory(
        email="responsable@cadri.test",
        role=roles_services["responsable_role"],
        first_name="René",
        last_name="Responsable",
    )


@pytest.fixture()
def agent_user(user_factory, roles_services):
    return user_factory(
        email="agent@cadri.test",
        role=roles_services["agent_role"],
        first_name="Alice",
        last_name="Agent",
    )


@pytest.fixture()
def other_agent_user(user_factory, roles_services):
    return user_factory(
        email="other.agent@cadri.test",
        role=roles_services["agent_role"],
        first_name="Oscar",
        last_name="Other",
    )


def _access_token_for(user: User) -> str:
    return create_access_token(identity=str(user.id))


@pytest.fixture()
def admin_token(app, admin_user):
    return _access_token_for(admin_user)


@pytest.fixture()
def responsable_token(app, responsable_user):
    return _access_token_for(responsable_user)


@pytest.fixture()
def agent_token(app, agent_user):
    return _access_token_for(agent_user)


@pytest.fixture()
def other_agent_token(app, other_agent_user):
    return _access_token_for(other_agent_user)
