"""API tests for user routes."""

import pytest

from app.services.auth_service import AuthService
from tests.helpers.auth_helpers import auth_headers


def test_users_health_is_public(client):
    response = client.get("/users/health")

    assert response.status_code == 200
    assert response.get_json()["message"] == "User routes working"


def test_admin_can_list_users(client, admin_token, admin_user, agent_user):
    response = client.get("/users", headers=auth_headers(admin_token))

    assert response.status_code == 200
    data = response.get_json()
    assert data["pagination"]["total_items"] >= 2
    emails = {user["email"] for user in data["items"]}
    assert admin_user.email in emails
    assert agent_user.email in emails


def test_agent_cannot_list_users(client, agent_token, agent_user):
    response = client.get("/users", headers=auth_headers(agent_token))

    assert response.status_code == 403


def test_admin_can_create_user(client, admin_token, roles_services, monkeypatch):
    sent_activation_emails = []

    def fake_send_activation_email_for_user(user):
        sent_activation_emails.append(user.email)

    monkeypatch.setattr(
        AuthService,
        "send_activation_email_for_user",
        staticmethod(fake_send_activation_email_for_user),
    )

    response = client.post(
        "/users",
        headers=auth_headers(admin_token),
        json={
            "first_name": "New",
            "last_name": "Agent",
            "email": "new.agent@cadri.test",
            "role": "agent",
            "service_id": str(roles_services["green_spaces"].id),
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["user"]["email"] == "new.agent@cadri.test"
    assert sent_activation_emails == ["new.agent@cadri.test"]


def test_responsable_can_create_agent_but_not_admin(
    client, responsable_token, roles_services, monkeypatch
):
    monkeypatch.setattr(
        AuthService,
        "send_activation_email_for_user",
        staticmethod(lambda user: None),
    )

    allowed_response = client.post(
        "/users",
        headers=auth_headers(responsable_token),
        json={
            "first_name": "Allowed",
            "last_name": "Agent",
            "email": "allowed.agent@cadri.test",
            "role": "agent",
            "service_id": str(roles_services["green_spaces"].id),
        },
    )

    forbidden_response = client.post(
        "/users",
        headers=auth_headers(responsable_token),
        json={
            "first_name": "Forbidden",
            "last_name": "Admin",
            "email": "forbidden.admin@cadri.test",
            "role": "admin",
            "service_id": str(roles_services["green_spaces"].id),
        },
    )

    assert allowed_response.status_code == 201
    assert forbidden_response.status_code == 403


def test_get_user_details_returns_user(client, admin_token, agent_user):
    response = client.get(
        f"/users/{agent_user.id}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.get_json()["email"] == agent_user.email


def test_users_can_get_own_details(
    client,
    responsable_token,
    responsable_user,
    agent_token,
    agent_user,
):
    responsable_response = client.get(
        f"/users/{responsable_user.id}",
        headers=auth_headers(responsable_token),
    )
    agent_response = client.get(
        f"/users/{agent_user.id}",
        headers=auth_headers(agent_token),
    )

    assert responsable_response.status_code == 200
    assert responsable_response.get_json()["email"] == responsable_user.email
    assert agent_response.status_code == 200
    assert agent_response.get_json()["email"] == agent_user.email


def test_non_admin_cannot_get_another_user_details(
    client,
    responsable_token,
    agent_token,
    admin_user,
    agent_user,
):
    responsable_response = client.get(
        f"/users/{agent_user.id}",
        headers=auth_headers(responsable_token),
    )
    agent_response = client.get(
        f"/users/{admin_user.id}",
        headers=auth_headers(agent_token),
    )

    assert responsable_response.status_code == 403
    assert agent_response.status_code == 403


def test_get_user_details_requires_jwt(client, agent_user):
    response = client.get(f"/users/{agent_user.id}")

    assert response.status_code == 401


def test_admin_can_update_user(client, admin_token, agent_user, roles_services):
    response = client.patch(
        f"/users/{agent_user.id}",
        headers=auth_headers(admin_token),
        json={
            "first_name": "Updated",
            "last_name": "Agent",
            "email": "updated.agent@cadri.test",
            "role": "agent",
            "service_id": str(roles_services["roads"].id),
        },
    )

    assert response.status_code == 200
    data = response.get_json()["user"]
    assert data["email"] == "updated.agent@cadri.test"
    assert data["service"]["name"] == "roads"


def test_admin_and_responsable_can_access_assignable_users(
    client, admin_token, responsable_token, agent_user
):
    admin_response = client.get("/users/assignable", headers=auth_headers(admin_token))
    responsable_response = client.get("/users/assignable", headers=auth_headers(responsable_token))

    assert admin_response.status_code == 200
    assert responsable_response.status_code == 200
    assert agent_user.email in {user["email"] for user in admin_response.get_json()}


def test_agent_cannot_access_assignable_users(client, agent_token):
    response = client.get("/users/assignable", headers=auth_headers(agent_token))

    assert response.status_code == 403


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("page", "abc", "integer"),
        ("per_page", "abc", "integer"),
        ("page", "", "integer"),
        ("per_page", "", "integer"),
        ("page", "1.5", "integer"),
        ("per_page", "1.5", "integer"),
        ("page", "0", "greater than or equal to 1"),
        ("page", "-1", "greater than or equal to 1"),
        ("per_page", "0", "greater than or equal to 1"),
        ("per_page", "-1", "greater than or equal to 1"),
        ("per_page", "101", "less than or equal to 100"),
    ],
)
def test_users_reject_invalid_pagination(client, admin_token, field, value, message):
    """Return useful client errors for malformed integers and existing bounds."""
    response = client.get("/users", headers=auth_headers(admin_token), query_string={field: value})

    assert response.status_code == 400
    error = response.get_json()["error"].lower()
    assert field.replace("_", " ") in error.replace("_", " ")
    assert message in error


@pytest.mark.parametrize("per_page", [1, 10, 100])
def test_users_accept_valid_pagination(client, admin_token, admin_user, per_page):
    """Preserve the pagination response shape and inclusive page-size bounds."""
    response = client.get(
        "/users",
        headers=auth_headers(admin_token),
        query_string={"page": 1, "per_page": per_page},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert set(data) == {"items", "pagination"}
    assert data["pagination"] == {
        "page": 1,
        "per_page": per_page,
        "total_items": 1,
        "total_pages": 1,
    }
    assert [item["id"] for item in data["items"]] == [str(admin_user.id)]
