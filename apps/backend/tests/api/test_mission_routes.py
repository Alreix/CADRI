"""API tests for mission routes."""

from datetime import datetime, timedelta, timezone

import pytest

from app.utils.constants import (
    MISSION_STATUS_COMPLETED,
    MISSION_STATUS_IN_PROGRESS,
    MISSION_STATUS_REMARK_PENDING_VALIDATION,
    MISSION_STATUS_TO_DO,
)


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def mission_payload(*, service_ids, assigned_user_ids, title="Mission test"):
    start_date = datetime.now(timezone.utc) + timedelta(days=1)
    end_date = start_date + timedelta(hours=2)

    return {
        "title": title,
        "intervention_type": "Maintenance",
        "location": "Town center",
        "description": "Mission created by automated tests.",
        "planned_agents_count": 1,
        "estimated_duration": 2.5,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "priority": "medium",
        "required_equipment": "Standard tools",
        "signage_required": False,
        "service_ids": service_ids,
        "assigned_user_ids": assigned_user_ids,
    }


def create_mission(client, token, roles_services, agent_user, **overrides):
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )
    payload.update(overrides)

    response = client.post(
        "/missions",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201, response.get_json()
    return response.get_json()["mission"]


def start_mission(client, token, mission):
    """Start a mission through the API before performing tracking actions."""
    response = client.patch(
        f"/missions/{mission['id']}/status",
        headers=auth_headers(token),
        json={"status": MISSION_STATUS_IN_PROGRESS},
    )
    assert response.status_code == 200, response.get_json()
    assert response.get_json()["mission"]["status"] == MISSION_STATUS_IN_PROGRESS


def test_missions_health_route_is_public(client):
    response = client.get("/missions/health")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Mission routes working"}


def test_admin_can_create_mission(client, admin_access_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )

    response = client.post(
        "/missions",
        headers=auth_headers(admin_access_token),
        json=payload,
    )

    assert response.status_code == 201
    data = response.get_json()

    assert data["message"] == "Mission created successfully"
    assert data["mission"]["title"] == "Mission test"
    assert data["mission"]["status"] == "to_do"
    assert data["mission"]["created_by"] is not None
    assert len(data["mission"]["services"]) == 1
    assert len(data["mission"]["assignments"]) == 1


def test_responsable_can_create_mission(
    client, responsable_access_token, roles_services, agent_user
):
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )

    response = client.post(
        "/missions",
        headers=auth_headers(responsable_access_token),
        json=payload,
    )

    assert response.status_code == 201
    assert response.get_json()["mission"]["title"] == "Mission test"


def test_agent_cannot_create_mission(client, agent_access_token, roles_services, agent_user):
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )

    response = client.post(
        "/missions",
        headers=auth_headers(agent_access_token),
        json=payload,
    )

    assert response.status_code == 403


def test_create_mission_requires_at_least_one_service(
    client,
    admin_access_token,
    agent_user,
):
    payload = mission_payload(
        service_ids=[],
        assigned_user_ids=[str(agent_user.id)],
    )

    response = client.post(
        "/missions",
        headers=auth_headers(admin_access_token),
        json=payload,
    )

    assert response.status_code == 400


def test_create_mission_rejects_invalid_date_order(
    client,
    admin_access_token,
    roles_services,
    agent_user,
):
    start_date = datetime.now(timezone.utc) + timedelta(days=2)
    end_date = datetime.now(timezone.utc) + timedelta(days=1)
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )
    payload["start_date"] = start_date.isoformat()
    payload["end_date"] = end_date.isoformat()

    response = client.post(
        "/missions",
        headers=auth_headers(admin_access_token),
        json=payload,
    )

    assert response.status_code == 400


