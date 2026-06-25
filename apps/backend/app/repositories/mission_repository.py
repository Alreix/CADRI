"""Repository for mission persistence operations."""

from sqlalchemy import case, or_

from app.extensions import db
from app.models.mission import Mission


class MissionRepository:
    """Centralize mission database access."""

    @staticmethod
    def get_by_id(mission_id):
        """Return a mission by its identifier."""
        return db.session.get(Mission, mission_id)

    @staticmethod
    def create(mission: Mission) -> Mission:
        """Persist a new mission."""
        db.session.add(mission)
        db.session.commit()
        return mission

    @staticmethod
    def update() -> None:
        """Commit pending mission updates."""
        db.session.commit()

    @staticmethod
    def delete(mission: Mission) -> None:
        """Delete a mission."""
        db.session.delete(mission)
        db.session.commit()

    @staticmethod
    def list_filtered(
        *,
        search: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        service_id: str | None = None,
        assigned_to_user_id: str | None = None,
        has_remark: bool | None = None,
        start_date=None,
        end_date=None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[list[Mission], int]:
        """Return missions filtered with pagination."""
        query = Mission.query

        if search:
            like_value = f"%{search}%"
            query = query.filter(
                or_(
                    Mission.title.ilike(like_value),
                    Mission.location.ilike(like_value),
                    Mission.description.ilike(like_value),
                )
            )

        if status:
            query = query.filter(Mission.status == status)

        if priority:
            query = query.filter(Mission.priority == priority)

        if start_date:
            query = query.filter(Mission.start_date >= start_date)

        if end_date:
            query = query.filter(Mission.end_date <= end_date)

        if service_id:
            query = query.join(Mission.services).filter_by(service_id=service_id)

        if assigned_to_user_id:
            query = query.join(Mission.assignments).filter_by(user_id=assigned_to_user_id)

        if has_remark is True:
            query = query.filter(Mission.remark.isnot(None), Mission.remark != "")
        elif has_remark is False:
            query = query.filter(or_(Mission.remark.is_(None), Mission.remark == ""))

        total_items = query.distinct().count()

        # Sort upcoming deadlines first, then surface higher priority missions.
        priority_order = case(
            (Mission.priority == "high", 1),
            (Mission.priority == "medium", 2),
            (Mission.priority == "low", 3),
            else_=4,
        )

        items = (
            query.order_by(Mission.end_date.asc(), priority_order.asc())
            .group_by(Mission.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return items, total_items
