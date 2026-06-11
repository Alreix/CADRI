"""Integration tests for repository helpers."""

from app.repositories.role_repository import RoleRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository


def test_role_repository_get_by_name(roles_services):
    role = RoleRepository.get_by_name("admin")

    assert role is not None
    assert role.label == "Admin"


def test_service_repository_get_by_name(roles_services):
    service = ServiceRepository.get_by_name("green_spaces")

    assert service is not None
    assert service.label == "Green spaces"


def test_user_repository_list_filtered_by_search(admin_user, agent_user):
    users, total_items = UserRepository.list_filtered(search="agent")

    assert total_items == 1
    assert users[0].email == agent_user.email
