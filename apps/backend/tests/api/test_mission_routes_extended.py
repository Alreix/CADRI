"""Additional API tests for mission route edge cases and filters."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from app.extensions import db
from app.models.mission import Mission
from app.repositories.mission_repository import MissionRepository
from app.utils.constants import MISSION_STATUS_IN_PROGRESS
from tests.helpers.auth_helpers import auth_headers
from tests.helpers.mission_helpers import mission_payload


def create_api_mission(client, token, roles_services, assigned_user_ids, **overrides):
    payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(user_id) for user_id in assigned_user_ids],
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
    """Start the mission before testing authorized tracking operations."""
    response = client.patch(
        f"/missions/{mission['id']}/status",
        headers=auth_headers(token),
        json={"status": MISSION_STATUS_IN_PROGRESS},
    )
    assert response.status_code == 200, response.get_json()


def test_get_mission_details_returns_relations(client, admin_token, roles_services, agent_user):
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])

    response = client.get(
        f"/missions/{mission['id']}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == mission["id"]
    assert len(data["services"]) == 1
    assert len(data["assignments"]) == 1


def test_mission_details_authorization_rules(
    client,
    admin_token,
    responsable_token,
    agent_token,
    roles_services,
    agent_user,
    responsable_user,
):
    assigned_mission = create_api_mission(
        client,
        admin_token,
        roles_services,
        [agent_user.id],
    )
    unassigned_mission = create_api_mission(
        client,
        admin_token,
        roles_services,
        [responsable_user.id],
    )

    responsable_response = client.get(
        f"/missions/{unassigned_mission['id']}",
        headers=auth_headers(responsable_token),
    )
    agent_assigned_response = client.get(
        f"/missions/{assigned_mission['id']}",
        headers=auth_headers(agent_token),
    )
    agent_unassigned_response = client.get(
        f"/missions/{unassigned_mission['id']}",
        headers=auth_headers(agent_token),
    )

    assert responsable_response.status_code == 200
    assert agent_assigned_response.status_code == 200
    assert agent_unassigned_response.status_code == 403


def test_get_mission_details_requires_jwt(client, admin_token, roles_services, agent_user):
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])

    response = client.get(f"/missions/{mission['id']}")

    assert response.status_code == 401


def test_get_unknown_mission_returns_404(client, admin_token):
    response = client.get(
        f"/missions/{uuid.uuid4()}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


def test_admin_can_update_mission_and_replace_services_and_assignments(
    client,
    admin_token,
    roles_services,
    agent_user,
    responsable_user,
):
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])
    updated_payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(responsable_user.id)],
    )
    updated_payload["title"] = "Updated mission title"
    updated_payload["location"] = "Updated location"
    updated_payload["priority"] = "low"

    response = client.patch(
        f"/missions/{mission['id']}",
        headers=auth_headers(admin_token),
        json=updated_payload,
    )

    assert response.status_code == 200
    data = response.get_json()["mission"]
    assert data["title"] == "Updated mission title"
    assert data["location"] == "Updated location"
    assert data["priority"] == "low"
    assert data["services"][0]["name"] == "green_spaces"
    assert data["assignments"][0]["email"] == responsable_user.email


def test_responsable_can_update_and_delete_mission(
    client,
    admin_token,
    responsable_token,
    roles_services,
    agent_user,
):
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])
    payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    payload["title"] = "Responsable updated mission"

    update_response = client.patch(
        f"/missions/{mission['id']}",
        headers=auth_headers(responsable_token),
        json=payload,
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["mission"]["title"] == "Responsable updated mission"

    delete_response = client.delete(
        f"/missions/{mission['id']}",
        headers=auth_headers(responsable_token),
    )
    assert delete_response.status_code == 200


def test_agent_cannot_update_or_delete_mission(
    client,
    admin_token,
    agent_token,
    roles_services,
    agent_user,
):
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])
    payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )

    update_response = client.patch(
        f"/missions/{mission['id']}",
        headers=auth_headers(agent_token),
        json=payload,
    )
    delete_response = client.delete(
        f"/missions/{mission['id']}",
        headers=auth_headers(agent_token),
    )

    assert update_response.status_code == 403
    assert delete_response.status_code == 403


def test_create_mission_rejects_unknown_service_inactive_user_and_admin_assignment(
    client,
    admin_token,
    roles_services,
    inactive_user,
    admin_user,
    agent_user,
):
    unknown_service_payload = mission_payload(
        service_ids=[str(uuid.uuid4())],
        assigned_user_ids=[str(agent_user.id)],
    )
    unknown_service_response = client.post(
        "/missions",
        headers=auth_headers(admin_token),
        json=unknown_service_payload,
    )
    assert unknown_service_response.status_code == 404

    inactive_user_payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(inactive_user.id)],
    )
    inactive_user_response = client.post(
        "/missions",
        headers=auth_headers(admin_token),
        json=inactive_user_payload,
    )
    assert inactive_user_response.status_code == 400

    admin_assignment_payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(admin_user.id)],
    )
    admin_assignment_response = client.post(
        "/missions",
        headers=auth_headers(admin_token),
        json=admin_assignment_payload,
    )
    assert admin_assignment_response.status_code == 400


def test_mission_list_supports_search_status_priority_service_date_and_pagination(
    client,
    admin_token,
    agent_token,
    roles_services,
    agent_user,
):
    now = datetime.now(timezone.utc)
    first_start = now + timedelta(days=1)
    second_start = now + timedelta(days=4)

    first_payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    first_payload["title"] = "Road lighting repair"
    first_payload["location"] = "North road"
    first_payload["priority"] = "high"
    first_payload["start_date"] = first_start.isoformat()
    first_payload["end_date"] = (first_start + timedelta(hours=2)).isoformat()

    second_payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    second_payload["title"] = "Park tree trimming"
    second_payload["location"] = "Central park"
    second_payload["priority"] = "low"
    second_payload["start_date"] = second_start.isoformat()
    second_payload["end_date"] = (second_start + timedelta(hours=2)).isoformat()

    first_response = client.post(
        "/missions",
        headers=auth_headers(admin_token),
        json=first_payload,
    )
    second_response = client.post(
        "/missions",
        headers=auth_headers(admin_token),
        json=second_payload,
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201
    first_id = first_response.get_json()["mission"]["id"]

    start_response = client.patch(
        f"/missions/{first_id}/status",
        headers=auth_headers(agent_token),
        json={"status": "in_progress"},
    )
    assert start_response.status_code == 200

    search_response = client.get(
        "/missions",
        headers=auth_headers(admin_token),
        query_string={"search": "lighting"},
    )
    assert search_response.status_code == 200
    assert {item["title"] for item in search_response.get_json()["items"]} == {
        "Road lighting repair"
    }

    status_response = client.get(
        "/missions",
        headers=auth_headers(admin_token),
        query_string={"status": "in_progress"},
    )
    assert status_response.status_code == 200
    assert all(item["status"] == "in_progress" for item in status_response.get_json()["items"])

    priority_response = client.get(
        "/missions",
        headers=auth_headers(admin_token),
        query_string={"priority": "low"},
    )
    assert priority_response.status_code == 200
    assert {item["title"] for item in priority_response.get_json()["items"]} == {
        "Park tree trimming"
    }

    service_response = client.get(
        "/missions",
        headers=auth_headers(admin_token),
        query_string={"service_id": str(roles_services["green_spaces"].id)},
    )
    assert service_response.status_code == 200
    assert {item["title"] for item in service_response.get_json()["items"]} == {
        "Park tree trimming"
    }

    date_response = client.get(
        "/missions",
        headers=auth_headers(admin_token),
        query_string={
            "start_date": (now + timedelta(days=3)).isoformat(),
            "end_date": (now + timedelta(days=5)).isoformat(),
        },
    )
    assert date_response.status_code == 200
    assert {item["title"] for item in date_response.get_json()["items"]} == {
        "Park tree trimming"
    }

    pagination_response = client.get(
        "/missions",
        headers=auth_headers(admin_token),
        query_string={"page": 1, "per_page": 1},
    )
    assert pagination_response.status_code == 200
    assert pagination_response.get_json()["pagination"]["per_page"] == 1
    assert len(pagination_response.get_json()["items"]) == 1


def test_mission_list_rejects_invalid_has_remark_value(client, admin_token):
    response = client.get(
        "/missions",
        headers=auth_headers(admin_token),
        query_string={"has_remark": "maybe"},
    )

    assert response.status_code == 400


def test_admin_can_update_mission_status_to_in_progress(
    client,
    admin_token,
    roles_services,
    agent_user,
):
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])

    response = client.patch(
        f"/missions/{mission['id']}/status",
        headers=auth_headers(admin_token),
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    assert response.get_json()["mission"]["status"] == "in_progress"


def test_admin_cannot_add_remark_and_agent_cannot_validate_remark(
    client,
    admin_token,
    agent_token,
    roles_services,
    agent_user,
):
    """Preserve the existing regression checks on a started mission."""
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])

    admin_remark_response = client.post(
        f"/missions/{mission['id']}/remark",
        headers=auth_headers(admin_token),
        json={"remark": "Admin should not add this remark."},
    )
    assert admin_remark_response.status_code == 403

    start_mission(client, admin_token, mission)

    agent_remark_response = client.post(
        f"/missions/{mission['id']}/remark",
        headers=auth_headers(agent_token),
        json={"remark": "Needs validation."},
    )
    assert agent_remark_response.status_code == 200

    agent_validate_response = client.post(
        f"/missions/{mission['id']}/validate",
        headers=auth_headers(agent_token),
    )
    assert agent_validate_response.status_code == 403


def test_responsable_can_add_remark_only_when_assigned(
    client,
    admin_token,
    responsable_token,
    roles_services,
    agent_user,
    responsable_user,
):
    """Preserve the existing regression checks on a started mission."""
    unassigned_mission = create_api_mission(
        client,
        admin_token,
        roles_services,
        [agent_user.id],
    )

    unassigned_response = client.post(
        f"/missions/{unassigned_mission['id']}/remark",
        headers=auth_headers(responsable_token),
        json={"remark": "Responsable is not assigned."},
    )
    assert unassigned_response.status_code == 403

    assigned_mission = create_api_mission(
        client,
        admin_token,
        roles_services,
        [responsable_user.id],
    )

    start_mission(client, admin_token, assigned_mission)

    assigned_response = client.post(
        f"/missions/{assigned_mission['id']}/remark",
        headers=auth_headers(responsable_token),
        json={"remark": "Responsable assigned remark."},
    )

    assert assigned_response.status_code == 200
    data = assigned_response.get_json()["mission"]
    assert data["remark"] == "Responsable assigned remark."
    assert data["remark_added_by"] == str(responsable_user.id)
    assert data["status"] == "remark_pending_validation"


def test_validate_mission_requires_remark_and_actual_duration(
    client,
    admin_token,
    roles_services,
    agent_user,
):
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])

    no_remark_response = client.post(
        f"/missions/{mission['id']}/validate",
        headers=auth_headers(admin_token),
    )
    assert no_remark_response.status_code == 400


def test_actual_duration_and_status_validation_errors(
    client,
    admin_token,
    agent_token,
    roles_services,
    agent_user,
):
    """Preserve the existing regression checks on a started mission."""
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])

    start_mission(client, admin_token, mission)

    duration_response = client.patch(
        f"/missions/{mission['id']}/actual-duration",
        headers=auth_headers(agent_token),
        json={"actual_duration": 0},
    )
    assert duration_response.status_code == 400

    status_response = client.patch(
        f"/missions/{mission['id']}/status",
        headers=auth_headers(agent_token),
        json={"status": "completed"},
    )
    assert status_response.status_code == 400


def test_complete_already_completed_mission_returns_409(
    client,
    admin_token,
    agent_token,
    roles_services,
    agent_user,
):
    """Preserve the existing regression checks on a started mission."""
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])

    start_mission(client, admin_token, mission)

    duration_response = client.patch(
        f"/missions/{mission['id']}/actual-duration",
        headers=auth_headers(agent_token),
        json={"actual_duration": 2},
    )
    assert duration_response.status_code == 200

    first_complete_response = client.post(
        f"/missions/{mission['id']}/complete",
        headers=auth_headers(agent_token),
    )
    assert first_complete_response.status_code == 200

    second_complete_response = client.post(
        f"/missions/{mission['id']}/complete",
        headers=auth_headers(agent_token),
    )
    assert second_complete_response.status_code == 409


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("page", "abc", "integer"),
        ("per_page", "abc", "integer"),
        ("page", "", "integer"),
        ("per_page", "", "integer"),
        ("page", "1.5", "integer"),
        ("per_page", "1.5", "integer"),
        ("page", "0", "greater than or equal to 1"),
        ("page", "-1", "greater than or equal to 1"),
        ("per_page", "0", "greater than or equal to 1"),
        ("per_page", "-1", "greater than or equal to 1"),
        ("per_page", "101", "less than or equal to 100"),
    ],
)
def test_missions_reject_invalid_pagination_before_repository(
    client, admin_token, monkeypatch, field, value, message,
):
    """Reject invalid pagination before offset, limit, or total-page arithmetic."""
    repository_lookup = Mock(side_effect=AssertionError("Repository must not be called"))
    monkeypatch.setattr(MissionRepository, "list_filtered", repository_lookup)

    response = client.get(
        "/missions", headers=auth_headers(admin_token), query_string={field: value}
    )

    assert response.status_code == 400
    error = response.get_json()["error"].lower()
    assert field.replace("_", " ") in error.replace("_", " ")
    assert message in error
    repository_lookup.assert_not_called()


@pytest.mark.parametrize("per_page", [1, 10, 100])
def test_missions_accept_valid_pagination(
    client, admin_token, roles_services, agent_user, per_page,
):
    """Preserve pagination metadata and results at both page-size boundaries."""
    mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])
    response = client.get(
        "/missions", headers=auth_headers(admin_token),
        query_string={"page": 1, "per_page": per_page},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert set(data) == {"items", "pagination"}
    assert data["pagination"] == {
        "page": 1, "per_page": per_page, "total_items": 1, "total_pages": 1,
    }
    assert [item["id"] for item in data["items"]] == [mission["id"]]


@pytest.mark.parametrize("field", ["start_date", "end_date"])
@pytest.mark.parametrize("value", ["banana", "", "2026-02-30T09:00:00"])
def test_missions_reject_malformed_date_filters(client, admin_token, field, value):
    """Reject malformed or explicitly empty filters instead of ignoring them."""
    response = client.get(
        "/missions", headers=auth_headers(admin_token), query_string={field: value}
    )

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert field in error
    assert "ISO" in error


def mission_snapshots(app):
    """Read persisted missions and their relationships in an independent session."""
    with app.app_context():
        return {
            str(mission.id): mission.to_dict(include_relations=True)
            for mission in Mission.query.all()
        }


@pytest.mark.parametrize("method", ["POST", "PATCH"])
@pytest.mark.parametrize(
    "dates,message",
    [
        ({"start_date": "banana"}, "start_date"),
        ({"end_date": "not-a-date"}, "end_date"),
        ({"start_date": ""}, "start_date"),
        ({"end_date": ""}, "end_date"),
        ({"start_date": "2026-02-30T09:00:00"}, "start_date"),
        ({"end_date": "2026-02-30T09:00:00"}, "end_date"),
        ({"start_date": "2026-09-14T09:00:00+00:00",
          "end_date": "2026-09-14T12:00:00"}, "timezone"),
        ({"start_date": "2026-09-14T09:00:00",
          "end_date": "2026-09-14T12:00:00+00:00"}, "timezone"),
        ({"start_date": "2026-09-15T09:00:00+00:00",
          "end_date": "2026-09-14T12:00:00+00:00"}, "greater than or equal"),
    ],
)
def test_invalid_mission_dates_do_not_mutate_data(
    app, client, admin_token, roles_services, agent_user, responsable_user,
    method, dates, message,
):
    """Reject invalid dates before creating rows or changing fields and relationships."""
    path = "/missions"
    if method == "PATCH":
        mission = create_api_mission(client, admin_token, roles_services, [agent_user.id])
        path = f"/missions/{mission['id']}"
    before = mission_snapshots(app)
    payload = mission_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(responsable_user.id)],
    )
    payload.update(title="Must not be persisted", location="Must not change", **dates)

    response = client.open(path, method=method, headers=auth_headers(admin_token), json=payload)

    assert response.status_code == 400
    assert message in response.get_json()["error"]
    assert mission_snapshots(app) == before
    assert not db.session.new
    assert not db.session.dirty


@pytest.mark.parametrize(
    "start,end",
    [
        ("2026-09-14T09:00:00+00:00", "2026-09-14T12:00:00+00:00"),
        ("2026-09-14T09:00:00+02:00", "2026-09-14T12:00:00+02:00"),
        ("2026-09-14T09:00:00Z", "2026-09-14T12:00:00Z"),
        ("2026-09-14T09:00:00", "2026-09-14T12:00:00"),
        ("2026-09-14 09:00:00.123456", "2026-09-14 12:00:00.123456"),
        ("2026-09-14", "2026-09-14"),
    ],
)
def test_existing_iso_formats_work_for_create_update_and_filters(
    client, admin_token, roles_services, agent_user, start, end,
):
    """Keep accepted aware, naive, date-only, and fractional ISO inputs working."""
    mission = create_api_mission(
        client, admin_token, roles_services, [agent_user.id],
        start_date=start, end_date=end,
    )
    payload = mission_payload(
        service_ids=[str(roles_services["roads"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    payload.update(title="Valid date update", start_date=start, end_date=end)
    response = client.patch(
        f"/missions/{mission['id']}", headers=auth_headers(admin_token), json=payload
    )
    assert response.status_code == 200
    assert response.get_json()["mission"]["title"] == "Valid date update"

    for filters in ({"start_date": start}, {"end_date": end},
                    {"start_date": start, "end_date": end}):
        response = client.get(
            "/missions", headers=auth_headers(admin_token), query_string=filters
        )
        assert response.status_code == 200
        assert [item["id"] for item in response.get_json()["items"]] == [mission["id"]]
