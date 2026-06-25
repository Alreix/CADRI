"""Unit tests for model-level behavior."""

from app.models.mission import Mission
from app.utils.constants import MISSION_STATUS_COMPLETED


def test_user_password_hashing(admin_user):
    assert admin_user.password_hash is not None
    assert admin_user.password_hash != "StrongPass1"
    assert admin_user.check_password("StrongPass1") is True
    assert admin_user.check_password("WrongPass1") is False


def test_user_to_dict_contains_role_and_service(admin_user):
    data = admin_user.to_dict(include_timestamps=True)

    assert data["email"] == admin_user.email
    assert data["role"]["name"] == "admin"
    assert data["service"]["name"] == "green_spaces"
    assert "created_at" in data
    assert "updated_at" in data


def test_mission_complete_sets_status_and_completed_at(admin_user):
    mission = Mission(
        title="Test mission",
        intervention_type="Maintenance",
        location="Town hall",
        description="Basic test mission",
        planned_agents_count=1,
        estimated_duration=1.0,
        start_date="2026-06-12T10:00:00+00:00",
        end_date="2026-06-12T12:00:00+00:00",
        priority="high",
        signage_required=False,
        created_by=admin_user.id,
    )

    mission.complete_mission()

    assert mission.status == MISSION_STATUS_COMPLETED
    assert mission.completed_at is not None
