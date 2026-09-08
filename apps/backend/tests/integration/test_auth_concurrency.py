"""PostgreSQL concurrency tests for serialized authentication operations."""

from threading import Barrier, Event, Lock, Thread, current_thread, local

from app.extensions import db
from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.auth_service import AuthService
from app.utils.exceptions import AuthenticationError


def _run_in_app_context(app, operation, outcomes, outcomes_lock):
    """Run one authentication operation in an independent scoped DB session."""

    with app.app_context():
        try:
            outcome = ("success", operation())
        except Exception as error:
            outcome = ("error", error)
        finally:
            db.session.remove()

    with outcomes_lock:
        outcomes.append(outcome)


def _start_worker(app, name, operation, outcomes, outcomes_lock):
    """Start a named worker using an independent Flask application context."""

    worker = Thread(
        target=_run_in_app_context,
        name=name,
        args=(app, operation, outcomes, outcomes_lock),
    )
    worker.start()
    return worker


def test_same_refresh_token_can_only_rotate_once(
    app, admin_user, monkeypatch
):
    """Concurrent requests for one token produce exactly one replacement."""

    raw_refresh_token = AuthService.login(admin_user.email, "StrongPass1")[
        "refresh_token"
    ]
    user_id = admin_user.id
    initial_reads = Barrier(2)
    thread_state = local()
    original_lookup = RefreshTokenRepository.get_by_token_hash

    def synchronize_initial_reads(token_hash):
        """Let both workers read the original token before either takes the lock."""

        token = original_lookup(token_hash)
        if not getattr(thread_state, "initial_read_done", False):
            thread_state.initial_read_done = True
            initial_reads.wait(timeout=10)
        return token

    monkeypatch.setattr(
        RefreshTokenRepository,
        "get_by_token_hash",
        staticmethod(synchronize_initial_reads),
    )

    outcomes = []
    outcomes_lock = Lock()
    workers = [
        _start_worker(
            app,
            f"refresh-worker-{index}",
            lambda: AuthService.refresh_session(raw_refresh_token),
            outcomes,
            outcomes_lock,
        )
        for index in range(2)
    ]
    for worker in workers:
        worker.join(timeout=15)
        assert not worker.is_alive()

    db.session.expire_all()
    active_tokens = [
        token
        for token in RefreshToken.query.filter_by(user_id=user_id).all()
        if token.is_valid()
    ]
    assert [status for status, _ in outcomes].count("success") == 1
    errors = [value for status, value in outcomes if status == "error"]
    assert len(errors) == 1
    assert isinstance(errors[0], AuthenticationError)
    assert len(active_tokens) == 1


def test_refresh_cannot_outlive_concurrent_password_change(
    app, admin_user, monkeypatch
):
    """A refresh paused before locking cannot bypass a completed password change."""

    raw_refresh_token = AuthService.login(admin_user.email, "StrongPass1")[
        "refresh_token"
    ]
    user_id = admin_user.id
    refresh_has_read = Event()
    allow_refresh_to_lock = Event()
    original_lookup = RefreshTokenRepository.get_by_token_hash

    def pause_refresh_after_initial_read(token_hash):
        """Pause only the refresh worker after its unlocked discovery query."""

        token = original_lookup(token_hash)
        if current_thread().name == "refresh-worker":
            refresh_has_read.set()
            assert allow_refresh_to_lock.wait(timeout=10)
        return token

    monkeypatch.setattr(
        RefreshTokenRepository,
        "get_by_token_hash",
        staticmethod(pause_refresh_after_initial_read),
    )

    outcomes = []
    outcomes_lock = Lock()
    refresh_worker = _start_worker(
        app,
        "refresh-worker",
        lambda: AuthService.refresh_session(raw_refresh_token),
        outcomes,
        outcomes_lock,
    )
    assert refresh_has_read.wait(timeout=10)
    password_worker = _start_worker(
        app,
        "password-worker",
        lambda: AuthService.change_password(
            user_id, "StrongPass1", "ChangedPass1!"
        ),
        outcomes,
        outcomes_lock,
    )
    password_worker.join(timeout=15)
    assert not password_worker.is_alive()
    allow_refresh_to_lock.set()
    refresh_worker.join(timeout=15)
    assert not refresh_worker.is_alive()

    db.session.expire_all()
    active_tokens = [
        token
        for token in RefreshToken.query.filter_by(user_id=user_id).all()
        if token.is_valid()
    ]
    assert any(status == "success" for status, _ in outcomes)
    assert any(
        status == "error" and isinstance(value, AuthenticationError)
        for status, value in outcomes
    )
    assert active_tokens == []


def test_refresh_cannot_resurrect_session_after_concurrent_logout(
    app, admin_user, monkeypatch
):
    """A completed logout makes an overlapping old-token refresh fail."""

    raw_refresh_token = AuthService.login(admin_user.email, "StrongPass1")[
        "refresh_token"
    ]
    user_id = admin_user.id
    refresh_has_read = Event()
    allow_refresh_to_lock = Event()
    original_lookup = RefreshTokenRepository.get_by_token_hash

    def pause_refresh_after_initial_read(token_hash):
        """Pause refresh discovery without delaying the logout lookup."""

        token = original_lookup(token_hash)
        if current_thread().name == "refresh-worker":
            refresh_has_read.set()
            assert allow_refresh_to_lock.wait(timeout=10)
        return token

    monkeypatch.setattr(
        RefreshTokenRepository,
        "get_by_token_hash",
        staticmethod(pause_refresh_after_initial_read),
    )

    outcomes = []
    outcomes_lock = Lock()
    refresh_worker = _start_worker(
        app,
        "refresh-worker",
        lambda: AuthService.refresh_session(raw_refresh_token),
        outcomes,
        outcomes_lock,
    )
    assert refresh_has_read.wait(timeout=10)
    logout_worker = _start_worker(
        app,
        "logout-worker",
        lambda: AuthService.logout(raw_refresh_token),
        outcomes,
        outcomes_lock,
    )
    logout_worker.join(timeout=15)
    assert not logout_worker.is_alive()
    allow_refresh_to_lock.set()
    refresh_worker.join(timeout=15)
    assert not refresh_worker.is_alive()

    db.session.expire_all()
    active_tokens = [
        token
        for token in RefreshToken.query.filter_by(user_id=user_id).all()
        if token.is_valid()
    ]
    assert any(status == "success" for status, _ in outcomes)
    assert any(
        status == "error" and isinstance(value, AuthenticationError)
        for status, value in outcomes
    )
    assert active_tokens == []
