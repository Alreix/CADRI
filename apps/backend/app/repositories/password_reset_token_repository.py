from app.extensions import db
from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    @staticmethod
    def get_by_id(token_id):
        return PasswordResetToken.query.get(token_id)

    @staticmethod
    def get_by_token_hash(token_hash):
        return PasswordResetToken.query.filter_by(token_hash=token_hash).first()

    @staticmethod
    def get_latest_for_user(user_id):
        return (
            PasswordResetToken.query
            .filter_by(user_id=user_id)
            .order_by(PasswordResetToken.created_at.desc())
            .first()
        )

    @staticmethod
    def create(token):
        db.session.add(token)
        db.session.commit()
        return token

    @staticmethod
    def update():
        db.session.commit()
