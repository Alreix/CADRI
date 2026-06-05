def test_metadata_health_route(client):
    response = client.get("/metadata/health")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Metadata routes working"


def test_get_roles_metadata(client, roles_services):
    response = client.get("/metadata/roles")
    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, list)
    assert any(role["name"] == "admin" for role in data)


def test_get_services_metadata(client, roles_services):
    response = client.get("/metadata/services")
    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, list)
    assert any(service["name"] == "green_spaces" for service in data)


def test_get_priorities_metadata(client):
    response = client.get("/metadata/priorities")
    assert response.status_code == 200
    data = response.get_json()

    assert any(priority["name"] == "high" for priority in data)


def test_get_statuses_metadata(client):
    response = client.get("/metadata/statuses")
    assert response.status_code == 200
    data = response.get_json()

    assert any(status["name"] == "completed" for status in data)