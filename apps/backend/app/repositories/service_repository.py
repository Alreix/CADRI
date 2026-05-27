from app.models.service import Service


class ServiceRepository:
    @staticmethod
    def get_all():
        return Service.query.order_by(Service.name.asc()).all()

    @staticmethod
    def get_by_id(service_id):
        return Service.query.get(service_id)

    @staticmethod
    def get_by_name(name):
        return Service.query.filter_by(name=name).first()
