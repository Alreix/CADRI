from app.extensions import db
from app.models.base_model import BaseModel

class Role(BaseModel):
    """Authorization role used to group permissions and access levels in CADRI.

    Roles represent the business identities used throughout the application,
    such as admin, manager, and agent. They let the authorization layer apply
    consistent rules without storing duplicated permission flags on each user.
    """

    __tablename__ = "roles"

    name = db.Column(db.String(50), nullable=False, unique=True)
    label = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Expose all users attached to the same role for administration and auditing.
    users = db.relationship("User", back_populates="role", lazy=True)

    def __repr__(self) -> str:
        """Return a compact debug representation for the role."""
        return f"<Role {self.name}>"
