"""Metadata routes exposed through Flask-RESTX."""

from flask import jsonify
from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required

from app.facades.metadata_facade import MetadataFacade
from app.utils.exceptions import AppError

metadata_ns = Namespace("metadata", description="Metadata operations")


@metadata_ns.route("/health")
class MetadataHealthResource(Resource):
    """Health-check endpoint for metadata routes."""

    def get(self) -> tuple[dict[str, str], int]:
        """Return a simple success message for metadata routes."""
        return {"message": "Metadata routes working"}, 200


@metadata_ns.route("/roles")
class RolesMetadataResource(Resource):
    """Expose the controlled list of roles."""

    @jwt_required()
    def get(self):
        """Return available roles."""
        try:
            roles = MetadataFacade.list_roles()
            return jsonify(roles), 200
        except AppError as error:
            return error.to_dict(), error.status_code


@metadata_ns.route("/services")
class ServicesMetadataResource(Resource):
    """Expose the controlled list of services."""

    @jwt_required()
    def get(self):
        """Return available services."""
        try:
            services = MetadataFacade.list_services()
            return jsonify(services), 200
        except AppError as error:
            return error.to_dict(), error.status_code


@metadata_ns.route("/priorities")
class PrioritiesMetadataResource(Resource):
    """Expose the controlled list of mission priorities."""

    @jwt_required()
    def get(self):
        """Return available mission priorities."""
        try:
            priorities = MetadataFacade.list_priorities()
            return jsonify(priorities), 200
        except AppError as error:
            return error.to_dict(), error.status_code


@metadata_ns.route("/statuses")
class StatusesMetadataResource(Resource):
    """Expose the controlled list of mission statuses."""

    @jwt_required()
    def get(self):
        """Return available mission statuses."""
        try:
            statuses = MetadataFacade.list_statuses()
            return jsonify(statuses), 200
        except AppError as error:
            return error.to_dict(), error.status_code
