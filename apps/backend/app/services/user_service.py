"""User management service for CADRI.

This module contains the high-level user management operations used by the
administration UI and API: creating users, updating profiles, deleting users,
and producing lists of assignable users. Business rules (permissions, role
validation) are enforced here while persistence is delegated to repositories.
"""

from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.utils.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.utils.validators import validate_email


class UserService:
    """High-level user management helpers.

    Keep orchestration and business rules here; use repositories for DB access
    so the code remains testable and focused.
    """
    @staticmethod
    def _validate_name(value, field_name):
        if not value or not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{field_name} is required.")
        return value.strip()

    @staticmethod
    def _get_role_or_fail(role_name):
        role = RoleRepository.get_by_name(role_name)
        if not role:
            raise NotFoundError("Role not found.")
        return role

    @staticmethod
    def _get_service_or_fail(service_id):
        service = ServiceRepository.get_by_id(service_id)
        if not service:
            raise NotFoundError("Service not found.")
        return service

    @staticmethod
    def _check_user_creation_permissions(current_user, target_role_name):
        if current_user.role.name == "admin":
            if target_role_name not in ["admin", "responsable", "agent"]:
                raise AuthorizationError("Target role is not allowed.")
            return

        if current_user.role.name == "responsable":
            if target_role_name != "agent":
                raise AuthorizationError("Responsable can only create agent accounts.")
            return

        raise AuthorizationError("You are not allowed to create users.")

    @staticmethod
    def _check_user_update_permissions(current_user):
        if current_user.role.name != "admin":
            raise AuthorizationError("Only admin can update another user.")

    @staticmethod
    def _check_user_delete_permissions(current_user):
        if current_user.role.name != "admin":
            raise AuthorizationError("Only admin can delete a user.")

    @staticmethod
    def create_user(current_user, first_name, last_name, email, role_name, service_id):
        UserService._check_user_creation_permissions(current_user, role_name)

        first_name = UserService._validate_name(first_name, "First name")
        last_name = UserService._validate_name(last_name, "Last name")
        email = validate_email(email)

        role = UserService._get_role_or_fail(role_name)
        service = UserService._get_service_or_fail(service_id)

        existing_user = UserRepository.get_by_email(email)
        if existing_user and existing_user.is_active:
            raise ConflictError("Email is already used by an active account.")

        if existing_user and not existing_user.is_active:
            existing_user.first_name = first_name
            existing_user.last_name = last_name
            existing_user.role_id = role.id
            existing_user.service_id = service.id
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
            service_id=service.id,
            is_active=False,
        )

        UserRepository.create(user)
        AuthService.send_activation_email_for_user(user)

        return user

    @staticmethod
    def list_users():
        return UserRepository.get_all()

    @staticmethod
    def get_user_details(user_id):
        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    @staticmethod
    def update_user(current_user, user_id, first_name, last_name, email, role_name, service_id):
        UserService._check_user_update_permissions(current_user)

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        first_name = UserService._validate_name(first_name, "First name")
        last_name = UserService._validate_name(last_name, "Last name")
        email = validate_email(email)

        role = UserService._get_role_or_fail(role_name)
        service = UserService._get_service_or_fail(service_id)

        existing_user = UserRepository.get_by_email(email)
        if existing_user and existing_user.id != user.id:
            raise ConflictError("Email is already used by another account.")

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.role_id = role.id
        user.service_id = service.id

        UserRepository.update()
        return user

    @staticmethod
    def delete_user(current_user, user_id):
        UserService._check_user_delete_permissions(current_user)

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        UserRepository.delete(user)

        return {"message": "User deleted successfully"}

    @staticmethod
    def list_assignable_users():
        users = UserRepository.get_all()

        assignable_users = [
            user for user in users
            if user.is_active and user.role and user.role.name in ["agent", "responsable"]
        ]

        return assignable_users

    @staticmethod
    def update_own_profile(current_user, first_name, last_name, email):
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
