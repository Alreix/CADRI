"""Facade layer for user management workflows.

The facade exposes the user service behind a thin, controller-friendly API so
routes stay focused on request/response handling instead of business rules.
"""

from app.services.user_service import UserService


class UserFacade:
    """Convenience wrapper around :class:`UserService`."""

    @staticmethod
    def create_user(current_user, first_name, last_name, email, role_name, service_id):
        """Create a user with the requested role and service assignment."""

        return UserService.create_user(
            current_user=current_user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_name=role_name,
            service_id=service_id,
        )

    @staticmethod
    def list_users():
        """Return the full user list."""

        return UserService.list_users()

    @staticmethod
    def get_user_details(user_id):
        """Return a single user's details."""

        return UserService.get_user_details(user_id)

    @staticmethod
    def update_user(current_user, user_id, first_name, last_name, email, role_name, service_id):
        """Update an existing user record."""

        return UserService.update_user(
            current_user=current_user,
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_name=role_name,
            service_id=service_id,
        )

    @staticmethod
    def delete_user(current_user, user_id):
        """Delete a user record."""

        return UserService.delete_user(current_user, user_id)

    @staticmethod
    def list_assignable_users():
        """Return users that can be assigned to missions."""

        return UserService.list_assignable_users()

    @staticmethod
    def update_own_profile(current_user, first_name, last_name, email):
        """Update the currently authenticated user's profile."""

        return UserService.update_own_profile(
            current_user=current_user,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

    