"""Integration tests for the initial CADRI seed data."""

from __future__ import annotations

from app.models.role import Role
from app.models.service import Service
from app.seeds.seed_initial_data import DEFAULT_ROLES, DEFAULT_SERVICES, run_seed


def test_run_seed_creates_default_roles_and_services(app):
    run_seed()

    roles = Role.query.order_by(Role.name.asc()).all()
    services = Service.query.order_by(Service.name.asc()).all()

    assert len(roles) == len(DEFAULT_ROLES)
    assert len(services) == len(DEFAULT_SERVICES)
    assert {role.name for role in roles} == {role["name"] for role in DEFAULT_ROLES}
    assert {service.name for service in services} == {service["name"] for service in DEFAULT_SERVICES}


def test_run_seed_is_idempotent(app):
    run_seed()
    run_seed()

    assert Role.query.count() == len(DEFAULT_ROLES)
    assert Service.query.count() == len(DEFAULT_SERVICES)