def test_list_missions_supports_my_missions_only_filter(
    client,
    admin_access_token,
    responsable_access_token,
    agent_access_token,
    roles_services,
    agent_user,
    responsable_user,
):
    create_mission(
        client,
        admin_access_token,
        roles_services,
        agent_user,
        title="Mission assigned to agent",
        assigned_user_ids=[str(agent_user.id)],
    )
    create_mission(
        client,
        admin_access_token,
        roles_services,
        agent_user,
        title="Mission assigned to responsable",
        assigned_user_ids=[str(responsable_user.id)],
    )

    admin_response = client.get(
        "/missions",
        headers=auth_headers(admin_access_token),
    )
    responsable_response = client.get(
        "/missions",
        headers=auth_headers(responsable_access_token),
    )
    agent_response = client.get(
        "/missions",
        headers=auth_headers(agent_access_token),
    )
    my_missions_response = client.get(
        "/missions?my_missions_only=true",
        headers=auth_headers(agent_access_token),
    )
    status_response = client.get(
        "/missions",
        headers=auth_headers(agent_access_token),
        query_string={"status": "to_do"},
    )

    assert admin_response.status_code == 200
    assert responsable_response.status_code == 200
    assert agent_response.status_code == 200
    assert my_missions_response.status_code == 200
    assert status_response.status_code == 200

    all_titles = {"Mission assigned to agent", "Mission assigned to responsable"}
    assert {mission["title"] for mission in admin_response.get_json()["items"]} == all_titles
    assert {mission["title"] for mission in responsable_response.get_json()["items"]} == all_titles
    assert {mission["title"] for mission in agent_response.get_json()["items"]} == {
        "Mission assigned to agent"
    }
    assert {mission["title"] for mission in my_missions_response.get_json()["items"]} == {
        "Mission assigned to agent"
    }
    assert {mission["title"] for mission in status_response.get_json()["items"]} == {
        "Mission assigned to agent"
    }


def test_agent_assigned_to_mission_can_update_status_and_actual_duration(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
):
    mission = create_mission(client, admin_access_token, roles_services, agent_user)

    status_response = client.patch(
        f"/missions/{mission['id']}/status",
        headers=auth_headers(agent_access_token),
        json={"status": "in_progress"},
    )

    assert status_response.status_code == 200
    assert status_response.get_json()["mission"]["status"] == "in_progress"

    duration_response = client.patch(
        f"/missions/{mission['id']}/actual-duration",
        headers=auth_headers(agent_access_token),
        json={"actual_duration": 3.5},
    )

    assert duration_response.status_code == 200
    assert duration_response.get_json()["mission"]["actual_duration"] == 3.5


def test_agent_not_assigned_to_mission_cannot_update_actual_duration(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
    responsable_user,
):
    mission = create_mission(
        client,
        admin_access_token,
        roles_services,
        agent_user,
        assigned_user_ids=[str(responsable_user.id)],
    )

    response = client.patch(
        f"/missions/{mission['id']}/actual-duration",
        headers=auth_headers(agent_access_token),
        json={"actual_duration": 2},
    )

    assert response.status_code == 403


def test_agent_can_complete_mission_without_remark(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
):
    """Exercise mission behavior after the required start transition."""
    mission = create_mission(client, admin_access_token, roles_services, agent_user)

    start_mission(client, agent_access_token, mission)

    duration_response = client.patch(
        f"/missions/{mission['id']}/actual-duration",
        headers=auth_headers(agent_access_token),
        json={"actual_duration": 2},
    )
    assert duration_response.status_code == 200

    complete_response = client.post(
        f"/missions/{mission['id']}/complete",
        headers=auth_headers(agent_access_token),
    )

    assert complete_response.status_code == 200
    assert complete_response.get_json()["completed_at"] is not None


def test_mission_with_remark_requires_validation_before_completion(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
):
    """Exercise mission behavior after the required start transition."""
    mission = create_mission(client, admin_access_token, roles_services, agent_user)

    start_mission(client, agent_access_token, mission)

    duration_response = client.patch(
        f"/missions/{mission['id']}/actual-duration",
        headers=auth_headers(agent_access_token),
        json={"actual_duration": 2},
    )
    assert duration_response.status_code == 200

    remark_response = client.post(
        f"/missions/{mission['id']}/remark",
        headers=auth_headers(agent_access_token),
        json={"remark": "Blocked access on site."},
    )
    assert remark_response.status_code == 200
    assert remark_response.get_json()["mission"]["status"] == "remark_pending_validation"

    completion_before_validation = client.post(
        f"/missions/{mission['id']}/complete",
        headers=auth_headers(agent_access_token),
    )
    assert completion_before_validation.status_code == 409

    validation_response = client.post(
        f"/missions/{mission['id']}/validate",
        headers=auth_headers(admin_access_token),
    )
    assert validation_response.status_code == 200
    validated_mission = validation_response.get_json()["mission"]
    assert validated_mission["status"] == "completed"
    assert validated_mission["validated_at"] is not None
    assert validated_mission["completed_at"] is not None


