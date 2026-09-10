"""PostgreSQL concurrency tests for serialized authentication operations."""

from threading import Barrier, Event, Lock, Thread, current_thread, local

from app.extensions import db
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.token_blocklist import TokenBlocklist
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
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


def test_user_delete_waits_for_refresh_lock_then_removes_all_session_state(
    app, admin_user, user_factory, monkeypatch
):
    """User deletion follows refresh lock order and removes its replacement."""

    target_user = user_factory(email="delete-refresh-race@cadri.test")
    target_user_id = target_user.id
    admin_user_id = admin_user.id
    raw_refresh_token = AuthService.login(target_user.email, "StrongPass1")[
        "refresh_token"
    ]
    refresh_has_lock = Event()
    delete_is_waiting = Event()
    allow_refresh = Event()
    original_lock = UserRepository.get_by_id_for_update

    def coordinate_user_locks(user_id):
        """Hold refresh's user lock until deletion is waiting for that lock."""

        if current_thread().name == "delete-worker":
            delete_is_waiting.set()
            return original_lock(user_id)

        user = original_lock(user_id)
        if current_thread().name == "refresh-worker":
            refresh_has_lock.set()
            assert allow_refresh.wait(timeout=10)
        return user

    monkeypatch.setattr(
        UserRepository,
        "get_by_id_for_update",
        staticmethod(coordinate_user_locks),
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
    assert refresh_has_lock.wait(timeout=10)

    def delete_target_user():
        """Load the administrator locally and delete the target user."""

        administrator = UserRepository.get_by_id(admin_user_id)
        return UserService.delete_user(administrator, target_user_id)

    delete_worker = _start_worker(
        app,
        "delete-worker",
        delete_target_user,
        outcomes,
        outcomes_lock,
    )
    assert delete_is_waiting.wait(timeout=10)
    allow_refresh.set()
    refresh_worker.join(timeout=15)
    delete_worker.join(timeout=15)
    assert not refresh_worker.is_alive()
    assert not delete_worker.is_alive()

    db.session.expire_all()
    assert [status for status, _ in outcomes].count("success") == 2
    assert UserRepository.get_by_id(target_user_id) is None
    assert RefreshToken.query.filter_by(user_id=target_user_id).count() == 0
    assert TokenBlocklist.query.filter_by(user_id=target_user_id).count() == 0


def test_old_password_login_waiting_on_password_change_is_rejected(
    app, admin_user, monkeypatch
):
    """A waiting login rechecks the password after password-change commit."""

    user_id = admin_user.id
    email = admin_user.email
    password_has_lock = Event()
    login_is_waiting = Event()
    allow_password_change = Event()
    original_id_lock = UserRepository.get_by_id_for_update
    original_email_lock = UserRepository.get_by_email_for_update

    def hold_password_change_lock(locked_user_id):
        """Pause password change while it owns the serialized user row."""

        user = original_id_lock(locked_user_id)
        if current_thread().name == "password-worker":
            password_has_lock.set()
            assert allow_password_change.wait(timeout=10)
        return user

    def observe_waiting_login(locked_email):
        """Record that stale-password login is attempting the same user lock."""

        if current_thread().name == "login-worker":
            login_is_waiting.set()
        return original_email_lock(locked_email)

    monkeypatch.setattr(
        UserRepository,
        "get_by_id_for_update",
        staticmethod(hold_password_change_lock),
    )
    monkeypatch.setattr(
        UserRepository,
        "get_by_email_for_update",
        staticmethod(observe_waiting_login),
    )

    outcomes = []
    outcomes_lock = Lock()
    password_worker = _start_worker(
        app,
        "password-worker",
        lambda: AuthService.change_password(
            user_id, "StrongPass1", "ChangedPass1!"
        ),
        outcomes,
        outcomes_lock,
    )
    assert password_has_lock.wait(timeout=10)
    login_worker = _start_worker(
        app,
        "login-worker",
        lambda: AuthService.login(email, "StrongPass1"),
        outcomes,
        outcomes_lock,
    )
    assert login_is_waiting.wait(timeout=10)
    allow_password_change.set()
    password_worker.join(timeout=15)
    login_worker.join(timeout=15)
    assert not password_worker.is_alive()
    assert not login_worker.is_alive()

    db.session.expire_all()
    assert [status for status, _ in outcomes].count("success") == 1
    errors = [value for status, value in outcomes if status == "error"]
    assert len(errors) == 1
    assert isinstance(errors[0], AuthenticationError)
    assert RefreshToken.query.filter_by(user_id=user_id).count() == 0
    assert AuthService.login(email, "ChangedPass1!")["access_token"]


def test_refresh_waiting_on_password_reset_cannot_resurrect_session(
    app, admin_user, monkeypatch
):
    """A completed reset invalidates refresh state waiting on its user lock."""

    user_id = admin_user.id
    email = admin_user.email
    raw_refresh_token = AuthService.login(email, "StrongPass1")["refresh_token"]
    reset_token, raw_reset_token = PasswordResetToken.create_for_user(user_id)
    db.session.add(reset_token)
    db.session.commit()
    reset_token_id = reset_token.id
    reset_has_lock = Event()
    refresh_is_waiting = Event()
    allow_reset = Event()
    original_lock = UserRepository.get_by_id_for_update

    def coordinate_user_locks(locked_user_id):
        """Hold reset's user lock until refresh is waiting for the same row."""

        if current_thread().name == "refresh-worker":
            refresh_is_waiting.set()
            return original_lock(locked_user_id)

        user = original_lock(locked_user_id)
        if current_thread().name == "reset-worker":
            reset_has_lock.set()
            assert allow_reset.wait(timeout=10)
        return user

    monkeypatch.setattr(
        UserRepository,
        "get_by_id_for_update",
        staticmethod(coordinate_user_locks),
    )

    outcomes = []
    outcomes_lock = Lock()
    reset_worker = _start_worker(
        app,
        "reset-worker",
        lambda: AuthService.reset_password(raw_reset_token, "ResetStrongPass1!"),
        outcomes,
        outcomes_lock,
    )
    assert reset_has_lock.wait(timeout=10)
    refresh_worker = _start_worker(
        app,
        "refresh-worker",
        lambda: AuthService.refresh_session(raw_refresh_token),
        outcomes,
        outcomes_lock,
    )
    assert refresh_is_waiting.wait(timeout=10)
    allow_reset.set()
    reset_worker.join(timeout=15)
    refresh_worker.join(timeout=15)
    assert not reset_worker.is_alive()
    assert not refresh_worker.is_alive()

    db.session.expire_all()
    persisted_reset = db.session.get(PasswordResetToken, reset_token_id)
    active_tokens = [
        token
        for token in RefreshToken.query.filter_by(user_id=user_id).all()
        if token.is_valid()
    ]
    assert [status for status, _ in outcomes].count("success") == 1
    errors = [value for status, value in outcomes if status == "error"]
    assert len(errors) == 1
    assert isinstance(errors[0], AuthenticationError)
    assert persisted_reset.is_used()
    assert active_tokens == []
    assert AuthService.login(email, "ResetStrongPass1!")["access_token"]
