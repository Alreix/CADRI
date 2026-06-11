"""Additional API tests for current-user profile routes."""

from tests.helpers.auth_helpers import auth_headers


def test_get_me_requires_authentication(client):
    response = client.get("/me")

    assert response.status_code == 401


def test_patch_me_requires_authentication(client):
    response = client.patch(
        "/me",
        json={
            "first_name": "No",
            "last_name": "Token",
            "email": "notoken@cadri.test",
        },
    )

    assert response.status_code == 401


def test_patch_me_rejects_duplicate_email(client, agent_token, admin_user):
    response = client.patch(
        "/me",
        headers=auth_headers(agent_token),
        json={
            "first_name": "Agent",
            "last_name": "Cadri",
            "email": admin_user.email,
        },
    )

    assert response.status_code == 409


def test_patch_me_rejects_invalid_email(client, agent_token):
    response = client.patch(
        "/me",
        headers=auth_headers(agent_token),
        json={
            "first_name": "Agent",
            "last_name": "Cadri",
            "email": "invalid-email",
        },
    )

    assert response.status_code == 400


def test_patch_me_ignores_role_and_service_changes(client, agent_token, agent_user, roles_services):
    original_role_id = str(agent_user.role_id)
    original_service_id = str(agent_user.service_id)

    response = client.patch(
        "/me",
        headers=auth_headers(agent_token),
        json={
            "first_name": "Updated",
            "last_name": "Self",
            "email": "updated.self@cadri.test",
            "role": "admin",
            "service_id": str(roles_services["green_spaces"].id),
        },
    )

    assert response.status_code == 200
    data = response.get_json()["user"]
    assert data["email"] == "updated.self@cadri.test"
    assert data["role"]["id"] == original_role_id
    assert data["service"]["id"] == original_service_id
