"""Initial data seeds for CADRI.

This module provides a small idempotent seeding mechanism used to populate
essential reference data (roles, services, and a few test users) required by
the application. Seeds are safe to run multiple times: existing records are
detected and not duplicated.
"""

from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.mission import Mission
from app.models.mission_assignment import MissionAssignment
from app.models.mission_service_link import MissionServiceLink
from app.models.role import Role
from app.models.service import Service
from app.models.user import User


DEFAULT_ROLES: list[dict[str, str]] = [
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

DEFAULT_SERVICES: list[dict[str, str]] = [
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


def seed_test_users():
    """Create a small set of default users for development and local tests."""
    admin_role = Role.query.filter_by(name="admin").first()
    responsable_role = Role.query.filter_by(name="responsable").first()
    agent_role = Role.query.filter_by(name="agent").first()

    green_spaces = Service.query.filter_by(name="green_spaces").first()
    roads = Service.query.filter_by(name="roads").first()

    users_to_seed = [
        {
            "first_name": "Admin",
            "last_name": "Cadri",
            "email": "admin@cadri.local",
            "role_id": admin_role.id,
            "service_id": green_spaces.id,
            "password": "StrongPass1*",
        },
        {
            "first_name": "Responsable",
            "last_name": "Cadri",
            "email": "responsable@cadri.local",
            "role_id": responsable_role.id,
            "service_id": green_spaces.id,
            "password": "StrongPass1*",
        },
        {
            "first_name": "Agent",
            "last_name": "Cadri",
            "email": "agent@cadri.local",
            "role_id": agent_role.id,
            "service_id": roads.id,
            "password": "StrongPass1*",
        },
    ]

    for user_data in users_to_seed:
        existing_user = User.query.filter_by(email=user_data["email"]).first()
        if not existing_user:
            user = User(
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                email=user_data["email"],
                role_id=user_data["role_id"],
                service_id=user_data["service_id"],
                is_active=True,
            )
            user.set_password(user_data["password"])
            db.session.add(user)


def seed_demo_missions():
    """Create demo missions for local development and final project review."""
    admin = User.query.filter_by(email="admin@cadri.local").first()
    responsable = User.query.filter_by(email="responsable@cadri.local").first()
    agent = User.query.filter_by(email="agent@cadri.local").first()

    green_spaces = Service.query.filter_by(name="green_spaces").first()
    roads = Service.query.filter_by(name="roads").first()
    buildings = Service.query.filter_by(name="buildings").first()
    cleanliness = Service.query.filter_by(name="cleanliness").first()
    events = Service.query.filter_by(name="events").first()

    if not all([admin, responsable, agent, green_spaces, roads, buildings, cleanliness, events]):
        return

    now = datetime.now(timezone.utc)
    missions_to_seed = [
        {
            "title": "Réparation nid-de-poule avenue des Platanes",
            "intervention_type": "Réparation de chaussée",
            "location": "Avenue des Platanes",
            "description": (
                "Réparer un nid-de-poule signalé sur la voie principale afin "
                "de sécuriser la circulation."
            ),
            "planned_agents_count": 2,
            "estimated_duration": 3,
            "start_date": now + timedelta(days=1),
            "end_date": now + timedelta(days=1, hours=3),
            "priority": "high",
            "required_equipment": "Enrobé à froid, compacteur, cônes de signalisation",
            "signage_required": True,
            "service_ids": [roads.id],
            "assigned_user_ids": [agent.id],
        },
        {
            "title": "Taille des haies du parc municipal",
            "intervention_type": "Entretien espaces verts",
            "location": "Parc municipal",
            "description": (
                "Tailler les haies autour des cheminements piétons pour "
                "améliorer la visibilité et l'accès au parc."
            ),
            "planned_agents_count": 2,
            "estimated_duration": 4,
            "start_date": now + timedelta(days=2),
            "end_date": now + timedelta(days=2, hours=4),
            "priority": "medium",
            "required_equipment": "Taille-haies, broyeur, équipements de protection",
            "signage_required": False,
            "service_ids": [green_spaces.id],
            "assigned_user_ids": [responsable.id, agent.id],
        },
        {
            "title": "Ramassage des branches square des Écoles",
            "intervention_type": "Nettoyage espaces verts",
            "location": "Square des Écoles",
            "description": (
                "Ramasser les branches tombées après intempéries et dégager "
                "les accès piétons du square."
            ),
            "planned_agents_count": 1,
            "estimated_duration": 2,
            "start_date": now + timedelta(days=4),
            "end_date": now + timedelta(days=4, hours=2),
            "priority": "low",
            "required_equipment": "Gants, râteau, camion benne",
            "signage_required": False,
            "service_ids": [green_spaces.id],
            "assigned_user_ids": [responsable.id],
        },
        {
            "title": "Contrôle affaissement trottoir rue Victor Hugo",
            "intervention_type": "Inspection de voirie",
            "location": "Rue Victor Hugo",
            "description": (
                "Contrôler l'affaissement du trottoir, sécuriser la zone et "
                "préparer une intervention de reprise si nécessaire."
            ),
            "planned_agents_count": 2,
            "estimated_duration": 2,
            "start_date": now + timedelta(days=5),
            "end_date": now + timedelta(days=5, hours=2),
            "priority": "high",
            "required_equipment": "Barrières, bombe de marquage, appareil photo",
            "signage_required": True,
            "service_ids": [roads.id],
            "assigned_user_ids": [responsable.id, agent.id],
        },
        {
            "title": "Désherbage des massifs devant la mairie",
            "intervention_type": "Entretien espaces verts",
            "location": "Place de la Mairie",
            "description": (
                "Désherber les massifs, retirer les végétaux secs et préparer "
                "les zones avant la plantation saisonnière."
            ),
            "planned_agents_count": 1,
            "estimated_duration": 3,
            "start_date": now + timedelta(days=6),
            "end_date": now + timedelta(days=6, hours=3),
            "priority": "medium",
            "required_equipment": "Binette, sacs de collecte, gants",
            "signage_required": False,
            "service_ids": [green_spaces.id],
            "assigned_user_ids": [responsable.id],
        },
        {
            "title": "Remplacement serrure local technique",
            "intervention_type": "Maintenance bâtiment",
            "location": "Local technique nord",
            "description": (
                "Remplacer la serrure défectueuse du local technique et "
                "vérifier que les accès restent sécurisés."
            ),
            "planned_agents_count": 2,
            "estimated_duration": 2,
            "start_date": now + timedelta(days=7),
            "end_date": now + timedelta(days=7, hours=2),
            "priority": "medium",
            "required_equipment": "Nouvelle serrure, tournevis, perceuse",
            "signage_required": False,
            "service_ids": [buildings.id],
            "assigned_user_ids": [responsable.id, agent.id],
        },
        {
            "title": "Nettoyage dépôt sauvage rue du Moulin",
            "intervention_type": "Nettoyage urbain",
            "location": "Rue du Moulin",
            "description": (
                "Retirer un dépôt sauvage signalé par les habitants et "
                "nettoyer la zone après enlèvement."
            ),
            "planned_agents_count": 2,
            "estimated_duration": 3,
            "start_date": now + timedelta(days=8),
            "end_date": now + timedelta(days=8, hours=3),
            "priority": "high",
            "required_equipment": "Camion benne, pinces, gants renforcés",
            "signage_required": True,
            "service_ids": [cleanliness.id],
            "assigned_user_ids": [responsable.id, agent.id],
        },
        {
            "title": "Installation barrières fête du quartier",
            "intervention_type": "Préparation événementielle",
            "location": "Place du Marché",
            "description": (
                "Installer les barrières de sécurité et organiser les accès "
                "piétons avant la fête du quartier."
            ),
            "planned_agents_count": 2,
            "estimated_duration": 4,
            "start_date": now + timedelta(days=9),
            "end_date": now + timedelta(days=9, hours=4),
            "priority": "medium",
            "required_equipment": "Barrières, rubalise, panneaux temporaires",
            "signage_required": True,
            "service_ids": [events.id],
            "assigned_user_ids": [responsable.id],
        },
        {
            "title": "Révision éclairage hall de la mairie",
            "intervention_type": "Maintenance électrique",
            "location": "Hall de la mairie",
            "description": (
                "Contrôler les luminaires du hall, remplacer les ampoules "
                "défectueuses et vérifier le bon fonctionnement général."
            ),
            "planned_agents_count": 1,
            "estimated_duration": 2,
            "start_date": now + timedelta(days=10),
            "end_date": now + timedelta(days=10, hours=2),
            "priority": "low",
            "required_equipment": "Escabeau, ampoules LED, testeur électrique",
            "signage_required": False,
            "service_ids": [buildings.id],
            "assigned_user_ids": [agent.id],
        },
        {
            "title": "Nettoyage caniveaux marché central",
            "intervention_type": "Entretien voirie et propreté",
            "location": "Marché central",
            "description": (
                "Nettoyer les caniveaux autour du marché central après la "
                "forte fréquentation du week-end."
            ),
            "planned_agents_count": 2,
            "estimated_duration": 3,
            "start_date": now + timedelta(days=11),
            "end_date": now + timedelta(days=11, hours=3),
            "priority": "medium",
            "required_equipment": "Balais, pelle, camion de nettoyage",
            "signage_required": True,
            "service_ids": [roads.id, cleanliness.id],
            "assigned_user_ids": [responsable.id, agent.id],
        },
    ]

    for mission_data in missions_to_seed:
        existing_mission = Mission.query.filter_by(title=mission_data["title"]).first()
        if existing_mission:
            continue

        mission = Mission(
            title=mission_data["title"],
            intervention_type=mission_data["intervention_type"],
            location=mission_data["location"],
            description=mission_data["description"],
            planned_agents_count=mission_data["planned_agents_count"],
            estimated_duration=mission_data["estimated_duration"],
            start_date=mission_data["start_date"],
            end_date=mission_data["end_date"],
            priority=mission_data["priority"],
            required_equipment=mission_data["required_equipment"],
            signage_required=mission_data["signage_required"],
            created_by=admin.id,
        )
        db.session.add(mission)
        db.session.flush()

        for service_id in mission_data["service_ids"]:
            db.session.add(
                MissionServiceLink(mission_id=mission.id, service_id=service_id)
            )

        for user_id in mission_data["assigned_user_ids"]:
            db.session.add(MissionAssignment(mission_id=mission.id, user_id=user_id))


def run_seed():
    """Run all seed steps and commit the created records."""

    seed_roles()
    seed_services()
    db.session.commit()

    seed_test_users()
    db.session.commit()

    seed_demo_missions()
    db.session.commit()

    print("Initial roles, services, test users, and demo missions seeded successfully.")
