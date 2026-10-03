"""Persistence model for explicitly revoked access-token identifiers."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.base_model import BaseModel


class TokenBlocklist(BaseModel):
    """Store the minimal metadata needed to reject a revoked access JWT."""

    __tablename__ = "token_blocklist"

    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    user_id = db.Column(
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_type = db.Column(db.String(20), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship("User", backref="blocked_access_tokens")

    def __repr__(self) -> str:
        """Return a debug representation that never exposes a raw token."""

        return f"<TokenBlocklist jti={self.jti}>"
