"""Authentication and session management for CADRI.

This module implements the main authentication flows used by the application:
- user login (issue access + refresh tokens)
- logout and refresh token revocation
- account activation and password reset orchestration

The implementation delegates persistence to repository helpers and uses the
email service to deliver activation/reset links. Business rules such as token
expiry durations are derived from application configuration.
"""

from datetime import datetime, timezone

from flask import current_app
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.repositories.account_activation_token_repository import (
    AccountActivationTokenRepository,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.token_blocklist_repository import TokenBlocklistRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.utils.exceptions import (
    AuthenticationError,
    GoneError,
    NotFoundError,
    ValidationError,
)
from app.utils.tokens import hash_token
from app.utils.validators import validate_email, validate_password


class AuthService:
    """High-level authentication orchestration used by routes and services.

    Keep business logic here and keep database interactions in repositories so
    the code remains testable and easy to reason about.
    """

    @staticmethod
    def _issue_access_token(user_id):
        """Issue an access JWT with sub-second UTC precision for invalidation."""

        return create_access_token(
            identity=str(user_id),
            additional_claims={"iat": datetime.now(timezone.utc).timestamp()},
        )

    @staticmethod
    def login(email, password):
        """Authenticate a user and create a fresh access/refresh token pair.

        The login flow normalizes the email, validates account activation, and
        revokes previous refresh tokens so a new login replaces older sessions.
        """
        email = validate_email(email)

        user = UserRepository.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid credentials.")

        if not user.is_active:
            raise AuthenticationError("Account is not activated.", status_code=403)

        if not user.password_hash:
            raise AuthenticationError(
                "Password is not initialized for this account.",
                status_code=403,
            )

        if not user.check_password(password):
            raise AuthenticationError("Invalid credentials.")

        access_token = AuthService._issue_access_token(user.id)

        RefreshTokenRepository.revoke_all_for_user(user.id)
        refresh_token, raw_refresh_token = RefreshToken.create_for_user(
            user.id,
            expires_in_days=current_app.config["REFRESH_TOKEN_EXPIRES_DAYS"],
        )
        RefreshTokenRepository.create(refresh_token)

        return {
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": raw_refresh_token,
            "user": {
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role.name,
                "service": {
                    "id": str(user.service.id),
                    "name": user.service.name,
                    "label": user.service.label,
                },
            },
        }

    @staticmethod
    def logout(raw_refresh_token, access_token_data=None):
        """Atomically revoke the current access JWT and opaque refresh token.

        Access-token metadata is optional so an expired or missing access token
        cannot prevent the refresh cookie from being terminated.
        """
        has_staged_changes = False
        try:
            if access_token_data:
                access_token_user = UserRepository.get_by_id(
                    access_token_data["user_id"]
                )
                if access_token_user is not None:
                    TokenBlocklistRepository.create_if_absent(
                        jti=access_token_data["jti"],
                        user_id=access_token_data["user_id"],
                        token_type=access_token_data["token_type"],
                        expires_at=access_token_data["expires_at"],
                        commit=False,
                    )
                    has_staged_changes = True

            if raw_refresh_token:
                token_hash = hash_token(raw_refresh_token)
                token = RefreshTokenRepository.get_by_token_hash(token_hash)
                if token is not None and not token.is_revoked():
                    token.revoke()
                    RefreshTokenRepository.update(commit=False)
                    has_staged_changes = True

            if has_staged_changes:
                db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {"message": "Logout successful"}

    @staticmethod
    def refresh_session(raw_refresh_token):
        """Rotate a valid refresh token and issue a new access token."""
        if not raw_refresh_token:
            raise AuthenticationError("Refresh token is required.")

        token_hash = hash_token(raw_refresh_token)
        token = RefreshTokenRepository.get_by_token_hash(token_hash)

        if not token:
            raise AuthenticationError("Invalid refresh token.")

        if not token.is_valid():
            raise AuthenticationError("Refresh token is expired or invalid.")

        user = UserRepository.get_by_id(token.user_id)
        if not user:
            raise AuthenticationError("User not found.")

        access_token = AuthService._issue_access_token(user.id)

        new_refresh_token, new_raw_refresh_token = RefreshToken.create_for_user(
            user.id,
            expires_in_days=current_app.config["REFRESH_TOKEN_EXPIRES_DAYS"],
        )

        token.rotate(new_raw_refresh_token)
        RefreshTokenRepository.update()
        RefreshTokenRepository.create(new_refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": new_raw_refresh_token,
        }

    @staticmethod
    def activate_account(raw_token, password):
        """Activate an account from an emailed token and initialize its password."""
        if not raw_token:
            raise ValidationError("Activation token is required.")

        validate_password(password)

        token_hash = hash_token(raw_token)
        token = AccountActivationTokenRepository.get_by_token_hash(token_hash)

        if not token:
            raise NotFoundError("Activation token not found.")

        if token.is_used() or token.is_expired():
            raise GoneError("Activation token is expired or already used.")

        user = UserRepository.get_by_id(token.user_id)
        if not user:
            raise NotFoundError("User not found.")

        user.set_password(password)
        user.is_active = True
        user.activated_at = datetime.now(timezone.utc)
        token.mark_as_used()

        UserRepository.update()
        AccountActivationTokenRepository.update()

        return {"message": "Account activated successfully"}

    @staticmethod
    def request_password_reset(email):
        """Create and email a password reset token when the account is eligible.

        The response is intentionally generic so callers cannot infer whether
        an email address belongs to an active CADRI account.
        """
        email = validate_email(email)

        user = UserRepository.get_by_email(email)

        if not user or not user.is_active:
            return {
                "message": "If the account exists, a reset email has been sent"
            }

        PasswordResetTokenRepository.invalidate_unused_tokens_for_user(user.id)

        token, raw_token = PasswordResetToken.create_for_user(
            user.id,
            expires_in_hours=current_app.config["PASSWORD_RESET_TOKEN_EXPIRES_HOURS"],
        )
        PasswordResetTokenRepository.create(token)

        EmailService.send_password_reset_email(user.email, raw_token)

        return {"message": "If the account exists, a reset email has been sent"}

    @staticmethod
    def reset_password(raw_token, password):
        """Reset a user's password after validating a one-time reset token."""
        if not raw_token:
            raise ValidationError("Reset token is required.")

        validate_password(password)

        token_hash = hash_token(raw_token)
        token = PasswordResetTokenRepository.get_by_token_hash(token_hash)

        if not token:
            raise NotFoundError("Reset token not found.")

        if token.is_used() or token.is_expired():
            raise GoneError("Reset token is expired or already used.")

        user = UserRepository.get_by_id(token.user_id)
        if not user:
            raise NotFoundError("User not found.")

        try:
            user.set_password(password)
            user.invalidate_existing_access_tokens()
            token.mark_as_used()

            UserRepository.update(commit=False)
            PasswordResetTokenRepository.update(commit=False)
            RefreshTokenRepository.revoke_all_for_user(user.id, commit=False)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {"message": "Password reset successfully"}

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change the current user's password and revoke active refresh tokens."""
        validate_password(new_password)

        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        if not user.check_password(current_password):
            raise AuthenticationError(
                "Current password is incorrect.",
                status_code=403,
            )

        try:
            user.set_password(new_password)
            user.invalidate_existing_access_tokens()
            UserRepository.update(commit=False)
            RefreshTokenRepository.revoke_all_for_user(user.id, commit=False)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {"message": "Password changed successfully"}


    @staticmethod
    def send_activation_email_for_user(user):
        """Invalidate older activation tokens and send a new activation email."""
        AccountActivationTokenRepository.invalidate_unused_tokens_for_user(user.id)

        token, raw_token = AccountActivationToken.create_for_user(
            user.id,
            expires_in_hours=current_app.config["ACCOUNT_ACTIVATION_TOKEN_EXPIRES_HOURS"],
        )
        AccountActivationTokenRepository.create(token)

        EmailService.send_activation_email(user.email, raw_token)
