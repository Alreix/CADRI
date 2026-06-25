"""RESTX routes for mission operations."""

from datetime import datetime

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.facades.mission_facade import MissionFacade
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import AppError, NotFoundError, ValidationError

missions_ns = Namespace("missions", description="Mission operations")

mission_payload_model = missions_ns.model(
    "MissionPayload",
    {
        "title": fields.String(required=True),
        "intervention_type": fields.String(required=True),
        "location": fields.String(required=True),
        "description": fields.String(required=True),
        "planned_agents_count": fields.Integer(required=True),
        "estimated_duration": fields.Float(required=True),
        "start_date": fields.String(required=True),
        "end_date": fields.String(required=True),
        "priority": fields.String(required=True),
        "required_equipment": fields.String(required=False),
        "signage_required": fields.Boolean(required=False),
        "service_ids": fields.List(fields.String, required=True),
        "assigned_user_ids": fields.List(fields.String, required=True),
    },
)

status_update_model = missions_ns.model(
    "MissionStatusUpdatePayload",
    {
        "status": fields.String(required=True),
    },
)

actual_duration_model = missions_ns.model(
    "MissionActualDurationPayload",
    {
        "actual_duration": fields.Float(required=True),
    },
)

remark_model = missions_ns.model(
    "MissionRemarkPayload",
    {
        "remark": fields.String(required=True),
    },
)


def get_current_user():
    """Return the authenticated current user."""
    current_user_id = get_jwt_identity()
    current_user = UserRepository.get_by_id(current_user_id)

    if not current_user:
        raise NotFoundError("Current user not found.")

    return current_user


def get_json_payload():
    """Return the JSON body or raise a validation error."""
    payload = request.get_json()
    if not payload:
        raise ValidationError("JSON body is required.")
    return payload


def parse_mission_payload(payload: dict) -> dict:
    """Convert incoming payload values to backend-ready mission values."""
    return {
        "title": payload["title"],
        "intervention_type": payload["intervention_type"],
        "location": payload["location"],
        "description": payload["description"],
        "planned_agents_count": payload["planned_agents_count"],
        "estimated_duration": payload["estimated_duration"],
        "start_date": datetime.fromisoformat(payload["start_date"]),
        "end_date": datetime.fromisoformat(payload["end_date"]),
        "priority": payload["priority"],
        "required_equipment": payload.get("required_equipment"),
        "signage_required": payload.get("signage_required", False),
        "service_ids": payload["service_ids"],
        "assigned_user_ids": payload["assigned_user_ids"],
    }


@missions_ns.route("/health")
class MissionsHealthResource(Resource):
    """Health-check endpoint for mission routes."""

    def get(self):
        """Return a success message for mission routes."""
        return {"message": "Mission routes working"}, 200


@missions_ns.route("")
class MissionCollectionResource(Resource):
    """Mission collection endpoints."""

    @jwt_required()
    def get(self):
        """Return filtered missions with pagination."""
        try:
            current_user = get_current_user()

            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))

            start_date_raw = request.args.get("start_date")
            end_date_raw = request.args.get("end_date")

            start_date = (
                datetime.fromisoformat(start_date_raw) if start_date_raw else None
            )
            end_date = (
                datetime.fromisoformat(end_date_raw) if end_date_raw else None
            )

            has_remark_raw = request.args.get("has_remark")
            has_remark = None

            if has_remark_raw == "true":
                has_remark = True
            elif has_remark_raw == "false":
                has_remark = False
            elif has_remark_raw is not None:
                raise ValidationError("has_remark must be true or false.")

            missions, total_items = MissionFacade.list_missions(
                current_user=current_user,
                search=request.args.get("search"),
                status=request.args.get("status"),
                priority=request.args.get("priority"),
                service_id=request.args.get("service_id"),
                my_missions_only=request.args.get("my_missions_only") == "true",
                has_remark=has_remark,
                start_date=start_date,
                end_date=end_date,
                page=page,
                per_page=per_page,
            )

            total_pages = (total_items + per_page - 1) // per_page

            return {
                "items": [mission.to_dict(include_relations=True) for mission in missions],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_items": total_items,
                    "total_pages": total_pages,
                },
            }, 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    @missions_ns.expect(mission_payload_model, validate=True)
    def post(self):
        """Create a complete mission."""
        try:
            current_user = get_current_user()
            payload = parse_mission_payload(get_json_payload())

            mission = MissionFacade.create_mission(current_user, payload)

            return {
                "message": "Mission created successfully",
                "mission": mission.to_dict(include_relations=True),
                }, 201

        except AppError as error:
            return error.to_dict(), error.status_code


