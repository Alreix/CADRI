"""Repository helpers for account activation token persistence.

These methods keep query logic centralized so the activation workflow can
create, fetch, and update tokens without duplicating database access code.
"""

from app.extensions import db
from app.models.account_activation_token import AccountActivationToken


class AccountActivationTokenRepository:
    """Data-access helpers for `AccountActivationToken` records."""

    @staticmethod
    def get_by_id(token_id):
        """Return the activation token with the given primary key, if any."""

        return AccountActivationToken.query.get(token_id)

    @staticmethod
    def get_by_token_hash(token_hash):
        """Return the activation token matching the stored token hash."""

        return AccountActivationToken.query.filter_by(token_hash=token_hash).first()

    @staticmethod
    def get_latest_for_user(user_id):
        """Return the most recently created activation token for a user."""

        return (
            AccountActivationToken.query
            .filter_by(user_id=user_id)
            .order_by(AccountActivationToken.created_at.desc())
            .first()
        )

    @staticmethod
    def create(token):
        """Persist a new activation token and return it."""

        db.session.add(token)
        db.session.commit()
        return token

    @staticmethod
    def update():
        """Commit pending changes for activation token records."""

        db.session.commit()
