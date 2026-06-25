"""Repository helpers for user persistence and lookup.

User queries are centralized here so the authentication and administration
layers do not duplicate database access code.
"""

from sqlalchemy import or_

from app.extensions import db
from app.models.user import User


class UserRepository:
    """Data-access helpers for ``User`` records."""

    @staticmethod
    def get_all():
        """Return all users ordered by most recent creation time."""
        return User.query.order_by(User.created_at.desc()).all()

    @staticmethod
    def get_by_id(user_id):
        """Return the user with the given primary key, if any."""
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email):
        """Return the user matching the given email address, if any."""
        return User.query.filter_by(email=email).first()

    @staticmethod
    def list_filtered(
        *,
        search: str | None = None,
        role_name: str | None = None,
        service_id: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[User], int]:
        """Return filtered users with pagination metadata support."""
        query = User.query

        if search:
            like_value = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(like_value),
                    User.last_name.ilike(like_value),
                    User.email.ilike(like_value),
                )
            )

        if role_name:
            query = query.join(User.role).filter_by(name=role_name)

        if service_id:
            query = query.filter(User.service_id == service_id)

        total_items = query.count()

        items = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total_items

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
