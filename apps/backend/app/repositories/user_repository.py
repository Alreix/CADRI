"""Repository helpers for user persistence and lookup.

User queries are centralized here so the authentication and administration
layers do not duplicate database access code.
"""

from app.extensions import db
from app.models.user import User


class UserRepository:
    """Data-access helpers for `User` records."""

    @staticmethod
    def get_all():
        """Return all users ordered by most recent creation time."""

        return User.query.order_by(User.created_at.desc()).all()

    @staticmethod
    def get_by_id(user_id):
        """Return the user with the given primary key, if any."""

        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email):
        """Return the user matching the given email address, if any."""

        return User.query.filter_by(email=email).first()

    @staticmethod
    def create(user):
        """Persist a new user and return it."""

        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update():
        """Commit pending changes for user records."""

        db.session.commit()

    @staticmethod
    def delete(user):
        """Delete the provided user and commit the transaction."""

        db.session.delete(user)
        db.session.commit()
