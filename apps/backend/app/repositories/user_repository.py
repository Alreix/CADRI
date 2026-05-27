from app.extensions import db
from app.models.user import User


class UserRepository:
    @staticmethod
    def get_all():
        return User.query.order_by(User.created_at.desc()).all()

    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def create(user):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update():
        db.session.commit()

    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()
