"""Authentication routes exposed through Flask-RESTX.

This module keeps the auth API entirely on a RESTX namespace so the app
factory can register it through `Api.add_namespace(...)`.
"""

from __future__ import annotations

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields
from werkzeug.http import dump_cookie

from app.facades.auth_facade import AuthFacade
from app.utils.exceptions import AppError, ValidationError


auth_ns = Namespace("auth", description="Authentication operations")

login_model = auth_ns.model(
    "LoginPayload",
    {
        "email": fields.String(required=True, description="User email"),
        "password": fields.String(required=True, description="User password"),
    },
)

activate_account_model = auth_ns.model(
    "ActivateAccountPayload",
    {
        "token": fields.String(required=True, description="Account activation token"),
        "password": fields.String(required=True, description="New password"),
    },
)

forgot_password_model = auth_ns.model(
    "ForgotPasswordPayload",
    {"email": fields.String(required=True, description="User email")},
)

reset_password_model = auth_ns.model(
    "ResetPasswordPayload",
    {
        "token": fields.String(required=True, description="Password reset token"),
        "password": fields.String(required=True, description="New password"),
    },
)

change_password_model = auth_ns.model(
    "ChangePasswordPayload",
    {
        "current_password": fields.String(required=True, description="Current password"),
        "new_password": fields.String(required=True, description="New password"),
    },
)


def get_json_payload():
    """Parse and validate the incoming JSON payload."""
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        raise ValidationError("JSON body is required.")
    return payload


def build_json_response(body, status_code: int = 200):
    """Return a raw RESTX payload tuple."""
    return body, status_code


def build_refresh_cookie_header(raw_refresh_token: str | None):
    """Build the Set-Cookie header for the refresh token."""
    if not raw_refresh_token:
        return None

    return dump_cookie(
        key=current_app.config["REFRESH_COOKIE_NAME"],
        value=raw_refresh_token,
        httponly=True,
        secure=current_app.config.get("REFRESH_COOKIE_SECURE", False),
        samesite=current_app.config.get("REFRESH_COOKIE_SAMESITE", "Lax"),
        path=current_app.config.get("REFRESH_COOKIE_PATH", "/"),
    )


def build_clear_refresh_cookie_header():
    """Build the Set-Cookie header that clears the refresh token."""
    return dump_cookie(
        key=current_app.config["REFRESH_COOKIE_NAME"],
        value="",
        httponly=True,
        secure=current_app.config.get("REFRESH_COOKIE_SECURE", False),
        samesite=current_app.config.get("REFRESH_COOKIE_SAMESITE", "Lax"),
        path=current_app.config.get("REFRESH_COOKIE_PATH", "/"),
        expires=0,
    )


@auth_ns.route("/health")
class AuthHealthResource(Resource):
    """Expose a public health check for the authentication namespace."""

    def get(self):
        """Return a lightweight auth health response."""
        return {"message": "Auth routes working"}, 200


@auth_ns.route("/login")
class LoginResource(Resource):
    """Authenticate users and issue their session tokens."""

    @auth_ns.expect(login_model, validate=True)
    def post(self):
        """Authenticate a user and set the refresh cookie."""
        try:
            payload = get_json_payload()

            result = AuthFacade.login(
                email=payload.get("email"),
                password=payload.get("password"),
            )

            raw_refresh_token = result.pop("refresh_token", None)
            headers = {}
            cookie_header = build_refresh_cookie_header(raw_refresh_token)
            if cookie_header:
                headers["Set-Cookie"] = cookie_header
            return result, 200, headers

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/logout")
class LogoutResource(Resource):
    """Terminate the current refresh-token based session."""

    def post(self):
        """Revoke the refresh token and clear the cookie."""
        try:
            raw_refresh_token = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"])
            result = AuthFacade.logout(raw_refresh_token)

            return result, 200, {"Set-Cookie": build_clear_refresh_cookie_header()}

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/refresh")
class RefreshSessionResource(Resource):
    """Refresh an authenticated session using the refresh token cookie."""

    def post(self):
        """Rotate the refresh token and return a new session payload."""
        try:
            raw_refresh_token = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"])
            result = AuthFacade.refresh_session(raw_refresh_token)

            new_raw_token = result.pop("refresh_token", None)
            headers = {}
            cookie_header = build_refresh_cookie_header(new_raw_token)
            if cookie_header:
                headers["Set-Cookie"] = cookie_header
            return result, 200, headers

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/activate-account")
class ActivateAccountResource(Resource):
    """Activate newly created accounts from emailed activation links."""

    @auth_ns.expect(activate_account_model, validate=True)
    def post(self):
        """Activate a new account from a token and password."""
        try:
            payload = get_json_payload()
            result = AuthFacade.activate_account(
                raw_token=payload.get("token"),
                password=payload.get("password"),
            )
            return build_json_response(result, 200)

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/forgot-password")
class ForgotPasswordResource(Resource):
    """Start the password reset flow for an active account."""

    @auth_ns.expect(forgot_password_model, validate=True)
    def post(self):
        """Start the password reset flow for the given email."""
        try:
            payload = get_json_payload()
            result = AuthFacade.request_password_reset(email=payload.get("email"))
            return build_json_response(result, 200)

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/reset-password")
class ResetPasswordResource(Resource):
    """Complete password reset requests from emailed reset links."""

    @auth_ns.expect(reset_password_model, validate=True)
    def post(self):
        """Reset a password using a reset token."""
        try:
            payload = get_json_payload()
            result = AuthFacade.reset_password(
                raw_token=payload.get("token"),
                password=payload.get("password"),
            )
            return build_json_response(result, 200)

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/change-password")
class ChangePasswordResource(Resource):
    """Allow an authenticated user to change their current password."""

    @jwt_required()
    @auth_ns.expect(change_password_model, validate=True)
    def patch(self):
        """Change the authenticated user's password."""
        try:
            payload = get_json_payload()
            user_id = get_jwt_identity()

            result = AuthFacade.change_password(
                user_id=user_id,
                current_password=payload.get("current_password"),
                new_password=payload.get("new_password"),
            )

            return build_json_response(result, 200)

        except AppError as error:
            return error.to_dict(), error.status_code
