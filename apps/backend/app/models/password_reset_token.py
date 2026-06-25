from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.base_model import BaseModel
from app.utils.tokens import generate_raw_token, hash_token


class PasswordResetToken(BaseModel):
    """One-time password reset token for CADRI's password recovery flow.

    This model stores only a hashed representation of the token, an expiry
    timestamp and the time when the token was consumed. By default the token
    expires after 2 hours which provides a balance between user convenience
    and security; adjust `expires_in_hours` when calling
    `create_for_user` if a different policy is desired.
    """

    __tablename__ = "password_reset_tokens"

    user_id = db.Column(
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Back reference for convenience when querying a user's tokens
    user = db.relationship("User", backref="password_reset_tokens")

    @classmethod
    def create_for_user(cls, user_id: int, expires_in_hours: int = 2) -> tuple["PasswordResetToken", str]:
        """Create a token instance and return (token_obj, raw_token).

        The raw token is returned so the caller can embed it in the password
        reset email. Only the hashed value is stored in the database.
        """

        raw_token = generate_raw_token()
        token = cls(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        return token, raw_token

    def is_expired(self) -> bool:
        """Return True when the token has passed its expiration timestamp."""

        return datetime.now(timezone.utc) > self.expires_at

    def is_used(self) -> bool:
        """Return True if the token has already been consumed."""

        return self.used_at is not None

    def verify_token(self, raw_token: str) -> bool:
        """Verify whether the provided raw token matches the stored hash."""

        return self.token_hash == hash_token(raw_token)

    def mark_as_used(self) -> None:
        """Mark the token as consumed now (UTC)."""

        self.used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a compact debug representation without exposing token data."""
        return f"<PasswordResetToken user_id={self.user_id}>"
