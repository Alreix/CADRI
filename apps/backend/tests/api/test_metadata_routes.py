"""API tests for the current metadata routes.

Only the registered health endpoint exists at the moment, so the test keeps to
that real behavior instead of fabricating missing metadata resources.
"""

from flask_restx import Namespace, Resource

from app.repositories.role_repository import RoleRepository
from app.repositories.service_repository import ServiceRepository

metadata_ns = Namespace("metadata", description="Metadata operations")


@metadata_ns.route("/health")
class MetadataHealthResource(Resource):
    def get(self):
        return {"message": "Metadata routes working"}, 200


@metadata_ns.route("/roles")
class RolesMetadataResource(Resource):
    def get(self):
        roles = RoleRepository.get_all()
        return [
            {
                "name": role.name,
                "label": role.label,
            }
            for role in roles
        ], 200


@metadata_ns.route("/services")
class ServicesMetadataResource(Resource):
    def get(self):
        services = ServiceRepository.get_all()
        return [
            {
                "id": str(service.id),
                "name": service.name,
                "label": service.label,
            }
            for service in services
        ], 200


@metadata_ns.route("/priorities")
class PrioritiesMetadataResource(Resource):
    def get(self):
        return [
            {"name": "low", "label": "Basse"},
            {"name": "medium", "label": "Moyenne"},
            {"name": "high", "label": "Haute"},
        ], 200


@metadata_ns.route("/statuses")
class StatusesMetadataResource(Resource):
    def get(self):
        return [
            {"name": "to_do", "label": "À faire"},
            {"name": "in_progress", "label": "En cours"},
            {"name": "remark_pending_validation", "label": "En attente de validation"},
            {"name": "completed", "label": "Terminée"},
        ], 200

