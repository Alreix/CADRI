"""Additional API tests for user administration routes."""

import uuid

from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from tests.helpers.auth_helpers import auth_headers


def test_responsable_cannot_list_all_users(client, responsable_token):
    response = client.get("/users", headers=auth_headers(responsable_token))

    assert response.status_code == 403


def test_users_list_supports_search_role_service_and_pagination(
    client,
    admin_token,
    admin_user,
    agent_user,
    roles_services,
):
    search_response = client.get(
        "/users",
        headers=auth_headers(admin_token),
        query_string={"search": "agent"},
    )
    assert search_response.status_code == 200
    search_emails = {user["email"] for user in search_response.get_json()["items"]}
    assert agent_user.email in search_emails

    role_response = client.get(
        "/users",
        headers=auth_headers(admin_token),
        query_string={"role": "agent"},
    )
    assert role_response.status_code == 200
    assert all(user["role"]["name"] == "agent" for user in role_response.get_json()["items"])

    service_response = client.get(
        "/users",
        headers=auth_headers(admin_token),
        query_string={"service_id": str(roles_services["roads"].id)},
    )
    assert service_response.status_code == 200
    assert all(
        user["service"]["name"] == "roads"
        for user in service_response.get_json()["items"]
    )

    pagination_response = client.get(
        "/users",
        headers=auth_headers(admin_token),
        query_string={"page": 1, "per_page": 1},
    )
    assert pagination_response.status_code == 200
    data = pagination_response.get_json()
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 1
    assert len(data["items"]) == 1


def test_admin_create_user_rejects_duplicate_active_email(
    client,
    admin_token,
    admin_user,
):
    response = client.post(
        "/users",
        headers=auth_headers(admin_token),
        json={
            "first_name": "Duplicate",
            "last_name": "Email",
            "email": admin_user.email,
            "role": "agent",
            "service_id": str(admin_user.service_id),
        },
    )

    assert response.status_code == 409


def test_admin_create_user_rejects_unknown_role_and_service(
    client,
    admin_token,
    roles_services,
):
    unknown_role_response = client.post(
        "/users",
        headers=auth_headers(admin_token),
        json={
            "first_name": "Unknown",
            "last_name": "Role",
            "email": "unknown.role@cadri.test",
            "role": "unknown",
            "service_id": str(roles_services["green_spaces"].id),
        },
    )

    assert unknown_role_response.status_code == 403
    assert unknown_role_response.get_json()["error"] == "Target role is not allowed."

    unknown_service_response = client.post(
        "/users",
        headers=auth_headers(admin_token),
        json={
            "first_name": "Unknown",
            "last_name": "Service",
            "email": "unknown.service@cadri.test",
            "role": "agent",
            "service_id": str(uuid.uuid4()),
        },
    )

    assert unknown_service_response.status_code == 404
    assert unknown_service_response.get_json()["error"] == "Service not found."


def test_agent_cannot_create_user(client, agent_token, roles_services):
    response = client.post(
        "/users",
        headers=auth_headers(agent_token),
        json={
            "first_name": "Forbidden",
            "last_name": "Create",
            "email": "forbidden.create@cadri.test",
            "role": "agent",
            "service_id": str(roles_services["green_spaces"].id),
        },
    )

    assert response.status_code == 403


def test_get_user_details_unknown_user_returns_404(client, admin_token):
    response = client.get(
        f"/users/{uuid.uuid4()}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


def test_update_user_rejects_duplicate_email(client, admin_token, admin_user, agent_user):
    response = client.patch(
        f"/users/{agent_user.id}",
        headers=auth_headers(admin_token),
        json={
            "first_name": "Updated",
            "last_name": "Duplicate",
            "email": admin_user.email,
            "role": "agent",
            "service_id": str(agent_user.service_id),
        },
    )

    assert response.status_code == 409


def test_update_user_requires_admin(client, responsable_token, agent_user, roles_services):
    response = client.patch(
        f"/users/{agent_user.id}",
        headers=auth_headers(responsable_token),
        json={
            "first_name": "Blocked",
            "last_name": "Update",
            "email": "blocked.update@cadri.test",
            "role": "agent",
            "service_id": str(roles_services["roads"].id),
        },
    )

    assert response.status_code == 403


def test_admin_can_delete_user(client, admin_token, user_factory, roles_services):
    user = user_factory(
        email="delete.me@cadri.test",
        role=roles_services["agent_role"],
        service=roles_services["roads"],
    )

    response = client.delete(
        f"/users/{user.id}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert UserRepository.get_by_id(user.id) is None


def test_non_admin_cannot_delete_user(client, responsable_token, agent_user):
    response = client.delete(
        f"/users/{agent_user.id}",
        headers=auth_headers(responsable_token),
    )

    assert response.status_code == 403


def test_assignable_users_only_return_active_agents_and_responsables(
    client,
    admin_token,
    admin_user,
    responsable_user,
    agent_user,
    user_factory,
    roles_services,
):
    inactive_agent = user_factory(
        email="inactive.assignable@cadri.test",
        role=roles_services["agent_role"],
        service=roles_services["roads"],
        is_active=False,
    )

    response = client.get("/users/assignable", headers=auth_headers(admin_token))

    assert response.status_code == 200
    emails = {user["email"] for user in response.get_json()}
    assert agent_user.email in emails
    assert responsable_user.email in emails
    assert admin_user.email not in emails
    assert inactive_agent.email not in emails
