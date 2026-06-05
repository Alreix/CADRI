"""API tests for the current users routes.

The current backend only registers a health route here; full user RESTX
resources are not implemented yet in the codebase.
"""

from __future__ import annotations


def test_users_health_route(client):
    response = client.get("/users/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {"message": "User routes working"}
