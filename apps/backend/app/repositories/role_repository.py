"""Repository helpers for role lookup and listing.

Roles are reference data used across the authorization and user management
flows, so query helpers are centralized here.
"""

from app.models.role import Role


class RoleRepository:
    """Data-access helpers for `Role` records."""

    @staticmethod
    def get_all():
        """Return all roles ordered alphabetically by technical name."""

        return Role.query.order_by(Role.name.asc()).all()

    @staticmethod
    def get_by_id(role_id):
        """Return the role with the given primary key, if any."""

        return Role.query.get(role_id)

    @staticmethod
    def get_by_name(name):
        """Return the role with the given technical name, if any."""

        return Role.query.filter_by(name=name).first()
