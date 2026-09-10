"""Repository helpers for refresh token persistence.

These methods encapsulate the refresh-token data access pattern used by the
session and authentication layers.
"""

from app.extensions import db
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Data-access helpers for `RefreshToken` records."""

    @staticmethod
    def get_by_id(token_id):
        """Return the refresh token with the given primary key, if any."""

        return RefreshToken.query.get(token_id)

    @staticmethod
    def get_by_token_hash(token_hash):
        """Return the refresh token matching the stored token hash."""

        return RefreshToken.query.filter_by(token_hash=token_hash).first()

    @staticmethod
    def get_by_token_hash_fresh(token_hash):
        """Re-read a refresh token from the database after its user lock is held."""

        return (
            RefreshToken.query
            .populate_existing()
            .filter_by(token_hash=token_hash)
            .first()
        )

    @staticmethod
    def get_latest_for_user(user_id):
        """Return the most recently created refresh token for a user."""

        return (
            RefreshToken.query
            .filter_by(user_id=user_id)
            .order_by(RefreshToken.created_at.desc())
            .first()
        )

    @staticmethod
    def revoke_all_for_user(user_id, *, commit: bool = True):
        """Revoke every refresh token currently linked to a user.

        This is typically used when a session must be invalidated globally,
        for example after a password change, an account compromise, or a
        forced logout across devices. A caller may defer the commit when these
        changes belong to a larger atomic security operation.
        """

        tokens = RefreshToken.query.filter_by(user_id=user_id).all()
        for token in tokens:
            if not token.is_revoked():
                token.revoke()
        if commit:
            db.session.commit()
        else:
            db.session.flush()

    @staticmethod
    def create(token, *, commit: bool = True):
        """Stage a refresh token and optionally commit the current transaction."""

        db.session.add(token)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
        return token

    @staticmethod
    def update(*, commit: bool = True):
        """Flush refresh-token changes and optionally commit the transaction."""

        if commit:
            db.session.commit()
        else:
            db.session.flush()
