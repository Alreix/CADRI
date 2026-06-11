"""Mission-service association model."""

from app.extensions import db
from app.models.base_model import BaseModel


class MissionServiceLink(BaseModel):
    """Represent the association between a mission and a service."""

    __tablename__ = "mission_service_links"

    __table_args__ = (
        db.UniqueConstraint("mission_id", "service_id", name="uq_mission_service_link"),
    )

    mission_id = db.Column(
        db.ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_id = db.Column(
        db.ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )

    mission = db.relationship("Mission", back_populates="services")
    service = db.relationship("Service", lazy=True)
