"""Application facade for mission-related use cases."""

from app.services.mission_service import MissionService


class MissionFacade:
    """Expose mission use cases to the route layer."""

    @staticmethod
    def create_mission(current_user, payload: dict):
        """Create a complete mission."""
        return MissionService.create_mission(current_user, payload)

    @staticmethod
    def list_missions(current_user, **filters):
        """Return missions with filters and pagination."""
        return MissionService.list_missions(current_user, **filters)

    @staticmethod
    def get_mission_details(current_user, mission_id):
        """Return all information for a mission."""
        return MissionService.get_mission_details(current_user, mission_id)

    @staticmethod
    def update_mission(current_user, mission_id, payload: dict):
        """Update editable mission fields."""
        return MissionService.update_mission(current_user, mission_id, payload)

    @staticmethod
    def update_status(current_user, mission_id, new_status: str):
        """Update mission status."""
        return MissionService.update_status(current_user, mission_id, new_status)

    @staticmethod
    def update_actual_duration(current_user, mission_id, actual_duration: float):
        """Update actual duration."""
        return MissionService.update_actual_duration(
            current_user,
            mission_id,
            actual_duration,
        )

    @staticmethod
    def add_remark(current_user, mission_id, remark: str):
        """Add a remark to a mission."""
        return MissionService.add_remark(current_user, mission_id, remark)

    @staticmethod
    def validate_mission(current_user, mission_id):
        """Validate a mission containing a remark."""
        return MissionService.validate_mission(current_user, mission_id)

    @staticmethod
    def complete_mission(current_user, mission_id):
        """Complete a mission if conditions are met."""
        return MissionService.complete_mission(current_user, mission_id)

    @staticmethod
    def delete_mission(current_user, mission_id):
        """Delete a mission."""
        return MissionService.delete_mission(current_user, mission_id)
