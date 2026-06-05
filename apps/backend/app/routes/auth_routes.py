"""Authentication routes exposed through Flask-RESTX.

This module keeps the auth API entirely on a RESTX namespace so the app
factory can register it through `Api.add_namespace(...)`.
"""

from __future__ import annotations

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

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
    """Return a JSON response tuple for RESTX resources."""
    return jsonify(body), status_code


def set_refresh_cookie(response, raw_refresh_token: str | None):
    """Attach the refresh token as an HTTP-only cookie."""
    if not raw_refresh_token:
        return

    response.set_cookie(
        key=current_app.config["REFRESH_COOKIE_NAME"],
        value=raw_refresh_token,
        httponly=True,
        secure=current_app.config.get("REFRESH_COOKIE_SECURE", False),
        samesite=current_app.config.get("REFRESH_COOKIE_SAMESITE", "Lax"),
        path=current_app.config.get("REFRESH_COOKIE_PATH", "/"),
    )


def clear_refresh_cookie(response):
    """Clear the refresh token cookie."""
    response.set_cookie(
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
    def get(self):
        """Return a lightweight auth health response."""
        return {"message": "Auth routes working"}, 200


@auth_ns.route("/login")
class LoginResource(Resource):
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
            response = jsonify(result)
            set_refresh_cookie(response, raw_refresh_token)
            return response, 200

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/logout")
class LogoutResource(Resource):
    def post(self):
        """Revoke the refresh token and clear the cookie."""
        try:
            raw_refresh_token = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"])
            result = AuthFacade.logout(raw_refresh_token)

            response = jsonify(result)
            clear_refresh_cookie(response)
            return response, 200

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/refresh")
class RefreshSessionResource(Resource):
    def post(self):
        """Rotate the refresh token and return a new session payload."""
        try:
            raw_refresh_token = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"])
            result = AuthFacade.refresh_session(raw_refresh_token)

            new_raw_token = result.pop("refresh_token", None)
            response = jsonify(result)
            set_refresh_cookie(response, new_raw_token)
            return response, 200

        except AppError as error:
            return error.to_dict(), error.status_code


@auth_ns.route("/activate-account")
class ActivateAccountResource(Resource):
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