from app.extensions import db
from app.models.role import Role
from app.models.service import Service


DEFAULT_ROLES = [
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

DEFAULT_SERVICES = [
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
    for role_data in DEFAULT_ROLES:
        existing_role = Role.query.filter_by(name=role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)


def seed_services():
    for service_data in DEFAULT_SERVICES:
        existing_service = Service.query.filter_by(name=service_data["name"]).first()
        if not existing_service:
            service = Service(**service_data)
            db.session.add(service)


def run_seed():
    seed_roles()
    seed_services()
    db.session.commit()
    print("Initial roles and services seeded successfully.")
