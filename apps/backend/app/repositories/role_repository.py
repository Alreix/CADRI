from app.models.role import Role


class RoleRepository:
    @staticmethod
    def get_all():
        return Role.query.order_by(Role.name.asc()).all()

    @staticmethod
    def get_by_id(role_id):
        return Role.query.get(role_id)

    @staticmethod
    def get_by_name(name):
        return Role.query.filter_by(name=name).first()
