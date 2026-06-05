"""Routes for the current authenticated user's profile."""

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.facades.user_facade import UserFacade
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import AppError, NotFoundError, ValidationError


me_ns = Namespace("me", description="Current user profile operations")

update_me_model = me_ns.model(
    "UpdateMePayload",
    {
        "first_name": fields.String(required=True, description="First name"),
        "last_name": fields.String(required=True, description="Last name"),
        "email": fields.String(required=True, description="Email"),
    },
)


def get_json_payload():
    """Parse and validate incoming JSON for profile updates."""
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        raise ValidationError("JSON body is required.")
    return payload


@me_ns.route("/health")
class MeHealthResource(Resource):
    def get(self):
        """Return the health status of the me namespace."""
        return {"message": "Me routes working"}, 200


@me_ns.route("")
class MeResource(Resource):
    @jwt_required()
    def get(self):
        """Return the current user's profile."""
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
        """Update the current user's profile."""
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