from app.extensions import db
from app.models.base_model import BaseModel
from app.utils.security import check_password, hash_password


class User(BaseModel):
    """Representation of a CADRI user account."""

    __tablename__ = "users"

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=True)

    role_id = db.Column(
        db.ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_id = db.Column(
        db.ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
    )

    is_active = db.Column(db.Boolean, nullable=False, default=False)
    activated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    role = db.relationship("Role", back_populates="users")
    service = db.relationship("Service", back_populates="users")

    def set_password(self, password: str) -> None:
        """Hash and store a new password for the user."""
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Return True when the provided password matches the stored hash."""
        if not self.password_hash:
            return False
        return check_password(password, self.password_hash)

    def activate_account(self) -> None:
        """Mark the user account as active."""
        self.is_active = True

    def update_profile(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> None:
        """Update profile fields that were explicitly provided."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if email is not None:
            self.email = email

    def to_dict(self, include_timestamps: bool = False) -> dict:
        """Serialize the user with role and service data for API responses."""
        data = {
            "id": str(self.id) if self.id else None,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "role": (
                {
                    "id": str(self.role.id) if self.role and self.role.id else None,
                    "name": self.role.name,
                    "label": self.role.label,
                }
                if self.role
                else None
            ),
            "service": (
                {
                    "id": str(self.service.id) if self.service and self.service.id else None,
                    "name": self.service.name,
                    "label": self.service.label,
                }
                if self.service
                else None
            ),
            "is_active": self.is_active,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }

        if include_timestamps:
            data["created_at"] = self.created_at.isoformat() if self.created_at else None
            data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None

        return data

    def __repr__(self) -> str:
        """Return a compact debug representation for logs and shells."""
        return f"<User {self.email}>"
