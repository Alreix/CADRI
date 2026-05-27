from app.extensions import db
from app.models.base_model import BaseModel
from app.utils.security import check_password, hash_password


class User(BaseModel):
    """Representation of a CADRI user account.

    Fields capture the user's identity, authentication data and organizational
    attachments (role and service). Methods provide small convenience helpers
    used by the authentication and account management layers.
    """

    __tablename__ = "users"

    # Basic identity fields
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=True)

    # Business relations: role and primary service (department)
    role_id = db.Column(
        db.ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_id = db.Column(
        db.ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Activation and status
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    activated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ORM relationships (reverse sides defined on Role and Service)
    role = db.relationship("Role", back_populates="users")
    service = db.relationship("Service", back_populates="users")

    def set_password(self, password: str) -> None:
        """Hash and store a plaintext password.

        Use the project security helper so hashing configuration stays centralized.
        """

        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Return True if the provided password matches the stored hash."""

        if not self.password_hash:
            return False
        return check_password(password, self.password_hash)

    def activate_account(self) -> None:
        """Mark the account as active (used after email activation)."""

        self.is_active = True

    def update_profile(self, first_name: str | None = None, last_name: str | None = None, email: str | None = None) -> None:
        """Update mutable profile fields while preserving role/service.

        Only the provided non-None arguments are applied so callers can update a
        single field without clearing others.
        """

        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if email is not None:
            self.email = email

    def __repr__(self) -> str:
        return f"<User {self.email}>"