def test_has_remark_filter_returns_only_missions_with_remark(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
):
    """Exercise mission behavior after the required start transition."""
    with_remark = create_mission(
        client,
        admin_access_token,
        roles_services,
        agent_user,
        title="Mission with remark",
    )
    create_mission(
        client,
        admin_access_token,
        roles_services,
        agent_user,
        title="Mission without remark",
    )

    start_mission(client, agent_access_token, with_remark)

    duration_response = client.patch(
        f"/missions/{with_remark['id']}/actual-duration",
        headers=auth_headers(agent_access_token),
        json={"actual_duration": 2},
    )
    assert duration_response.status_code == 200

    remark_response = client.post(
        f"/missions/{with_remark['id']}/remark",
        headers=auth_headers(agent_access_token),
        json={"remark": "Needs validation."},
    )
    assert remark_response.status_code == 200

    response = client.get(
        "/missions?has_remark=true",
        headers=auth_headers(admin_access_token),
    )

    assert response.status_code == 200
    titles = {mission["title"] for mission in response.get_json()["items"]}

    assert titles == {"Mission with remark"}


def test_admin_can_delete_mission(
    client,
    admin_access_token,
    roles_services,
    agent_user,
):
    mission = create_mission(client, admin_access_token, roles_services, agent_user)

    delete_response = client.delete(
        f"/missions/{mission['id']}",
        headers=auth_headers(admin_access_token),
    )

    assert delete_response.status_code == 200

    get_response = client.get(
        f"/missions/{mission['id']}",
        headers=auth_headers(admin_access_token),
    )

    assert get_response.status_code == 404


@pytest.mark.parametrize(
    "status",
    [
        MISSION_STATUS_TO_DO,
        MISSION_STATUS_IN_PROGRESS,
        MISSION_STATUS_REMARK_PENDING_VALIDATION,
        MISSION_STATUS_COMPLETED,
    ],
)
@pytest.mark.parametrize("action", ["actual-duration", "remark", "complete"])
def test_tracking_actions_enforce_current_status(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
    status,
    action,
):
    """Reject invalid direct API actions without changing persisted mission data."""
    mission = create_mission(client, admin_access_token, roles_services, agent_user)
    path = f"/missions/{mission['id']}"
    headers = auth_headers(agent_access_token)
    if status != MISSION_STATUS_TO_DO:
        start_mission(client, agent_access_token, mission)
        response = client.patch(
            f"{path}/actual-duration", headers=headers, json={"actual_duration": 2}
        )
        assert response.status_code == 200
    if status == MISSION_STATUS_REMARK_PENDING_VALIDATION:
        response = client.post(f"{path}/remark", headers=headers, json={"remark": "Review"})
        assert response.status_code == 200
    elif status == MISSION_STATUS_COMPLETED:
        assert client.post(f"{path}/complete", headers=headers).status_code == 200

    before = client.get(path, headers=headers).get_json()
    assert before["status"] == status
    if action == "actual-duration":
        response = client.patch(f"{path}/{action}", headers=headers, json={"actual_duration": 3})
        allowed = status in (MISSION_STATUS_IN_PROGRESS, MISSION_STATUS_REMARK_PENDING_VALIDATION)
    elif action == "remark":
        response = client.post(f"{path}/{action}", headers=headers, json={"remark": "New remark"})
        allowed = status == MISSION_STATUS_IN_PROGRESS
    else:
        response = client.post(f"{path}/{action}", headers=headers)
        allowed = status == MISSION_STATUS_IN_PROGRESS

    assert response.status_code == (200 if allowed else 409), response.get_json()
    after = client.get(path, headers=headers).get_json()
    if not allowed:
        assert after == before
    elif action == "actual-duration":
        assert after["actual_duration"] == 3
        assert after["status"] == status
    elif action == "remark":
        assert after["status"] == MISSION_STATUS_REMARK_PENDING_VALIDATION
        assert after["remark"] == "New remark"
        assert after["completed_at"] is None
    else:
        assert after["status"] == MISSION_STATUS_COMPLETED
        assert after["completed_at"] is not None
        assert after["remark"] is None


