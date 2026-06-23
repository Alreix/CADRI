from app.extensions import db
from app.models.base_model import BaseModel


class Service(BaseModel):
    """Organizational service (department) within CADRI.

    Services represent municipal departments or business units that users are
    attached to. They are used to scope missions and to filter assignable users
    in the UI and APIs.
    """

    __tablename__ = "services"

    name = db.Column(db.String(100), nullable=False, unique=True)
    # Human-friendly label for UI lists and filters
    label = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Reverse relationship: list users that belong to this service
    users = db.relationship("User", back_populates="service", lazy=True)

    def __repr__(self) -> str:
        """Return a compact debug representation for the service."""
        return f"<Service {self.name}>"
