
from flask import Blueprint, jsonify
from flask_restx import Namespace, Resource

from app.repositories.role_repository import RoleRepository
from app.repositories.service_repository import ServiceRepository


# RESTX namespace for documentation
metadata_ns = Namespace("metadata", description="Metadata operations")

# Blueprint for runtime registration by the app factory
metadata_bp = Blueprint("metadata", __name__)


"""Metadata-related routes.

This module exposes both a `Namespace` (for API docs) and a lightweight
`Blueprint` (`metadata_bp`) used at runtime. The blueprint endpoints mirror the
namespace resources so the app factory can register `metadata_bp` directly.
"""


@metadata_ns.route("/health")
class MetadataHealthResource(Resource):
    """Simple runtime health endpoint for metadata routes (docs namespace)."""
    def get(self):
        return {"message": "Metadata routes working"}, 200


@metadata_bp.get("/health")
def metadata_health():
    """Blueprint health endpoint for runtime tests."""
    return jsonify({"message": "Metadata routes working"}), 200


@metadata_ns.route("/roles")
class RolesMetadataResource(Resource):
    def get(self):
        """Return available roles used as metadata."""
        roles = RoleRepository.get_all()

        return jsonify([
            {"name": role.name, "label": role.label} for role in roles
        ]), 200


@metadata_ns.route("/services")
class ServicesMetadataResource(Resource):
    def get(self):
        """Return available services used as metadata."""
        services = ServiceRepository.get_all()

        return jsonify([
            {"id": str(service.id), "name": service.name, "label": service.label}
            for service in services
        ]), 200


@metadata_ns.route("/priorities")
class PrioritiesMetadataResource(Resource):
    def get(self):
        """Return the list of supported priority levels."""
        return jsonify(
            [
                {"name": "low", "label": "Basse"},
                {"name": "medium", "label": "Moyenne"},
                {"name": "high", "label": "Haute"},
            ]
        ), 200


@metadata_ns.route("/statuses")
class StatusesMetadataResource(Resource):
    def get(self):
        """Return the list of supported mission statuses."""
        return jsonify(
            [
                {"name": "to_do", "label": "À faire"},
                {"name": "in_progress", "label": "En cours"},
                {"name": "remark_pending_validation", "label": "En attente de validation"},
                {"name": "completed", "label": "Terminée"},
            ]
        ), 200


@metadata_bp.get("/roles")
def metadata_roles():
    """Blueprint: return available roles used as metadata."""
    roles = RoleRepository.get_all()
    return jsonify([{"name": r.name, "label": r.label} for r in roles]), 200


@metadata_bp.get("/services")
def metadata_services():
    """Blueprint: return available services used as metadata."""
    services = ServiceRepository.get_all()
    return jsonify([
        {"id": str(s.id), "name": s.name, "label": s.label} for s in services
    ]), 200


@metadata_bp.get("/priorities")
def metadata_priorities():
    """Blueprint: return the list of supported priority levels."""
    return jsonify([
        {"name": "low", "label": "Basse"},
        {"name": "medium", "label": "Moyenne"},
        {"name": "high", "label": "Haute"},
    ]), 200


@metadata_bp.get("/statuses")
def metadata_statuses():
    """Blueprint: return the list of supported mission statuses."""
    return jsonify([
        {"name": "to_do", "label": "À faire"},
        {"name": "in_progress", "label": "En cours"},
        {"name": "remark_pending_validation", "label": "En attente de validation"},
        {"name": "completed", "label": "Terminée"},
    ]), 200