@missions_ns.route("/<string:mission_id>")
class MissionItemResource(Resource):
    """Single mission endpoints."""

    @jwt_required()
    def get(self, mission_id):
        """Return mission details."""
        try:
            mission = MissionFacade.get_mission_details(mission_id)
            return mission.to_dict(include_relations=True), 200
        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    @missions_ns.expect(mission_payload_model, validate=True)
    def patch(self, mission_id):
        """Update editable mission fields."""
        try:
            current_user = get_current_user()
            payload = parse_mission_payload(get_json_payload())

            mission = MissionFacade.update_mission(current_user, mission_id, payload)

            return {
                "message": "Mission updated successfully",
                "mission": mission.to_dict(include_relations=True),
            }, 200

        except AppError as error:
            return error.to_dict(), error.status_code

    @jwt_required()
    def delete(self, mission_id):
        """Delete a mission."""
        try:
            current_user = get_current_user()
            MissionFacade.delete_mission(current_user, mission_id)
            return {"message": "Mission deleted successfully"}, 200
        except AppError as error:
            return error.to_dict(), error.status_code


@missions_ns.route("/<string:mission_id>/status")
class MissionStatusResource(Resource):
    """Mission status update endpoint."""

    @jwt_required()
    @missions_ns.expect(status_update_model, validate=True)
    def patch(self, mission_id):
        """Update the mission status."""
        try:
            current_user = get_current_user()
            payload = get_json_payload()

            mission = MissionFacade.update_status(
                current_user,
                mission_id,
                payload["status"],
            )

            return {
                "message": "Mission status updated successfully",
                "mission": mission.to_dict(),
            }, 200

        except AppError as error:
            return error.to_dict(), error.status_code


@missions_ns.route("/<string:mission_id>/actual-duration")
class MissionActualDurationResource(Resource):
    """Mission actual duration update endpoint."""

    @jwt_required()
    @missions_ns.expect(actual_duration_model, validate=True)
    def patch(self, mission_id):
        """Update the actual duration."""
        try:
            current_user = get_current_user()
            payload = get_json_payload()

            mission = MissionFacade.update_actual_duration(
                current_user,
                mission_id,
                payload["actual_duration"],
            )

            return {
                "message": "Actual duration updated successfully",
                "mission": mission.to_dict(),
            }, 200

        except AppError as error:
            return error.to_dict(), error.status_code


@missions_ns.route("/<string:mission_id>/remark")
class MissionRemarkResource(Resource):
    """Mission remark endpoint."""

    @jwt_required()
    @missions_ns.expect(remark_model, validate=True)
    def post(self, mission_id):
        """Add a remark to a mission."""
        try:
            current_user = get_current_user()
            payload = get_json_payload()

            mission = MissionFacade.add_remark(
                current_user,
                mission_id,
                payload["remark"],
            )

            return {
                "message": "Remark added successfully",
                "mission": mission.to_dict(),
            }, 200

        except AppError as error:
            return error.to_dict(), error.status_code


@missions_ns.route("/<string:mission_id>/validate")
class MissionValidateResource(Resource):
    """Mission validation endpoint."""

    @jwt_required()
    def post(self, mission_id):
        """Validate a mission containing a remark."""
        try:
            current_user = get_current_user()
            mission = MissionFacade.validate_mission(current_user, mission_id)

            return {
                "message": "Mission validated successfully",
                "mission": mission.to_dict(),
            }, 200

        except AppError as error:
            return error.to_dict(), error.status_code


@missions_ns.route("/<string:mission_id>/complete")
class MissionCompleteResource(Resource):
    """Mission completion endpoint."""

    @jwt_required()
    def post(self, mission_id):
        """Complete a mission if business conditions are met."""
        try:
            current_user = get_current_user()
            mission = MissionFacade.complete_mission(current_user, mission_id)

            return {
                "message": "Mission completed successfully",
                "completed_at": mission.completed_at.isoformat()
                if mission.completed_at
                else None,
            }, 200

        except AppError as error:
            return error.to_dict(), error.status_code
