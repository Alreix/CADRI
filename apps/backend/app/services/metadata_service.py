"""Business service responsible for metadata retrieval."""

from app.repositories.role_repository import RoleRepository
from app.repositories.service_repository import ServiceRepository
from app.utils.constants import MISSION_PRIORITY_OPTIONS, MISSION_STATUS_OPTIONS


class MetadataService:
    """Centralize controlled metadata exposed by the API."""

    @staticmethod
    def list_roles() -> list[dict[str, str]]:
        """Return the list of available roles."""
        roles = RoleRepository.get_all()

        return [
            {
                "id": str(role.id),
                "name": role.name,
                "label": role.label,
            }
            for role in roles
        ]

    @staticmethod
    def list_services() -> list[dict[str, str]]:
        """Return the list of available services."""
        services = ServiceRepository.get_all()

        return [
            {
                "id": str(service.id),
                "name": service.name,
                "label": service.label,
            }
            for service in services
        ]

    @staticmethod
    def list_priorities() -> list[dict[str, str]]:
        """Return the controlled list of mission priorities."""
        return MISSION_PRIORITY_OPTIONS.copy()

    @staticmethod
    def list_statuses() -> list[dict[str, str]]:
        """Return the controlled list of mission statuses."""
        return MISSION_STATUS_OPTIONS.copy()
