"""API tests for metadata routes."""

from tests.helpers.auth_helpers import auth_headers


def test_metadata_health_is_public(client):
    response = client.get("/metadata/health")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Metadata routes working"


def test_roles_requires_authentication(client):
    response = client.get("/metadata/roles")

    assert response.status_code == 401


def test_roles_returns_controlled_roles(client, admin_token, roles_services):
    response = client.get("/metadata/roles", headers=auth_headers(admin_token))

    assert response.status_code == 200
    role_names = {role["name"] for role in response.get_json()}
    assert {"admin", "responsable", "agent"}.issubset(role_names)


def test_services_returns_controlled_services(client, admin_token, roles_services):
    response = client.get("/metadata/services", headers=auth_headers(admin_token))

    assert response.status_code == 200
    service_names = {service["name"] for service in response.get_json()}
    assert {"green_spaces", "roads"}.issubset(service_names)


def test_priorities_and_statuses_are_available(client, admin_token, roles_services):
    priorities_response = client.get("/metadata/priorities", headers=auth_headers(admin_token))
    statuses_response = client.get("/metadata/statuses", headers=auth_headers(admin_token))

    assert priorities_response.status_code == 200
    assert statuses_response.status_code == 200
    assert "high" in {priority["name"] for priority in priorities_response.get_json()}
    assert "completed" in {status["name"] for status in statuses_response.get_json()}
