"""Integration tests for the initial CADRI seed data."""

from app.extensions import db
from app.models.role import Role
from app.models.service import Service
from app.models.user import User
from app.seeds.seed_initial_data import run_seed


def test_run_seed_creates_default_roles_services_and_users(app):
    with app.app_context():
        db.session.query(User).delete()
        db.session.query(Role).delete()
        db.session.query(Service).delete()
        db.session.commit()

        run_seed()

        roles = Role.query.all()
        services = Service.query.all()
        users = User.query.all()

        assert len(roles) == 3
        assert len(services) == 6
        assert len(users) == 3
