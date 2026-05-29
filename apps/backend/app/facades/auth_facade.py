"""Facade layer for authentication workflows.

This module keeps route handlers thin by exposing a stable entrypoint over the
authentication service. It does not implement business logic itself; it simply
forwards calls to the underlying service layer.
"""

from app.services.auth_service import AuthService


class AuthFacade:
    """Convenience wrapper around :class:`AuthService`.

    The facade keeps the public surface area small and gives controllers a
    single place to call for authentication-related actions.
    """

    @staticmethod
    def login(email, password):
        """Authenticate a user and return session tokens."""

        return AuthService.login(email, password)

    @staticmethod
    def logout(raw_refresh_token):
        """Invalidate the current refresh token."""

        return AuthService.logout(raw_refresh_token)

    @staticmethod
    def refresh_session(raw_refresh_token):
        """Rotate a refresh token and issue a new access token."""

        return AuthService.refresh_session(raw_refresh_token)

    @staticmethod
    def activate_account(raw_token, password):
        """Activate a newly created account using its raw token."""

        return AuthService.activate_account(raw_token, password)

    @staticmethod
    def request_password_reset(email):
        """Start the password reset flow for the given email address."""

        return AuthService.request_password_reset(email)

    @staticmethod
    def reset_password(raw_token, password):
        """Complete a password reset using the raw reset token."""

        return AuthService.reset_password(raw_token, password)

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change an authenticated user's password."""

        return AuthService.change_password(user_id, current_password, new_password)

    @staticmethod
    def send_activation_email_for_user(user):
        """Resend an activation email for a user record."""

        return AuthService.send_activation_email_for_user(user)
