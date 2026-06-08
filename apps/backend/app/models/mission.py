"""Mission model for the CADRI backend."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.base_model import BaseModel


class Mission(BaseModel):
    """Represent a field intervention mission."""

    __tablename__ = "missions"

    title = db.Column(db.String(255), nullable=False)
    intervention_type = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)

    planned_agents_count = db.Column(db.Integer, nullable=False)
    estimated_duration = db.Column(db.Numeric(10, 2), nullable=False)

    start_date = db.Column(db.DateTime(timezone=True), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True), nullable=False)

    priority = db.Column(db.String(50), nullable=False)
    required_equipment = db.Column(db.Text, nullable=True)
    signage_required = db.Column(db.Boolean, nullable=False, default=False)

    status = db.Column(db.String(50), nullable=False, default="to_do")
    actual_duration = db.Column(db.Numeric(10, 2), nullable=True)

    remark = db.Column(db.Text, nullable=True)
    remark_added_by = db.Column(
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    remark_added_at = db.Column(db.DateTime(timezone=True), nullable=True)

    validated_by = db.Column(
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    validated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_by = db.Column(
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    creator = db.relationship("User", foreign_keys=[created_by], lazy=True)
    remark_author = db.relationship("User", foreign_keys=[remark_added_by], lazy=True)
    validator = db.relationship("User", foreign_keys=[validated_by], lazy=True)

    services = db.relationship(
        "MissionServiceLink",
        back_populates="mission",
        cascade="all, delete-orphan",
        lazy=True,
    )
    assignments = db.relationship(
        "MissionAssignment",
        back_populates="mission",
        cascade="all, delete-orphan",
        lazy=True,
    )

    def update_status(self, new_status: str) -> None:
        """Update the mission status."""
        self.status = new_status

    def update_actual_duration(self, actual_duration: float) -> None:
        """Update the actual duration."""
        self.actual_duration = actual_duration

    def add_remark(self, remark: str, author_id) -> None:
        """Attach a remark to the mission."""
        self.remark = remark
        self.remark_added_by = author_id
        self.remark_added_at = datetime.now(timezone.utc)

    def validate_mission(self, validator_id) -> None:
        """Mark the mission as validated."""
        self.validated_by = validator_id
        self.validated_at = datetime.now(timezone.utc)

    def complete_mission(self) -> None:
        """Mark the mission as completed."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = "completed"

    def to_dict(self, include_relations: bool = False) -> dict:
        """Serialize the mission."""
        data = {
            "id": str(self.id),
            "title": self.title,
            "intervention_type": self.intervention_type,
            "location": self.location,
            "description": self.description,
            "planned_agents_count": self.planned_agents_count,
            "estimated_duration": float(self.estimated_duration),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "priority": self.priority,
            "required_equipment": self.required_equipment,
            "signage_required": self.signage_required,
            "status": self.status,
            "actual_duration": (
                float(self.actual_duration) if self.actual_duration is not None else None
            ),
            "remark": self.remark,
            "remark_added_by": (
                str(self.remark_added_by) if self.remark_added_by else None
            ),
            "remark_added_at": (
                self.remark_added_at.isoformat() if self.remark_added_at else None
            ),
            "validated_by": str(self.validated_by) if self.validated_by else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_relations:
            data["services"] = [
                service_link.service.to_dict() for service_link in self.services
            ]
            data["assignments"] = [
                assignment.user.to_dict() for assignment in self.assignments
            ]

        return data
