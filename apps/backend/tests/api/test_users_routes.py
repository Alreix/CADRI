"""API tests for the current users routes.

The current backend only registers a health route here; full user RESTX
resources are not implemented yet in the codebase.
"""

from app.services.email_service import EmailService


def test_get_me_success(client, admin_access_token):
    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == "admin@cadri.local"


def test_update_me_success(client, admin_access_token):
    response = client.patch(
        "/me",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json={
            "first_name": "Updated",
            "last_name": "Admin",
            "email": "updated_admin@cadri.local",
        },
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["message"] == "Profile updated successfully"
    assert data["user"]["email"] == "updated_admin@cadri.local"


def test_list_users_success(client, admin_access_token):
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert response.status_code == 200
    data = response.get_json()

    assert "items" in data
    assert "pagination" in data


def test_create_user_success_as_admin(
    client,
    admin_access_token,
    roles_services,
    monkeypatch,
):
    def fake_send_activation_email_for_user(user):
        return None

    monkeypatch.setattr(
        EmailService,
        "send_activation_email",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "app.services.auth_service.AuthService.send_activation_email_for_user",
        fake_send_activation_email_for_user,
    )

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_access_token}"},
        json={
            "first_name": "New",
            "last_name": "Agent",
            "email": "new_agent@cadri.local",
            "role": "agent",
            "service_id": str(roles_services["green_spaces_id"]),
        },
    )

    assert response.status_code == 201
    data = response.get_json()

    assert data["message"] == "User created successfully"
    assert data["user"]["email"] == "new_agent@cadri.local"


def test_responsable_cannot_create_admin(
    client,
    responsable_access_token,
    roles_services,
):
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {responsable_access_token}"},
        json={
            "first_name": "Bad",
            "last_name": "Admin",
            "email": "bad_admin@cadri.local",
            "role": "admin",
            "service_id": str(roles_services["green_spaces_id"]),
        },
    )

    assert response.status_code == 403


def test_get_user_details_success(client, admin_access_token, agent_user):
    response = client.get(
        f"/users/{agent_user.id}",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == "agent@cadri.local"


def test_list_assignable_users_success(
    client,
    admin_access_token,
    agent_user,
    responsable_user,
):
    response = client.get(
        "/users/assignable",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, list)
    assert len(data) >= 2
