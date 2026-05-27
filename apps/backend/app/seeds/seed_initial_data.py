"""Initial data seeds for CADRI.

This module provides a small idempotent seeding mechanism used to populate
essential reference data (roles and services) required by the application.
Seeds are safe to run multiple times: existing records are detected and not
duplicated. The human-friendly `label` fields include localized strings used
directly by the UI mockups.
"""

from typing import Dict, List

from app.extensions import db
from app.models.role import Role
from app.models.service import Service


DEFAULT_ROLES: List[Dict[str, str]] = [
    {
        "name": "admin",
        "label": "Admin",
        "description": "Full access to user and mission management.",
    },
    {
        "name": "responsable",
        "label": "Responsable",
        "description": "Manages missions and creates agent accounts.",
    },
    {
        "name": "agent",
        "label": "Agent",
        "description": "Consults and updates assigned missions.",
    },
]

DEFAULT_SERVICES: List[Dict[str, str]] = [
    {
        "name": "green_spaces",
        "label": "Espaces verts",
        "description": "Green spaces operations.",
    },
    {
        "name": "roads",
        "label": "Voirie",
        "description": "Road maintenance operations.",
    },
    {
        "name": "buildings",
        "label": "Bâtiments",
        "description": "Municipal buildings operations.",
    },
    {
        "name": "cleanliness",
        "label": "Propreté",
        "description": "Cleanliness operations.",
    },
    {
        "name": "events",
        "label": "Événementiel",
        "description": "Events operations.",
    },
    {
        "name": "other",
        "label": "Autre",
        "description": "Other municipal operations.",
    },
]


def seed_roles():
    """Create default role records when they do not already exist.

    This function is intentionally idempotent: it queries by the stable
    `name` key to avoid creating duplicates when the seed runs multiple times
    (for example in development or CI environments).
    """

    for role_data in DEFAULT_ROLES:
        existing_role = Role.query.filter_by(name=role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)


def seed_services():
    """Create default service (department) records when missing.

    Services map to municipal departments used in the CADRI UI and mission
    scoping. Labels in this seed are localized French strings matching the
    project's mockups.
    """

    for service_data in DEFAULT_SERVICES:
        existing_service = Service.query.filter_by(name=service_data["name"]).first()
        if not existing_service:
            service = Service(**service_data)
            db.session.add(service)


def run_seed():
    """Run all seed steps and commit the created records.

    Keep the commit centralized so callers can control the transaction scope
    if they prefer (for example wrapping the seeding in a larger migration).
    """

    seed_roles()
    seed_services()
    db.session.commit()
    print("Initial roles and services seeded successfully.")
