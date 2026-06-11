"""API tests for mission routes."""

from tests.helpers.auth_helpers import auth_headers
from tests.helpers.mission_helpers import mission_payload


def test_missions_health_is_public(client):
    response = client.get("/missions/health")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Mission routes working"


def test_admin_can_create_mission(client, admin_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )

    response = client.post("/missions", headers=auth_headers(admin_token), json=payload)

    assert response.status_code == 201
    data = response.get_json()["mission"]
    assert data["title"] == payload["title"]
    assert data["created_by"] is not None
    assert len(data["services"]) == 1
    assert len(data["assignments"]) == 1


def test_agent_cannot_create_mission(client, agent_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )

    response = client.post("/missions", headers=auth_headers(agent_token), json=payload)

    assert response.status_code == 403


def test_create_mission_requires_at_least_one_service(client, admin_token, agent_user):
    payload = mission_payload(service_ids=[], assigned_user_ids=[str(agent_user.id)])

    response = client.post("/missions", headers=auth_headers(admin_token), json=payload)

    assert response.status_code == 400


def test_list_missions_filters_my_missions_only(client, admin_token, agent_token, roles_services, agent_user, other_agent_user):
    first_payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    second_payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(other_agent_user.id)],
    )
    first_payload["title"] = "Mission for current agent"
    second_payload["title"] = "Mission for other agent"

    assert client.post("/missions", headers=auth_headers(admin_token), json=first_payload).status_code == 201
    assert client.post("/missions", headers=auth_headers(admin_token), json=second_payload).status_code == 201

    response = client.get(
        "/missions?my_missions_only=true",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200
    titles = [mission["title"] for mission in response.get_json()["items"]]
    assert titles == ["Mission for current agent"]


def test_agent_assigned_to_mission_can_update_actual_duration(client, admin_token, agent_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    created = client.post("/missions", headers=auth_headers(admin_token), json=payload)
    mission_id = created.get_json()["mission"]["id"]

    response = client.patch(
        f"/missions/{mission_id}/actual-duration",
        headers=auth_headers(agent_token),
        json={"actual_duration": 3.5},
    )

    assert response.status_code == 200
    assert response.get_json()["mission"]["actual_duration"] == 3.5


def test_agent_not_assigned_to_mission_cannot_update_actual_duration(client, admin_token, other_agent_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    created = client.post("/missions", headers=auth_headers(admin_token), json=payload)
    mission_id = created.get_json()["mission"]["id"]

    response = client.patch(
        f"/missions/{mission_id}/actual-duration",
        headers=auth_headers(other_agent_token),
        json={"actual_duration": 3.5},
    )

    assert response.status_code == 403


def test_agent_can_complete_mission_without_remark(client, admin_token, agent_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    created = client.post("/missions", headers=auth_headers(admin_token), json=payload)
    mission_id = created.get_json()["mission"]["id"]

    assert client.patch(
        f"/missions/{mission_id}/actual-duration",
        headers=auth_headers(agent_token),
        json={"actual_duration": 2.0},
    ).status_code == 200

    response = client.post(
        f"/missions/{mission_id}/complete",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200
    assert response.get_json()["completed_at"] is not None


def test_mission_with_remark_requires_validation_before_completion(client, admin_token, agent_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    created = client.post("/missions", headers=auth_headers(admin_token), json=payload)
    mission_id = created.get_json()["mission"]["id"]

    assert client.patch(
        f"/missions/{mission_id}/actual-duration",
        headers=auth_headers(agent_token),
        json={"actual_duration": 2.0},
    ).status_code == 200

    assert client.post(
        f"/missions/{mission_id}/remark",
        headers=auth_headers(agent_token),
        json={"remark": "Blocked access reported."},
    ).status_code == 200

    completion_response = client.post(
        f"/missions/{mission_id}/complete",
        headers=auth_headers(agent_token),
    )

    validation_response = client.post(
        f"/missions/{mission_id}/validate",
        headers=auth_headers(admin_token),
    )

    assert completion_response.status_code == 409
    assert validation_response.status_code == 200
    assert validation_response.get_json()["mission"]["status"] == "completed"


def test_has_remark_filter_returns_only_missions_with_remark(client, admin_token, agent_token, roles_services, agent_user):
    with_remark = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    without_remark = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    with_remark["title"] = "Mission with remark"
    without_remark["title"] = "Mission without remark"

    created_with_remark = client.post("/missions", headers=auth_headers(admin_token), json=with_remark)
    created_without_remark = client.post("/missions", headers=auth_headers(admin_token), json=without_remark)
    assert created_with_remark.status_code == 201
    assert created_without_remark.status_code == 201

    mission_id = created_with_remark.get_json()["mission"]["id"]
    assert client.post(
        f"/missions/{mission_id}/remark",
        headers=auth_headers(agent_token),
        json={"remark": "Needs validation."},
    ).status_code == 200

    response = client.get("/missions?has_remark=true", headers=auth_headers(admin_token))

    assert response.status_code == 200
    titles = {mission["title"] for mission in response.get_json()["items"]}
    assert titles == {"Mission with remark"}
