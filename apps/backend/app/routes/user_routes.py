"""RESTX routes for user administration and profile-related operations."""

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.facades.user_facade import UserFacade
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import AppError, NotFoundError, ValidationError

users_ns = Namespace("users", description="User management operations")

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
    """Return the request JSON payload or raise a validation error."""
    payload = request.get_json()
    if not payload:
        raise ValidationError("JSON body is required.")
    return payload


def get_current_user():
    """Return the authenticated current user."""
    current_user_id = get_jwt_identity()
    current_user = UserRepository.get_by_id(current_user_id)

    if not current_user:
        raise NotFoundError("Current user not found.")

    return current_user


@users_ns.route("/health")
class UsersHealthResource(Resource):
    """Health-check endpoint for user routes."""

    def get(self):
        """Return a success message for user routes."""
        return {"message": "User routes working"}, 200


@users_ns.route("")
class UsersCollectionResource(Resource):
    """Collection endpoints for users."""

    @jwt_required()
    def get(self):
        """Return users with filters and pagination."""
        try:
            current_user = get_current_user()

            search = request.args.get("search")
            role_name = request.args.get("role")
            service_id = request.args.get("service_id")
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))

            result = UserFacade.list_users(
                current_user=current_user,
                search=search,
                role_name=role_name,
                service_id=service_id,
                page=page,
                per_page=per_page,
            )

            return jsonify(
                {
                    "items": [user.to_dict() for user in result["items"]],
                    "pagination": result["pagination"],
                }
            ), 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    @users_ns.expect(create_user_model, validate=True)
    def post(self):
        """Create a new user."""
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
    """Endpoint returning users that can be assigned to missions."""

    @jwt_required()
    def get(self):
        """Return active assignable users."""
        try:
            users = UserFacade.list_assignable_users()
            return jsonify([user.to_dict() for user in users]), 200

        except AppError as error:
            return error.to_dict(), error.status_code


@users_ns.route("/<string:user_id>")
class UserItemResource(Resource):
    """Single-user endpoints."""

    @jwt_required()
    def get(self, user_id):
        """Return one user."""
        try:
            user = UserFacade.get_user_details(user_id)
            return jsonify(user.to_dict(include_timestamps=True)), 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    @users_ns.expect(update_user_model, validate=True)
    def patch(self, user_id):
        """Update one user."""
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
        """Delete one user."""
        try:
            current_user = get_current_user()
            result = UserFacade.delete_user(current_user, user_id)
            return jsonify(result), 200

        except AppError as error:
            return error.to_dict(), error.status_code
