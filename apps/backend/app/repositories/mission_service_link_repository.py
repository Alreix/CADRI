"""Repository for mission-service link persistence operations."""

from app.extensions import db
from app.models.mission_service_link import MissionServiceLink


class MissionServiceLinkRepository:
    """Centralize mission-service association access."""

    @staticmethod
    def create(link: MissionServiceLink) -> MissionServiceLink:
        """Persist a mission-service link."""
        db.session.add(link)
        db.session.flush()
        return link

    @staticmethod
    def remove_for_mission(mission_id) -> None:
        """Remove all services linked to a mission."""
        MissionServiceLink.query.filter_by(mission_id=mission_id).delete()
        db.session.flush()

