"""Integration tests for UserService."""

import pytest

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utils.exceptions import AuthorizationError


def test_admin_can_create_admin_responsable_and_agent(admin_user, roles_services, monkeypatch):
    monkeypatch.setattr(AuthService, "send_activation_email_for_user", staticmethod(lambda user: None))

    for role_name in ["admin", "responsable", "agent"]:
        user = UserService.create_user(
            current_user=admin_user,
            first_name="Created",
            last_name=role_name,
            email=f"created.{role_name}@cadri.test",
            role_name=role_name,
            service_id=str(roles_services["green_spaces"].id),
        )
        assert user.email == f"created.{role_name}@cadri.test"
        assert user.is_active is False


def test_responsable_can_only_create_agent(responsable_user, roles_services, monkeypatch):
    monkeypatch.setattr(AuthService, "send_activation_email_for_user", staticmethod(lambda user: None))

    created_agent = UserService.create_user(
        current_user=responsable_user,
        first_name="Created",
        last_name="Agent",
        email="created.by.responsable@cadri.test",
        role_name="agent",
        service_id=str(roles_services["green_spaces"].id),
    )

    assert created_agent.email == "created.by.responsable@cadri.test"

    with pytest.raises(AuthorizationError):
        UserService.create_user(
            current_user=responsable_user,
            first_name="Forbidden",
            last_name="Admin",
            email="forbidden.by.responsable@cadri.test",
            role_name="admin",
            service_id=str(roles_services["green_spaces"].id),
        )
