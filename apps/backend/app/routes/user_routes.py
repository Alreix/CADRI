"""User management HTTP routes.

Provides the RESTX `users_ns` for documentation and a runtime `users_bp`
blueprint registered by the application. Routes delegate to `UserFacade` and
`UserRepository` and raise domain `AppError`s translated to HTTP responses.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.facades.user_facade import UserFacade
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import AppError, NotFoundError, ValidationError


# RESTX namespace (for docs)
users_ns = Namespace("users", description="User management operations")

# Blueprint used at runtime by the app factory
users_bp = Blueprint("users", __name__)

create_user_model = users_ns.model(
    "CreateUserPayload",
    {
        "first_name": fields.String(required=True, description="First name"),
        "last_name": fields.String(required=True, description="Last name"),
        "email": fields.String(required=True, description="Email"),
        "role": fields.String(required=True, description="Role name"),
        "service_id": fields.String(required=True, description="Service ID"),
    },
)

update_user_model = users_ns.model(
    "UpdateUserPayload",
    {
        "first_name": fields.String(required=True, description="First name"),
        "last_name": fields.String(required=True, description="Last name"),
        "email": fields.String(required=True, description="Email"),
        "role": fields.String(required=True, description="Role name"),
        "service_id": fields.String(required=True, description="Service ID"),
    },
)


def get_json_payload():
    """Parse and validate incoming JSON payloads for user endpoints."""
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        raise ValidationError("JSON body is required.")
    return payload


def get_current_user():
    current_user_id = get_jwt_identity()
    current_user = UserRepository.get_by_id(current_user_id)

    if not current_user:
        raise NotFoundError("Current user not found.")

    return current_user


@users_ns.route("/health")
class UsersHealthResource(Resource):
    def get(self):
        """Health-check for the `users` namespace."""
        return {"message": "User routes working"}, 200


@users_bp.get("/health")
def users_health():
    """Blueprint health endpoint for runtime tests."""
    return {"message": "User routes working"}, 200


@users_ns.route("")
class UsersCollectionResource(Resource):
    @jwt_required()
    def get(self):
        """List all users with simple pagination metadata."""
        try:
            users = UserFacade.list_users()

            items = [user.to_dict() for user in users]

            return jsonify(
                {
                    "items": items,
                    "pagination": {
                        "page": 1,
                        "per_page": len(items),
                        "total_items": len(items),
                        "total_pages": 1,
                    },
                }
            ), 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    @users_ns.expect(create_user_model, validate=True)
    def post(self):
        """Create a new user using the provided payload."""
        try:
            current_user = get_current_user()
            payload = get_json_payload()

            user = UserFacade.create_user(
                current_user=current_user,
                first_name=payload.get("first_name"),
                last_name=payload.get("last_name"),
                email=payload.get("email"),
                role_name=payload.get("role"),
                service_id=payload.get("service_id"),
            )

            return jsonify(
                {
                    "message": "User created successfully",
                    "user": user.to_dict(),
                }
            ), 201

        except AppError as error:
            return error.to_dict(), error.status_code


@users_ns.route("/assignable")
class AssignableUsersResource(Resource):
    @jwt_required()
    def get(self):
        """Return list of users that can be assigned to missions."""
        try:
            users = UserFacade.list_assignable_users()
            return jsonify([user.to_dict() for user in users]), 200

        except AppError as error:
            return error.to_dict(), error.status_code


@users_ns.route("/<string:user_id>")
class UserItemResource(Resource):
    @jwt_required()
    def get(self, user_id):
        """Return details for a single user by id."""
        try:
            user = UserFacade.get_user_details(user_id)
            return jsonify(user.to_dict(include_timestamps=True)), 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    @users_ns.expect(update_user_model, validate=True)
    def patch(self, user_id):
        """Update an existing user's fields."""
        try:
            current_user = get_current_user()
            payload = get_json_payload()

            user = UserFacade.update_user(
                current_user=current_user,
                user_id=user_id,
                first_name=payload.get("first_name"),
                last_name=payload.get("last_name"),
                email=payload.get("email"),
                role_name=payload.get("role"),
                service_id=payload.get("service_id"),
            )

            return jsonify(
                {
                    "message": "User updated successfully",
                    "user": user.to_dict(),
                }
            ), 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    def delete(self, user_id):
        """Delete a user by id (if permitted)."""
        try:
            current_user = get_current_user()
            result = UserFacade.delete_user(current_user, user_id)

            return jsonify(result), 200

        except AppError as error:
            return error.to_dict(), error.status_code
