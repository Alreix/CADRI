"""Repository helpers for password reset token persistence.

The password recovery flow uses these methods to look up, create, and commit
token records while keeping database access logic centralized.
"""

from app.extensions import db
from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    """Data-access helpers for `PasswordResetToken` records."""

    @staticmethod
    def get_by_id(token_id):
        """Return the password reset token with the given primary key, if any."""

        return PasswordResetToken.query.get(token_id)

    @staticmethod
    def get_by_token_hash(token_hash):
        """Return the password reset token matching the stored hash."""

        return PasswordResetToken.query.filter_by(token_hash=token_hash).first()

    @staticmethod
    def get_latest_for_user(user_id):
        """Return the most recently created password reset token for a user."""

        return (
            PasswordResetToken.query
            .filter_by(user_id=user_id)
            .order_by(PasswordResetToken.created_at.desc())
            .first()
        )
    
    @staticmethod
    def invalidate_unused_tokens_for_user(user_id):
        """Invalidate unused tokens for user."""
        tokens = PasswordResetToken.query.filter_by(user_id=user_id).all()
        for token in tokens:
            if not token.is_used():
                token.mark_as_used()
        db.session.commit()

    @staticmethod
    def create(token):
        """Persist a new password reset token and return it."""

        db.session.add(token)
        db.session.commit()
        return token

    @staticmethod
    def update():
        """Commit pending changes for password reset token records."""

        db.session.commit()
