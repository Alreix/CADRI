"""Mission assignment model."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.base_model import BaseModel


class MissionAssignment(BaseModel):
    """Represent the assignment of a user to a mission."""

    __tablename__ = "mission_assignments"

    mission_id = db.Column(
        db.ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    mission = db.relationship("Mission", back_populates="assignments")
    user = db.relationship("User", lazy=True)
