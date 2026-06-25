"""Application-wide constants for the CADRI backend."""

from typing import Final


ADMIN_ROLE: Final[str] = "admin"
RESPONSABLE_ROLE: Final[str] = "responsable"
AGENT_ROLE: Final[str] = "agent"

ALL_ROLE_NAMES: Final[tuple[str, ...]] = (
    ADMIN_ROLE,
    RESPONSABLE_ROLE,
    AGENT_ROLE,
)

ADMIN_ALLOWED_CREATION_ROLES: Final[tuple[str, ...]] = (
    ADMIN_ROLE,
    RESPONSABLE_ROLE,
    AGENT_ROLE,
)

RESPONSABLE_ALLOWED_CREATION_ROLES: Final[tuple[str, ...]] = (
    AGENT_ROLE,
)

ASSIGNABLE_ROLE_NAMES: Final[tuple[str, ...]] = (
    RESPONSABLE_ROLE,
    AGENT_ROLE,
)

MISSION_PRIORITY_LOW: Final[str] = "low"
MISSION_PRIORITY_MEDIUM: Final[str] = "medium"
MISSION_PRIORITY_HIGH: Final[str] = "high"

MISSION_PRIORITY_OPTIONS: Final[list[dict[str, str]]] = [
    {"name": MISSION_PRIORITY_LOW, "label": "Basse"},
    {"name": MISSION_PRIORITY_MEDIUM, "label": "Moyenne"},
    {"name": MISSION_PRIORITY_HIGH, "label": "Urgente"},
]

MISSION_STATUS_TO_DO: Final[str] = "to_do"
MISSION_STATUS_IN_PROGRESS: Final[str] = "in_progress"
MISSION_STATUS_REMARK_PENDING_VALIDATION: Final[str] = "remark_pending_validation"
MISSION_STATUS_COMPLETED: Final[str] = "completed"

MISSION_STATUS_OPTIONS: Final[list[dict[str, str]]] = [
    {"name": MISSION_STATUS_TO_DO, "label": "A faire"},
    {"name": MISSION_STATUS_IN_PROGRESS, "label": "En cours"},
    {
        "name": MISSION_STATUS_REMARK_PENDING_VALIDATION,
        "label": "En attente de validation",
    },
    {"name": MISSION_STATUS_COMPLETED, "label": "Terminée"},
]
