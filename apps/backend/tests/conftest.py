import os

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db
from app.models.account_activation_token import AccountActivationToken
from app.models.mission import Mission
from app.models.mission_assignment import MissionAssignment
from app.models.mission_service_link import MissionServiceLink
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.service import Service
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    os.environ["FLASK_ENV"] = "testing"
    application = create_app()
    application.config["TESTING"] = True
    application.config["SQLALCHEMY_EXPIRE_ON_COMMIT"] = False

    with application.app_context():
        database_uri = application.config["SQLALCHEMY_DATABASE_URI"]
        if "test" not in database_uri and "cadri_test_db" not in database_uri:
            raise RuntimeError(
                "Tests must run against the test database, not the development DB."
            )

        db.drop_all()
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
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
        yield
        db.session.rollback()


@pytest.fixture()
def roles_services(app):
    with app.app_context():
        admin_role = Role(name="admin", label="Admin", description="Admin role")
        responsable_role = Role(
            name="responsable",
            label="Responsable",
            description="Responsable role",
        )
        agent_role = Role(name="agent", label="Agent", description="Agent role")

        green_spaces = Service(
            name="green_spaces",
            label="Espaces verts",
            description="Green spaces service",
        )
        roads = Service(
            name="roads",
            label="Voirie",
            description="Roads service",
        )

        db.session.add_all(
            [admin_role, responsable_role, agent_role, green_spaces, roads]
        )
        db.session.commit()

        return {
            "admin_role": admin_role,
            "responsable_role": responsable_role,
            "agent_role": agent_role,
            "green_spaces": green_spaces,
            "roads": roads,
            "admin_role_id": admin_role.id,
            "responsable_role_id": responsable_role.id,
            "agent_role_id": agent_role.id,
            "green_spaces_id": green_spaces.id,
            "roads_id": roads.id,
        }


@pytest.fixture()
def user_factory(app, roles_services):
    def _create_user(
        *,
        email="user@cadri.test",
        first_name="Test",
        last_name="User",
        role=None,
        role_id=None,
        service=None,
        service_id=None,
        is_active=True,
        password="StrongPass1",
    ):
        selected_role_id = role_id or (role.id if role else roles_services["agent_role_id"])
        selected_service_id = service_id or (
            service.id if service else roles_services["green_spaces_id"]
        )

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_id=selected_role_id,
            service_id=selected_service_id,
            is_active=is_active,
        )

        if password:
            user.set_password(password)

        db.session.add(user)
        db.session.commit()
        return user

    return _create_user


@pytest.fixture()
def admin_user(user_factory, roles_services):
    return user_factory(
        email="admin@cadri.local",
        first_name="Admin",
        last_name="Cadri",
        role_id=roles_services["admin_role_id"],
        service_id=roles_services["green_spaces_id"],
        is_active=True,
        password="StrongPass1",
    )


@pytest.fixture()
def responsable_user(user_factory, roles_services):
    return user_factory(
        email="responsable@cadri.local",
        first_name="Responsable",
        last_name="Cadri",
        role_id=roles_services["responsable_role_id"],
        service_id=roles_services["green_spaces_id"],
        is_active=True,
        password="StrongPass1",
    )


@pytest.fixture()
def agent_user(user_factory, roles_services):
    return user_factory(
        email="agent@cadri.local",
        first_name="Agent",
        last_name="Cadri",
        role_id=roles_services["agent_role_id"],
        service_id=roles_services["roads_id"],
        is_active=True,
        password="StrongPass1",
    )


@pytest.fixture()
def inactive_user(user_factory, roles_services):
    return user_factory(
        email="inactive@cadri.local",
        first_name="Inactive",
        last_name="Cadri",
        role_id=roles_services["agent_role_id"],
        service_id=roles_services["roads_id"],
        is_active=False,
        password="StrongPass1",
    )


@pytest.fixture()
def admin_access_token(app, admin_user):
    with app.app_context():
        return create_access_token(identity=str(admin_user.id))


@pytest.fixture()
def responsable_access_token(app, responsable_user):
    with app.app_context():
        return create_access_token(identity=str(responsable_user.id))


@pytest.fixture()
def agent_access_token(app, agent_user):
    with app.app_context():
        return create_access_token(identity=str(agent_user.id))


@pytest.fixture()
def admin_token(admin_access_token):
    return admin_access_token


@pytest.fixture()
def responsable_token(responsable_access_token):
    return responsable_access_token


@pytest.fixture()
def agent_token(agent_access_token):
    return agent_access_token
