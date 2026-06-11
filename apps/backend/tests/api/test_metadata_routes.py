"""API tests for metadata routes."""


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_metadata_health_route_is_public(client):
    response = client.get("/metadata/health")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Metadata routes working"}


def test_roles_requires_authentication(client):
    response = client.get("/metadata/roles")

    assert response.status_code == 401


def test_roles_returns_controlled_roles(client, admin_access_token, roles_services):
    response = client.get(
        "/metadata/roles",
        headers=auth_headers(admin_access_token),
    )

    assert response.status_code == 200
    role_names = {role["name"] for role in response.get_json()}

    assert role_names == {"admin", "responsable", "agent"}


def test_services_returns_controlled_services(client, admin_access_token, roles_services):
    response = client.get(
        "/metadata/services",
        headers=auth_headers(admin_access_token),
    )

    assert response.status_code == 200
    service_names = {service["name"] for service in response.get_json()}

    assert "green_spaces" in service_names
    assert "roads" in service_names


def test_priorities_returns_controlled_priorities(client, admin_access_token):
    response = client.get(
        "/metadata/priorities",
        headers=auth_headers(admin_access_token),
    )

    assert response.status_code == 200
    priority_names = {priority["name"] for priority in response.get_json()}

    assert priority_names == {"low", "medium", "high"}


def test_statuses_returns_controlled_statuses(client, admin_access_token):
    response = client.get(
        "/metadata/statuses",
        headers=auth_headers(admin_access_token),
    )

    assert response.status_code == 200
    status_names = {status["name"] for status in response.get_json()}

    assert status_names == {
        "to_do",
        "in_progress",
        "remark_pending_validation",
        "completed",
    }
