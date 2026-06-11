"""Integration tests for MissionService."""

import pytest

from app.services.mission_service import MissionService
from app.utils.exceptions import AuthorizationError, ValidationError
from tests.helpers.mission_helpers import mission_service_payload


def test_admin_can_create_mission_with_services_and_assignments(admin_user, agent_user, roles_services):
    payload = mission_service_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )

    mission = MissionService.create_mission(admin_user, payload)

    assert mission.id is not None
    assert mission.created_by == admin_user.id
    assert len(mission.services) == 1
    assert len(mission.assignments) == 1


def test_agent_cannot_create_mission(agent_user, roles_services):
    payload = mission_service_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )

    with pytest.raises(AuthorizationError):
        MissionService.create_mission(agent_user, payload)


def test_create_mission_rejects_empty_services(admin_user, agent_user):
    payload = mission_service_payload(service_ids=[], assigned_user_ids=[str(agent_user.id)])

    with pytest.raises(ValidationError):
        MissionService.create_mission(admin_user, payload)


def test_agent_not_assigned_cannot_act_on_mission(admin_user, agent_user, other_agent_user, roles_services):
    payload = mission_service_payload(
        service_ids=[str(roles_services["green_spaces"].id)],
        assigned_user_ids=[str(agent_user.id)],
    )
    mission = MissionService.create_mission(admin_user, payload)

    with pytest.raises(AuthorizationError):
        MissionService.update_actual_duration(other_agent_user, mission.id, 2.0)
