"""Application facade for metadata-related use cases."""

from app.services.metadata_service import MetadataService


class MetadataFacade:
    """Expose metadata use cases to the route layer."""

    @staticmethod
    def list_roles() -> list[dict[str, str]]:
        """Return all roles formatted for API responses."""
        return MetadataService.list_roles()

    @staticmethod
    def list_services() -> list[dict[str, str]]:
        """Return all services formatted for API responses."""
        return MetadataService.list_services()

    @staticmethod
    def list_priorities() -> list[dict[str, str]]:
        """Return all available mission priorities."""
        return MetadataService.list_priorities()

    @staticmethod
    def list_statuses() -> list[dict[str, str]]:
        """Return all available mission statuses."""
        return MetadataService.list_statuses()
