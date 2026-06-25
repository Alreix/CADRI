"""Mission helper functions used by service and route tests."""

from datetime import datetime, timedelta, timezone

from app.utils.constants import MISSION_PRIORITY_HIGH


def mission_payload(service_ids: list[str], assigned_user_ids: list[str]) -> dict:
    """Return a valid JSON payload for the mission API."""
    start_date = datetime.now(timezone.utc) + timedelta(days=1)
    end_date = start_date + timedelta(hours=2)

    return {
        "title": "Repair street lighting",
        "intervention_type": "Electrical maintenance",
        "location": "Main street",
        "description": "Replace damaged lights and secure the area.",
        "planned_agents_count": 1,
        "estimated_duration": 2.5,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "priority": MISSION_PRIORITY_HIGH,
        "required_equipment": "Ladder, safety cones",
        "signage_required": True,
        "service_ids": service_ids,
        "assigned_user_ids": assigned_user_ids,
    }


def mission_service_payload(service_ids: list[str], assigned_user_ids: list[str]) -> dict:
    """Return a valid Python payload for MissionService tests."""
    payload = mission_payload(service_ids, assigned_user_ids)
    payload["start_date"] = datetime.fromisoformat(payload["start_date"])
    payload["end_date"] = datetime.fromisoformat(payload["end_date"])
    return payload
