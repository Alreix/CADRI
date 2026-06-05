"""Routes handling the current authenticated user's profile.

This module provides both a Flask-RESTX `Namespace` useful for API docs
(`me_ns`) and a function-based Flask `Blueprint` (`me_bp`) which is
registered by the application factory. Endpoints delegate business logic to
the `UserFacade` and repository helpers.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.facades.user_facade import UserFacade
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import AppError, NotFoundError, ValidationError


# RESTX namespace for documentation
me_ns = Namespace("me", description="Current user profile operations")

# Blueprint for runtime registration by the app factory
me_bp = Blueprint("me", __name__)

update_me_model = me_ns.model(
    "UpdateMePayload",
    {
        "first_name": fields.String(required=True, description="First name"),
        "last_name": fields.String(required=True, description="Last name"),
        "email": fields.String(required=True, description="Email"),
    },
)


def get_json_payload():
    """Parse and validate incoming JSON for profile updates.

    Uses `silent=True` so invalid JSON results in a `ValidationError` rather
    than a Flask exception. Returns the parsed dict.
    """
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        raise ValidationError("JSON body is required.")
    return payload


@me_ns.route("/health")
class MeHealthResource(Resource):
    def get(self):
        """Health-check for the `me` namespace."""
        return {"message": "Me routes working"}, 200


@me_bp.get("/health")
def me_health():
    """Blueprint health endpoint for runtime tests."""
    return {"message": "Me routes working"}, 200


@me_ns.route("")
class MeResource(Resource):
    @jwt_required()
    def get(self):
        """Return current user profile as JSON."""
        try:
            user_id = get_jwt_identity()
            user = UserRepository.get_by_id(user_id)

            if not user:
                raise NotFoundError("User not found.")

            return jsonify(user.to_dict()), 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    @me_ns.expect(update_me_model, validate=True)
    def patch(self):
        """Update the authenticated user's profile with provided fields."""
        try:
            user_id = get_jwt_identity()
            current_user = UserRepository.get_by_id(user_id)

            if not current_user:
                raise NotFoundError("User not found.")

            payload = get_json_payload()

            updated_user = UserFacade.update_own_profile(
                current_user=current_user,
                first_name=payload.get("first_name"),
                last_name=payload.get("last_name"),
                email=payload.get("email"),
            )

            return jsonify(
                {
                    "message": "Profile updated successfully",
                    "user": updated_user.to_dict(),
                }
            ), 200

        except AppError as error:
            return error.to_dict(), error.status_code
