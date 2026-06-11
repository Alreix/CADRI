"""Integration tests for MissionService business rules."""

from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models.mission_assignment import MissionAssignment
from app.models.mission_service_link import MissionServiceLink
from app.repositories.mission_repository import MissionRepository
from app.repositories.user_repository import UserRepository
from app.services.mission_service import MissionService
from app.utils.exceptions import AuthorizationError, ConflictError, ValidationError


def mission_payload(*, service_ids, assigned_user_ids, title="Service mission"):
    start_date = datetime.now(timezone.utc) + timedelta(days=1)
    end_date = start_date + timedelta(hours=2)

    return {
        "title": title,
        "intervention_type": "Maintenance",
        "location": "Town center",
        "description": "Mission created by service tests.",
        "planned_agents_count": 1,
        "estimated_duration": 2,
        "start_date": start_date,
        "end_date": end_date,
        "priority": "medium",
        "required_equipment": "Standard tools",
        "signage_required": False,
        "service_ids": service_ids,
        "assigned_user_ids": assigned_user_ids,
    }


def get_user(user_namespace):
    return UserRepository.get_by_id(user_namespace.id)


def create_service_mission(current_user, roles_services, agent_user, **overrides):
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )
    payload.update(overrides)
    return MissionService.create_mission(current_user, payload)


def test_create_mission_persists_services_assignments_and_creator(
    admin_user,
    roles_services,
    agent_user,
):
    admin = get_user(admin_user)

    mission = create_service_mission(admin, roles_services, agent_user)

    assert mission.id is not None
    assert mission.created_by == admin.id
    assert mission.status == "to_do"
    assert MissionServiceLink.query.filter_by(mission_id=mission.id).count() == 1
    assert MissionAssignment.query.filter_by(mission_id=mission.id).count() == 1


def test_agent_cannot_create_mission(agent_user, roles_services):
    agent = get_user(agent_user)
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )

    with pytest.raises(AuthorizationError):
        MissionService.create_mission(agent, payload)


def test_create_mission_rejects_empty_services(admin_user, agent_user):
    admin = get_user(admin_user)
    payload = mission_payload(service_ids=[], assigned_user_ids=[str(agent_user.id)])

    with pytest.raises(ValidationError):
        MissionService.create_mission(admin, payload)


def test_create_mission_rejects_invalid_date_order(admin_user, roles_services, agent_user):
    admin = get_user(admin_user)
    start_date = datetime.now(timezone.utc) + timedelta(days=2)
    end_date = datetime.now(timezone.utc) + timedelta(days=1)
    payload = mission_payload(
        service_ids=[str(roles_services["roads_id"])],
        assigned_user_ids=[str(agent_user.id)],
    )
    payload["start_date"] = start_date
    payload["end_date"] = end_date

    with pytest.raises(ValidationError):
        MissionService.create_mission(admin, payload)


def test_agent_assigned_to_mission_can_update_duration(
    admin_user,
    agent_user,
    roles_services,
):
    admin = get_user(admin_user)
    agent = get_user(agent_user)
    mission = create_service_mission(admin, roles_services, agent_user)

    updated = MissionService.update_actual_duration(agent, mission.id, 4)

    assert float(updated.actual_duration) == 4


def test_agent_not_assigned_to_mission_cannot_update_duration(
    admin_user,
    agent_user,
    responsable_user,
    roles_services,
):
    admin = get_user(admin_user)
    agent = get_user(agent_user)
    mission = create_service_mission(
        admin,
        roles_services,
        agent_user,
        assigned_user_ids=[str(responsable_user.id)],
    )

    with pytest.raises(AuthorizationError):
        MissionService.update_actual_duration(agent, mission.id, 4)


def test_agent_adds_remark_and_mission_waits_for_validation(
    admin_user,
    agent_user,
    roles_services,
):
    admin = get_user(admin_user)
    agent = get_user(agent_user)
    mission = create_service_mission(admin, roles_services, agent_user)

    MissionService.update_actual_duration(agent, mission.id, 2)
    updated = MissionService.add_remark(agent, mission.id, "Problem on site")

    assert updated.remark == "Problem on site"
    assert updated.status == "remark_pending_validation"
    assert updated.remark_added_by == agent.id


def test_agent_cannot_add_second_remark(admin_user, agent_user, roles_services):
    admin = get_user(admin_user)
    agent = get_user(agent_user)
    mission = create_service_mission(admin, roles_services, agent_user)

    MissionService.add_remark(agent, mission.id, "First remark")

    with pytest.raises(ConflictError):
        MissionService.add_remark(agent, mission.id, "Second remark")


def test_mission_with_remark_is_completed_after_validation(
    admin_user,
    agent_user,
    roles_services,
):
    admin = get_user(admin_user)
    agent = get_user(agent_user)
    mission = create_service_mission(admin, roles_services, agent_user)

    MissionService.update_actual_duration(agent, mission.id, 2)
    MissionService.add_remark(agent, mission.id, "Needs review")

    validated = MissionService.validate_mission(admin, mission.id)

    assert validated.validated_by == admin.id
    assert validated.validated_at is not None
    assert validated.status == "completed"
    assert validated.completed_at is not None


def test_complete_mission_requires_actual_duration(admin_user, agent_user, roles_services):
    admin = get_user(admin_user)
    agent = get_user(agent_user)
    mission = create_service_mission(admin, roles_services, agent_user)

    with pytest.raises(ValidationError):
        MissionService.complete_mission(agent, mission.id)


def test_list_missions_filters_by_assignment_and_remark(
    admin_user,
    agent_user,
    responsable_user,
    roles_services,
):
    admin = get_user(admin_user)
    agent = get_user(agent_user)

    mission_with_remark = create_service_mission(
        admin,
        roles_services,
        agent_user,
        title="With remark",
    )
    create_service_mission(
        admin,
        roles_services,
        agent_user,
        title="Without remark",
        assigned_user_ids=[str(responsable_user.id)],
    )

    MissionService.update_actual_duration(agent, mission_with_remark.id, 2)
    MissionService.add_remark(agent, mission_with_remark.id, "Remark")

    missions, total = MissionService.list_missions(
        agent,
        my_missions_only=True,
        has_remark=True,
    )

    assert total == 1
    assert missions[0].title == "With remark"


def test_delete_mission_removes_assignments_and_service_links(
    admin_user,
    agent_user,
    roles_services,
):
    admin = get_user(admin_user)
    mission = create_service_mission(admin, roles_services, agent_user)
    mission_id = mission.id

    MissionService.delete_mission(admin, mission_id)

    assert MissionRepository.get_by_id(mission_id) is None
    assert MissionAssignment.query.filter_by(mission_id=mission_id).count() == 0
    assert MissionServiceLink.query.filter_by(mission_id=mission_id).count() == 0
