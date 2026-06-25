"""Repository helpers for service lookup and listing.

Services represent municipal departments in CADRI and are reused throughout
the user and mission workflows.
"""

from app.models.service import Service


class ServiceRepository:
    """Data-access helpers for `Service` records."""

    @staticmethod
    def get_all():
        """Return all services ordered alphabetically by technical name."""

        return Service.query.order_by(Service.label.asc()).all()

    @staticmethod
    def get_by_id(service_id):
        """Return the service with the given primary key, if any."""

        return Service.query.get(service_id)

    @staticmethod
    def get_by_name(name):
        """Return the service with the given technical name, if any."""

        return Service.query.filter_by(name=name).first()

