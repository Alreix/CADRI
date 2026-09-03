"""Business service for mission workflows."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.mission import Mission
from app.models.mission_assignment import MissionAssignment
from app.models.mission_service_link import MissionServiceLink
from app.repositories.mission_assignment_repository import MissionAssignmentRepository
from app.repositories.mission_repository import MissionRepository
from app.repositories.mission_service_link_repository import MissionServiceLinkRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.utils.constants import (
    ADMIN_ROLE,
    AGENT_ROLE,
    ASSIGNABLE_ROLE_NAMES,
    MISSION_STATUS_COMPLETED,
    MISSION_STATUS_IN_PROGRESS,
    MISSION_STATUS_REMARK_PENDING_VALIDATION,
    MISSION_STATUS_TO_DO,
    RESPONSABLE_ROLE,
)
from app.utils.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError


class MissionService:
    """Apply mission-related business rules."""

    @staticmethod
    def _require_admin_or_responsable(current_user) -> None:
        """Ensure the current user can manage mission definitions."""
        if current_user.role.name not in (ADMIN_ROLE, RESPONSABLE_ROLE):
            raise AuthorizationError("You are not allowed to manage missions.")

    @staticmethod
    def _require_agent_or_manager(current_user) -> None:
        """Ensure the current user can perform field-level mission actions."""
        if current_user.role.name not in (AGENT_ROLE, RESPONSABLE_ROLE, ADMIN_ROLE):
            raise AuthorizationError("You are not allowed to access this mission action.")
        
    @staticmethod
    def _is_user_assigned_to_mission(current_user, mission: Mission) -> bool:
        """Return whether the current user is assigned to the mission."""
        return any(
            str(assignment.user_id) == str(current_user.id)
            for assignment in mission.assignments
        )

    @staticmethod
    def _require_agent_assignment_if_agent(current_user, mission: Mission) -> None:
        """Ensure agents can act only on missions assigned to them."""
        if current_user.role.name == AGENT_ROLE and not MissionService._is_user_assigned_to_mission(
            current_user,
            mission,
        ):
            raise AuthorizationError("Agent can only act on assigned missions.")

    @staticmethod
    def _validate_dates(start_date, end_date) -> None:
        """Ensure the mission end date is not before the start date."""
        if end_date < start_date:
            raise ValidationError("End date must be greater than or equal to start date.")

    @staticmethod
    def _validate_services(service_ids: list[str]) -> None:
        """Ensure every mission is attached to at least one service."""
        if not service_ids:
            raise ValidationError("At least one service must be linked to the mission.")

    @staticmethod
    def _validate_assignable_users(user_ids: list[str]) -> None:
        """Ensure assigned users exist, are active, and have assignable roles."""
        for user_id in user_ids:
            user = UserRepository.get_by_id(user_id)
            if not user:
                raise NotFoundError("Assigned user not found.")
            if not user.is_active:
                raise ValidationError("Assigned users must be active.")
            if user.role.name not in ASSIGNABLE_ROLE_NAMES:
                raise ValidationError("Only active agents or managers can be assigned.")

    @staticmethod
    def create_mission(current_user, payload: dict) -> Mission:
        """Create a complete mission with services and assignments."""
        MissionService._require_admin_or_responsable(current_user)

        service_ids = payload.get("service_ids", [])
        assigned_user_ids = payload.get("assigned_user_ids", [])

        MissionService._validate_services(service_ids)
        MissionService._validate_assignable_users(assigned_user_ids)
        MissionService._validate_estimated_duration(payload["estimated_duration"])
        MissionService._validate_dates(payload["start_date"], payload["end_date"])

        mission = Mission(
            title=payload["title"],
            intervention_type=payload["intervention_type"],
            location=payload["location"],
            description=payload["description"],
            planned_agents_count=payload["planned_agents_count"],
            estimated_duration=payload["estimated_duration"],
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            priority=payload["priority"],
            required_equipment=payload.get("required_equipment"),
            signage_required=payload.get("signage_required", False),
            status=MISSION_STATUS_TO_DO,
            created_by=current_user.id,
        )

        db.session.add(mission)
        db.session.flush()

        for service_id in service_ids:
            service = ServiceRepository.get_by_id(service_id)
            if not service:
                raise NotFoundError("Service not found.")
            MissionServiceLinkRepository.create(
                MissionServiceLink(mission_id=mission.id, service_id=service_id)
            )

        for user_id in assigned_user_ids:
            MissionAssignmentRepository.create(
                MissionAssignment(mission_id=mission.id, user_id=user_id)
            )

        db.session.commit()
        return mission

    @staticmethod
    def list_missions(current_user, **filters) -> tuple[list[Mission], int]:
        """Return missions with filters, search, and pagination."""
        assigned_to_user_id = None
        if current_user.role.name == AGENT_ROLE:
            assigned_to_user_id = str(current_user.id)
        elif filters.get("my_missions_only"):
            assigned_to_user_id = str(current_user.id)

        return MissionRepository.list_filtered(
            search=filters.get("search"),
            status=filters.get("status"),
            priority=filters.get("priority"),
            service_id=filters.get("service_id"),
            assigned_to_user_id=assigned_to_user_id,
            has_remark=filters.get("has_remark"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            page=filters.get("page", 1),
            per_page=filters.get("per_page", 10),
        )

    @staticmethod
    def get_mission_details(current_user, mission_id) -> Mission:
        """Return mission details."""
        MissionService._require_agent_or_manager(current_user)

        mission = MissionRepository.get_by_id(mission_id)
        if not mission:
            raise NotFoundError("Mission not found.")

        MissionService._require_agent_assignment_if_agent(current_user, mission)
        return mission

    @staticmethod
    def update_mission(current_user, mission_id, payload: dict) -> Mission:
        """Update editable mission fields."""
        MissionService._require_admin_or_responsable(current_user)

        mission = MissionService.get_mission_details(current_user, mission_id)

        service_ids = payload.get("service_ids", [])
        assigned_user_ids = payload.get("assigned_user_ids", [])

        MissionService._validate_estimated_duration(payload["estimated_duration"])
        MissionService._validate_services(service_ids)
        MissionService._validate_assignable_users(assigned_user_ids)
        MissionService._validate_dates(payload["start_date"], payload["end_date"])

        mission.title = payload["title"]
        mission.intervention_type = payload["intervention_type"]
        mission.location = payload["location"]
        mission.description = payload["description"]
        mission.planned_agents_count = payload["planned_agents_count"]
        mission.estimated_duration = payload["estimated_duration"]
        mission.start_date = payload["start_date"]
        mission.end_date = payload["end_date"]
        mission.priority = payload["priority"]
        mission.required_equipment = payload.get("required_equipment")
        mission.signage_required = payload.get("signage_required", False)

        MissionServiceLinkRepository.remove_for_mission(mission.id)
        for service_id in service_ids:
            service = ServiceRepository.get_by_id(service_id)
            if not service:
                raise NotFoundError("Service not found.")
            MissionServiceLinkRepository.create(
                MissionServiceLink(mission_id=mission.id, service_id=service_id)
            )

        MissionAssignmentRepository.remove_for_mission(mission.id)
        for user_id in assigned_user_ids:
            MissionAssignmentRepository.create(
                MissionAssignment(mission_id=mission.id, user_id=user_id)
            )

        db.session.commit()
        return mission

    @staticmethod
    def update_status(current_user, mission_id, new_status: str) -> Mission:
        """Update mission status according to business rules."""
        MissionService._require_agent_or_manager(current_user)
        mission = MissionService.get_mission_details(current_user, mission_id)
        MissionService._require_agent_assignment_if_agent(current_user, mission)

        if new_status == MISSION_STATUS_IN_PROGRESS:
            if mission.status != MISSION_STATUS_TO_DO:
                raise ValidationError("Mission can only be started from to_do status.")
            mission.update_status(new_status)
        else:
            raise ValidationError("Invalid mission status transition.")

        MissionRepository.update()
        return mission

    @staticmethod
    def update_actual_duration(current_user, mission_id, actual_duration: float) -> Mission:
        """Update the actual duration."""
        MissionService._require_agent_or_manager(current_user)
        mission = MissionService.get_mission_details(current_user, mission_id)
        MissionService._require_agent_assignment_if_agent(current_user, mission)

        if actual_duration <= 0:
            raise ValidationError("Actual duration must be greater than zero.")

        mission.update_actual_duration(actual_duration)
        MissionRepository.update()
        return mission

    @staticmethod
    def add_remark(current_user, mission_id, remark: str) -> Mission:
        """Add an assigned agent or responsable remark and apply business effects."""
        if current_user.role.name not in (AGENT_ROLE, RESPONSABLE_ROLE):
            raise AuthorizationError(
                "Only an assigned agent or responsable can add a remark."
            )

        mission = MissionService.get_mission_details(current_user, mission_id)

        if not MissionService._is_user_assigned_to_mission(current_user, mission):
            raise AuthorizationError("Only assigned users can add a remark.")

        if mission.remark:
            raise ConflictError("A remark already exists for this mission.")

        mission.add_remark(remark, current_user.id)
        mission.update_status(MISSION_STATUS_REMARK_PENDING_VALIDATION)
        MissionRepository.update()
        return mission
    
    @staticmethod
    def _validate_estimated_duration(estimated_duration) -> None:
        """Ensure the planned mission duration is at least one hour."""
        if estimated_duration < 1:
            raise ValidationError("Estimated duration must be greater than or equal to 1.")

    @staticmethod
    def validate_mission(current_user, mission_id) -> Mission:
        """Validate a mission containing a remark."""
        MissionService._require_admin_or_responsable(current_user)
        mission = MissionService.get_mission_details(current_user, mission_id)

        if not mission.remark:
            raise ValidationError("Mission validation requires an existing remark.")

        if mission.status != MISSION_STATUS_REMARK_PENDING_VALIDATION:
            raise ConflictError("Mission is not in a valid state for validation.")

        if mission.actual_duration is None:
            raise ValidationError("Actual duration is required before validation.")

        mission.validate_mission(current_user.id)
        mission.complete_mission()
        MissionRepository.update()
        return mission

    @staticmethod
    def complete_mission(current_user, mission_id) -> Mission:
        """Complete a mission if business conditions are met."""
        MissionService._require_agent_or_manager(current_user)
        mission = MissionService.get_mission_details(current_user, mission_id)
        MissionService._require_agent_assignment_if_agent(current_user, mission)

        if mission.actual_duration is None:
            raise ValidationError("Actual duration is required before completion.")

        if mission.remark and mission.validated_at is None:
            raise ConflictError("Mission remark must be validated before completion.")

        if mission.status == MISSION_STATUS_COMPLETED:
            raise ConflictError("Mission is already completed.")

        mission.complete_mission()
        MissionRepository.update()
        return mission

    @staticmethod
    def delete_mission(current_user, mission_id) -> None:
        """Delete a mission in an exceptional way."""
        MissionService._require_admin_or_responsable(current_user)
        mission = MissionService.get_mission_details(current_user, mission_id)
        MissionRepository.delete(mission)
