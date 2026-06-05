def test_missions_health_route(client):
    response = client.get("/missions/health")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Mission routes working"