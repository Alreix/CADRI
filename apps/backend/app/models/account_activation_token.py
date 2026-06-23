from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.base_model import BaseModel
from app.utils.tokens import generate_raw_token, hash_token


class AccountActivationToken(BaseModel):
    """Single-use activation token used to secure CADRI account setup.

    The CADRI documentation requires activation links to expire after 24 hours.
    This model stores the hashed token, the expiration timestamp, and the time
    at which the token was consumed so the activation flow can enforce those
    business rules reliably.
    """

    __tablename__ = "account_activation_tokens"

    user_id = db.Column(
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Back reference kept plural because one user can receive multiple activation attempts.
    user = db.relationship("User", backref="account_activation_tokens")

    @classmethod
    def create_for_user(cls, user_id: int, expires_in_hours: int = 24):
        """Create a new token record and return it with the raw token string.

        The raw token is only needed once for building the email link. The
        database stores only the hashed representation for security.
        """

        raw_token = generate_raw_token()
        token = cls(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
        )
        return token, raw_token

    def is_expired(self) -> bool:
        """Return True when the activation token can no longer be used."""

        return datetime.now(timezone.utc) > self.expires_at

    def is_used(self) -> bool:
        """Return True if the token has already been consumed."""

        return self.used_at is not None

    def verify_token(self, raw_token: str) -> bool:
        """Check whether the provided raw token matches the stored hash."""

        return self.token_hash == hash_token(raw_token)

    def mark_as_used(self) -> None:
        """Mark the token as consumed at the current UTC time."""

        self.used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a compact debug representation without exposing token data."""
        return f"<AccountActivationToken user_id={self.user_id}>"
