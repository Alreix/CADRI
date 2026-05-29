"""API tests for the current metadata routes.

Only the registered health endpoint exists at the moment, so the test keeps to
that real behavior instead of fabricating missing metadata resources.
"""

from __future__ import annotations


def test_metadata_health_route(client):
    response = client.get("/metadata/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {"message": "Metadata routes working"}
