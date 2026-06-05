"""Authentication HTTP routes (blueprint) for the CADRI backend.

This module exposes a Flask `Blueprint` (`auth_bp`) with the auth-related
endpoints used by the application. Each route delegates business logic to the
`AuthFacade` and translates exceptions into HTTP responses.

The file also defines `auth_ns` and payload models so API documentation tools
can reuse the same models if the `Namespace` is registered in documentation
builders. The actual app factory registers `auth_bp` (see `app.__init__`).
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, fields

from app.facades.auth_facade import AuthFacade
from app.utils.exceptions import AppError, ValidationError


# RESTX namespace (useful for generating docs). We keep models here but the
# application registers the function-based `auth_bp` blueprint for runtime.
auth_ns = Namespace("auth", description="Authentication operations")

# Blueprint consumed by the app factory in `app.__init__.py`.
auth_bp = Blueprint("auth", __name__)


# --- Models used for request validation and API docs ---
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


# --- Helpers ---
def get_json_payload():
    """Parse and validate the incoming JSON payload.

    Raises:
        ValidationError: when the request body is missing or not a JSON object.

    Returns:
        dict: parsed JSON body
    """
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        raise ValidationError("JSON body is required.")
    return payload


def build_json_response(body, status_code: int = 200):
    """Return a Flask-compatible JSON response tuple.

    Returns the pair accepted by Flask view returns: `(Response, status_code)`.
    """
    return jsonify(body), status_code


def set_refresh_cookie(response, raw_refresh_token: str | None):
    """Set the refresh token as a secure HTTP-only cookie on the response.

    If `raw_refresh_token` is falsy nothing is set. Cookie attributes are
    read from application config so tests and environments control security.
    """
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
    """Clear the refresh cookie by setting an empty value and immediate expiry."""
    response.set_cookie(
        key=current_app.config["REFRESH_COOKIE_NAME"],
        value="",
        httponly=True,
        secure=current_app.config.get("REFRESH_COOKIE_SECURE", False),
        samesite=current_app.config.get("REFRESH_COOKIE_SAMESITE", "Lax"),
        path=current_app.config.get("REFRESH_COOKIE_PATH", "/"),
        expires=0,
    )


# --- Blueprint routes ---
@auth_bp.get("/health")
def auth_health():
    """Health-check for the auth blueprint.

    A lightweight endpoint used by tests to assert the blueprint is registered.
    """
    return {"message": "Auth routes working"}, 200


@auth_bp.post("/login")
def login():
    """Authenticate a user and set a refresh cookie.

    Expected JSON: {"email": str, "password": str}
    """
    try:
        payload = get_json_payload()

        result = AuthFacade.login(email=payload.get("email"), password=payload.get("password"))

        raw_refresh_token = result.pop("refresh_token", None)
        response = jsonify(result)
        set_refresh_cookie(response, raw_refresh_token)
        return response, 200

    except AppError as error:
        return error.to_dict(), error.status_code


@auth_bp.post("/logout")
def logout():
    """Revoke the user's refresh token and clear the cookie."""
    try:
        raw_refresh_token = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"]) 
        result = AuthFacade.logout(raw_refresh_token)

        response = jsonify(result)
        clear_refresh_cookie(response)
        return response, 200

    except AppError as error:
        return error.to_dict(), error.status_code


@auth_bp.post("/refresh")
def refresh_session():
    """Rotate the refresh token and return a new access token payload."""
    try:
        raw_refresh_token = request.cookies.get(current_app.config["REFRESH_COOKIE_NAME"]) 
        result = AuthFacade.refresh_session(raw_refresh_token)

        new_raw = result.pop("refresh_token", None)
        response = jsonify(result)
        set_refresh_cookie(response, new_raw)
        return response, 200

    except AppError as error:
        return error.to_dict(), error.status_code


@auth_bp.post("/activate-account")
def activate_account():
    """Activate a new account using an activation token and set a password.

    Expected JSON: {"token": str, "password": str}
    """
    try:
        payload = get_json_payload()
        result = AuthFacade.activate_account(raw_token=payload.get("token"), password=payload.get("password"))
        return build_json_response(result, 200)

    except AppError as error:
        return error.to_dict(), error.status_code


@auth_bp.post("/forgot-password")
def forgot_password():
    """Request a password reset: create a token and send the email."""
    try:
        payload = get_json_payload()
        result = AuthFacade.request_password_reset(email=payload.get("email"))
        return build_json_response(result, 200)

    except AppError as error:
        return error.to_dict(), error.status_code


@auth_bp.post("/reset-password")
def reset_password():
    """Reset a user's password using a reset token.

    Expected JSON: {"token": str, "password": str}
    """
    try:
        payload = get_json_payload()
        result = AuthFacade.reset_password(raw_token=payload.get("token"), password=payload.get("password"))
        return build_json_response(result, 200)

    except AppError as error:
        return error.to_dict(), error.status_code


@auth_bp.patch("/change-password")
@jwt_required()
def change_password():
    """Change the authenticated user's password.

    Expected JSON: {"current_password": str, "new_password": str}
    """
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
