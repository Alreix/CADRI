"""User management service for CADRI.

This module contains the high-level user management operations used by the
administration UI and API: creating users, updating profiles, deleting users,
and producing lists of assignable users. Business rules are enforced here
while persistence is delegated to repositories.
"""

from app.extensions import db
from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.utils.constants import (
    ADMIN_ALLOWED_CREATION_ROLES,
    ADMIN_ROLE,
    AGENT_ROLE,
    ASSIGNABLE_ROLE_NAMES,
    RESPONSABLE_ALLOWED_CREATION_ROLES,
    RESPONSABLE_ROLE,
)
from app.utils.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.utils.validators import validate_email


class UserService:
    """High-level user management helpers."""

    @staticmethod
    def _validate_name(value, field_name):
        """Validate a user first name or last name."""
        if not value or not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field_name} is required.")
        return value.strip()

    @staticmethod
    def _validate_pagination(page: int, per_page: int) -> tuple[int, int]:
        """Validate and normalize pagination values."""
        if page < 1:
            raise ValidationError("Page must be greater than or equal to 1.")

        if per_page < 1:
            raise ValidationError("Per page must be greater than or equal to 1.")

        if per_page > 100:
            raise ValidationError("Per page must be less than or equal to 100.")

        return page, per_page

    @staticmethod
    def _get_role_or_fail(role_name):
        """Return a role or raise if it does not exist."""
        role = RoleRepository.get_by_name(role_name)
        if not role:
            raise NotFoundError("Role not found.")
        return role

    @staticmethod
    def _get_service_or_fail(service_id):
        """Return a service or raise if it does not exist."""
        service = ServiceRepository.get_by_id(service_id)
        if not service:
            raise NotFoundError("Service not found.")
        return service

    @staticmethod
    def _check_user_creation_permissions(current_user, target_role_name):
        """Validate whether the current user can create the requested role."""
        if current_user.role.name == ADMIN_ROLE:
            if target_role_name not in ADMIN_ALLOWED_CREATION_ROLES:
                raise AuthorizationError("Target role is not allowed.")
            return

        if current_user.role.name == RESPONSABLE_ROLE:
            if target_role_name not in RESPONSABLE_ALLOWED_CREATION_ROLES:
                raise AuthorizationError("Responsable can only create agent accounts.")
            return

        raise AuthorizationError("You are not allowed to create users.")

    @staticmethod
    def _check_user_update_permissions(current_user):
        """Ensure only admins can update another user."""
        if current_user.role.name != ADMIN_ROLE:
            raise AuthorizationError("Only admin can update another user.")

    @staticmethod
    def _check_user_delete_permissions(current_user):
        """Ensure only admins can delete a user."""
        if current_user.role.name != ADMIN_ROLE:
            raise AuthorizationError("Only admin can delete a user.")

    @staticmethod
    def _check_user_list_permissions(current_user):
        """Ensure only admins can list all users."""
        if current_user.role.name != ADMIN_ROLE:
            raise AuthorizationError("Only admin can list users.")
        
    @staticmethod
    def _check_user_details_permissions(current_user, user_id):
        """Ensure users can only access allowed user details."""
        if current_user.role.name != ADMIN_ROLE and str(current_user.id) != str(user_id):
            raise AuthorizationError("You are not allowed to access this user.")

    @staticmethod
    def _check_assignable_users_permissions(current_user):
        """Ensure only admins and responsables can list assignable users."""
        if current_user.role.name not in (ADMIN_ROLE, RESPONSABLE_ROLE):
            raise AuthorizationError("Only admin or responsable can list assignable users.")

    @staticmethod
    def create_user(current_user, first_name, last_name, email, role_name, service_id):
        """Create a new user and trigger the activation email."""
        UserService._check_user_creation_permissions(current_user, role_name)

        first_name = UserService._validate_name(first_name, "First name")
        last_name = UserService._validate_name(last_name, "Last name")
        email = validate_email(email)

        role = UserService._get_role_or_fail(role_name)
        UserService._get_service_or_fail(service_id)

        existing_user = UserRepository.get_by_email(email)

        if existing_user and existing_user.is_active:
            raise ConflictError("Email is already used by an active account.")

        if existing_user and not existing_user.is_active:
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            existing_user.role_id = role.id
            existing_user.service_id = service_id
            existing_user.password_hash = None
            existing_user.activated_at = None

            UserRepository.update()
            AuthService.send_activation_email_for_user(existing_user)
            return existing_user

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role_id=role.id,
            service_id=service_id,
            is_active=False,
        )

        UserRepository.create(user)
        AuthService.send_activation_email_for_user(user)

        return user

    @staticmethod
    def list_users(
        current_user,
        *,
        search: str | None = None,
        role_name: str | None = None,
        service_id: str | None = None,
        page: int = 1,
        per_page: int = 10,
    ):
        """Return a filtered and paginated user list for admins only."""
        UserService._check_user_list_permissions(current_user)
        page, per_page = UserService._validate_pagination(page, per_page)

        if role_name is not None:
            UserService._get_role_or_fail(role_name)

        if service_id is not None:
            UserService._get_service_or_fail(service_id)

        items, total_items = UserRepository.list_filtered(
            search=search,
            role_name=role_name,
            service_id=service_id,
            page=page,
            per_page=per_page,
        )

        total_pages = (total_items + per_page - 1) // per_page if total_items else 0

        return {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": total_pages,
            },
        }

    @staticmethod
    def get_user_details(current_user, user_id):
        """Return a single user's details."""
        UserService._check_user_details_permissions(current_user, user_id)

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    @staticmethod
    def update_user(current_user, user_id, first_name, last_name, email, role_name, service_id):
        """Update another user's profile, role, and service."""
        UserService._check_user_update_permissions(current_user)

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        first_name = UserService._validate_name(first_name, "First name")
        last_name = UserService._validate_name(last_name, "Last name")
        email = validate_email(email)

        role = UserService._get_role_or_fail(role_name)
        UserService._get_service_or_fail(service_id)

        existing_user = UserRepository.get_by_email(email)
        if existing_user and existing_user.id != user.id:
            raise ConflictError("Email is already used by another account.")

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.role_id = role.id
        user.service_id = service_id

        UserRepository.update()
        return user

    @staticmethod
    def delete_user(current_user, user_id):
        """Delete a user and related authentication tokens directly."""
        UserService._check_user_delete_permissions(current_user)

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        AccountActivationToken.query.filter_by(user_id=user.id).delete()
        PasswordResetToken.query.filter_by(user_id=user.id).delete()
        RefreshToken.query.filter_by(user_id=user.id).delete()

        db.session.delete(user)
        db.session.commit()

        return {"message": "User deleted successfully"}

    @staticmethod
    def list_assignable_users(current_user):
        """Return active users that can be assigned to missions."""
        UserService._check_assignable_users_permissions(current_user)
        users = UserRepository.get_all()

        assignable_users = [
            user
            for user in users
            if user.is_active and user.role and user.role.name in ASSIGNABLE_ROLE_NAMES
        ]

        return assignable_users

    @staticmethod
    def update_own_profile(current_user, first_name, last_name, email):
        """Update the current user's own profile."""
        first_name = UserService._validate_name(first_name, "First name")
        last_name = UserService._validate_name(last_name, "Last name")
        email = validate_email(email)

        existing_user = UserRepository.get_by_email(email)
        if existing_user and existing_user.id != current_user.id:
            raise ConflictError("Email is already used by another account.")

        current_user.update_profile(
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        UserRepository.update()
        return current_user
