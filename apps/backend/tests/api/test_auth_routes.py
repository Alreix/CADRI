"""API tests for the current auth routes.

The current codebase only exposes a health endpoint in this module, so the test
covers the registered route without inventing missing RESTX resources yet.
"""

from __future__ import annotations


def test_auth_health_route(client):
    response = client.get("/auth/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {"message": "Auth routes working"}
