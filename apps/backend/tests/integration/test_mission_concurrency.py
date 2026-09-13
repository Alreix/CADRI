"""Deterministic PostgreSQL tests for serialized mission workflow transitions."""

from queue import Queue
from threading import Event, Thread, current_thread
from time import monotonic

import pytest
from sqlalchemy import text

from app.extensions import db
from app.models.mission import Mission
from app.models.user import User
from app.repositories.mission_repository import MissionRepository
from app.services.mission_service import MissionService
from app.utils.constants import (
    MISSION_STATUS_COMPLETED,
    MISSION_STATUS_IN_PROGRESS,
    MISSION_STATUS_REMARK_PENDING_VALIDATION,
)
from app.utils.exceptions import ConflictError
from tests.integration.test_mission_service import create_service_mission


@pytest.mark.parametrize("first_action", ["complete", "remark"])
def test_completion_and_remark_serialize_with_fresh_state(
    app, admin_user, agent_user, roles_services, monkeypatch, first_action,
):
    """Make the loser wait and reject using refreshed identity-map data."""
    assert db.engine.dialect.name == "postgresql"
    mission = create_service_mission(admin_user, roles_services, agent_user)
    mission_id, user_id = mission.id, agent_user.id
    MissionService.update_status(agent_user, mission_id, MISSION_STATUS_IN_PROGRESS)
    MissionService.update_actual_duration(agent_user, mission_id, 2)
    db.session.remove()

    first_locked = Event()
    release_first = Event()
    second_read = Event()
    outcomes = Queue()
    backend_pids = {}
    original_lookup = MissionRepository.get_by_id_for_update

    def hold_first_lock(identifier):
        """Keep the first real lock until PostgreSQL reports a blocked waiter."""
        locked = original_lookup(identifier)
        if current_thread().name == "mission-first":
            first_locked.set()
            assert release_first.wait(timeout=15), "First transaction was not released"
        return locked

    monkeypatch.setattr(
        MissionRepository, "get_by_id_for_update", staticmethod(hold_first_lock)
    )

    def run_action(action, first):
        """Use an independent context and retain a stale ORM reference."""
        with app.app_context():
            try:
                db.session.execute(text("SET LOCAL lock_timeout = '12s'"))
                backend_pids[first] = db.session.execute(
                    text("SELECT pg_backend_pid()")
                ).scalar_one()
                user = db.session.get(User, user_id)
                cached = db.session.get(Mission, mission_id)
                assert cached.status == MISSION_STATUS_IN_PROGRESS
                if not first:
                    second_read.set()
                if action == "complete":
                    result = MissionService.complete_mission(user, mission_id)
                else:
                    result = MissionService.add_remark(user, mission_id, "Concurrent remark")
                outcomes.put((first, "success", result.status))
            except ConflictError as error:
                outcomes.put((first, "conflict", (error, cached.status)))
            except Exception as error:
                # Surface worker failures to pytest instead of losing them in a thread.
                outcomes.put((first, "error", error))
            finally:
                db.session.remove()

    second_action = "remark" if first_action == "complete" else "complete"
    first = Thread(target=run_action, name="mission-first", args=(first_action, True))
    second = Thread(target=run_action, name="mission-second", args=(second_action, False))
    workers = []
    try:
        first.start()
        workers.append(first)
        assert first_locked.wait(timeout=10), "First transaction did not lock the mission"
        second.start()
        workers.append(second)
        assert second_read.wait(timeout=10), "Second transaction did not cache the old state"
        deadline = monotonic() + 10
        with db.engine.connect() as observer:
            while monotonic() < deadline:
                blockers = observer.execute(
                    text("SELECT pg_blocking_pids(:pid)"), {"pid": backend_pids[False]}
                ).scalar_one()
                if backend_pids[True] in blockers:
                    break
            else:
                pytest.fail("PostgreSQL did not report the expected lock wait")
    finally:
        release_first.set()
        for worker in workers:
            worker.join(timeout=15)
        assert all(not worker.is_alive() for worker in workers), "Mission worker did not finish"

    results = {first: (status, value) for first, status, value in list(outcomes.queue)}
    expected = (
        MISSION_STATUS_COMPLETED if first_action == "complete"
        else MISSION_STATUS_REMARK_PENDING_VALIDATION
    )
    assert results[True] == ("success", expected)
    assert results[False][0] == "conflict", results
    assert isinstance(results[False][1][0], ConflictError)
    assert results[False][1][1] == expected

    with app.app_context():
        persisted = db.session.get(Mission, mission_id)
        assert persisted.status == expected
        assert persisted.validated_at is None
        assert float(persisted.actual_duration) == 2
        if first_action == "complete":
            assert persisted.completed_at is not None
            assert persisted.remark is None
            assert persisted.remark_added_at is None
            assert persisted.remark_added_by is None
        else:
            assert persisted.completed_at is None
            assert persisted.remark == "Concurrent remark"
            assert persisted.remark_added_at is not None
            assert persisted.remark_added_by == user_id
        # The losing transaction has ended and released its lock.
        db.session.execute(text("SET LOCAL lock_timeout = '1s'"))
        assert MissionRepository.get_by_id_for_update(mission_id).status == expected
