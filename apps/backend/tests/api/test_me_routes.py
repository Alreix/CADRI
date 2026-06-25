"""API tests for the current user profile routes."""

from tests.helpers.auth_helpers import auth_headers


def test_me_health_is_public(client):
    response = client.get("/me/health")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Me routes working"


def test_get_me_returns_current_user(client, agent_token, agent_user):
    response = client.get("/me", headers=auth_headers(agent_token))

    assert response.status_code == 200
    assert response.get_json()["email"] == agent_user.email


def test_patch_me_updates_own_profile(client, agent_token):
    response = client.patch(
        "/me",
        headers=auth_headers(agent_token),
        json={
            "first_name": "Updated",
            "last_name": "Profile",
            "email": "updated.profile@cadri.test",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "updated.profile@cadri.test"