def test_started_mission_requires_duration_before_completion(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
):
    """Keep the existing missing-duration error for a started mission."""
    mission = create_mission(client, admin_access_token, roles_services, agent_user)
    start_mission(client, agent_access_token, mission)
    response = client.post(
        f"/missions/{mission['id']}/complete", headers=auth_headers(agent_access_token)
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Actual duration is required before completion."


@pytest.mark.parametrize("validator_role", ["admin", "responsable"])
def test_remark_can_receive_duration_then_manager_validation(
    client,
    admin_access_token,
    responsable_access_token,
    agent_access_token,
    roles_services,
    agent_user,
    validator_role,
):
    """Allow duration entry and correction while a remark awaits manager validation."""
    mission = create_mission(client, admin_access_token, roles_services, agent_user)
    start_mission(client, agent_access_token, mission)
    path = f"/missions/{mission['id']}"
    headers = auth_headers(agent_access_token)
    manager_headers = auth_headers(
        admin_access_token if validator_role == "admin" else responsable_access_token
    )
    response = client.post(f"{path}/remark", headers=headers, json={"remark": "Review needed"})
    assert response.status_code == 200
    assert response.get_json()["mission"]["status"] == MISSION_STATUS_REMARK_PENDING_VALIDATION
    assert response.get_json()["mission"]["actual_duration"] is None
    assert client.post(f"{path}/validate", headers=headers).status_code == 403
    response = client.post(f"{path}/validate", headers=manager_headers)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Actual duration is required before validation."
    for duration in (2, 3):
        response = client.patch(
            f"{path}/actual-duration", headers=headers, json={"actual_duration": duration}
        )
        assert response.status_code == 200
        assert response.get_json()["mission"]["actual_duration"] == duration
    response = client.post(f"{path}/validate", headers=manager_headers)
    assert response.status_code == 200
    validated = response.get_json()["mission"]
    assert validated["status"] == MISSION_STATUS_COMPLETED
    assert validated["validated_at"] is not None
    assert validated["completed_at"] is not None
    assert client.post(f"{path}/validate", headers=manager_headers).status_code == 409


@pytest.mark.parametrize("action", ["status", "actual-duration", "remark", "complete"])
def test_unassigned_agent_cannot_use_workflow_actions(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
    responsable_user,
    action,
):
    """Preserve assignment checks before evaluating mission state."""
    mission = create_mission(
        client,
        admin_access_token,
        roles_services,
        agent_user,
        assigned_user_ids=[str(responsable_user.id)],
    )
    path = f"/missions/{mission['id']}"
    headers = auth_headers(agent_access_token)
    payloads = {
        "status": {"status": MISSION_STATUS_IN_PROGRESS},
        "actual-duration": {"actual_duration": 2},
        "remark": {"remark": "Unauthorized"},
    }
    method = "PATCH" if action in ("status", "actual-duration") else "POST"
    response = client.open(
        f"{path}/{action}", method=method, headers=headers, json=payloads.get(action)
    )
    assert response.status_code == 403
    assert client.get(path, headers=headers).status_code == 403


def test_restarting_mission_keeps_existing_validation_error(
    client,
    admin_access_token,
    agent_access_token,
    roles_services,
    agent_user,
):
    """Preserve the public 400 error for an invalid repeated start."""
    mission = create_mission(client, admin_access_token, roles_services, agent_user)
    start_mission(client, agent_access_token, mission)
    response = client.patch(
        f"/missions/{mission['id']}/status",
        headers=auth_headers(agent_access_token),
        json={"status": MISSION_STATUS_IN_PROGRESS},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Mission can only be started from to_do status."
