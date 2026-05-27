from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.base_model import BaseModel
from app.utils.tokens import generate_raw_token, hash_token


class RefreshToken(BaseModel):
    """Long-lived refresh token record for user session management.

    Refresh tokens are stored as hashed values and can be revoked or rotated.
    Rotation records the hash of the replacing token so old tokens can be
    invalidated while preserving an audit trail. By default refresh tokens are
    valid for 7 days but this can be adjusted when creating the token.
    """

    __tablename__ = "refresh_tokens"

    user_id = db.Column(
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    replaced_by_token_hash = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", backref="refresh_tokens")

    @classmethod
    def create_for_user(cls, user_id: int, expires_in_days: int = 7) -> tuple["RefreshToken", str]:
        """Create a new refresh token instance and return (token_obj, raw_token).

        The raw token should be delivered to the client (for example in a
        secure HTTP-only cookie). Only the hashed token is persisted to the DB.
        """

        raw_token = generate_raw_token()
        token = cls(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        )
        return token, raw_token

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_replaced(self) -> bool:
        return self.replaced_by_token_hash is not None

    def is_valid(self) -> bool:
        """Return True if the token may be used for issuing a new access token."""

        return not self.is_expired() and not self.is_revoked() and not self.is_replaced()

    def verify_token(self, raw_token: str) -> bool:
        return self.token_hash == hash_token(raw_token)

    def revoke(self) -> None:
        """Revoke the token immediately (used when a session is terminated)."""

        self.revoked_at = datetime.now(timezone.utc)

    def rotate(self, new_raw_token: str) -> None:
        """Rotate this token: record the replacing token's hash and revoke.

        Rotation records the hash of the new token so this record becomes
        explicitly replaced and cannot be used again. Callers should persist the
        new token record and deliver its raw value to the client.
        """

        self.replaced_by_token_hash = hash_token(new_raw_token)
        self.revoke()

    def __repr__(self) -> str:
        return f"<RefreshToken user_id={self.user_id}>"