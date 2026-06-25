"""Repository for mission assignment persistence operations."""

from app.extensions import db
from app.models.mission_assignment import MissionAssignment


class MissionAssignmentRepository:
    """Centralize mission assignment access."""

    @staticmethod
    def create(assignment: MissionAssignment) -> MissionAssignment:
        """Persist a mission assignment."""
        db.session.add(assignment)
        db.session.flush()
        return assignment

    @staticmethod
    def remove_for_mission(mission_id) -> None:
        """Remove all assignments linked to a mission."""
        MissionAssignment.query.filter_by(mission_id=mission_id).delete()
        db.session.flush()

