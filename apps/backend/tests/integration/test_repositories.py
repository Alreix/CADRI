"""Integration tests for repository helpers."""

from __future__ import annotations

from app.extensions import db
from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.account_activation_token_repository import (
    AccountActivationTokenRepository,
)
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.utils.tokens import hash_token


def test_role_repository_lists_reference_roles(reference_data):
    roles = RoleRepository.get_all()

    assert [role.name for role in roles] == ["admin", "agent", "responsable"]
    assert RoleRepository.get_by_name("admin").label == "Admin"
    assert RoleRepository.get_by_name("responsable").name == "responsable"


def test_service_repository_lists_reference_services(reference_data):
    services = ServiceRepository.get_all()

    assert [service.name for service in services] == ["events", "roads"]
    assert ServiceRepository.get_by_name("roads").label == "Voirie"
    assert ServiceRepository.get_by_name("events").name == "events"


def test_user_repository_crud(reference_data):
    user = User(
        first_name="Alice",
        last_name="Martin",
        email="alice.martin@cadri.local",
        role_id=reference_data["roles"]["agent"].id,
        service_id=reference_data["services"]["roads"].id,
        is_active=True,
    )
    user.set_password("Password1")

    created_user = UserRepository.create(user)

    assert UserRepository.get_by_email("alice.martin@cadri.local").id == created_user.id
    assert len(UserRepository.get_all()) == 1

    created_user.update_profile(first_name="Alicia", email="alicia.martin@cadri.local")
    UserRepository.update()

    reloaded_user = UserRepository.get_by_email("alicia.martin@cadri.local")
    assert reloaded_user.first_name == "Alicia"

    UserRepository.delete(reloaded_user)
    assert db.session.get(User, created_user.id) is None


def test_account_activation_token_repository_workflow(user_factory):
    user = user_factory(
        email="pending@cadri.local",
        role_name="agent",
        password=None,
        is_active=False,
    )

    token, raw_token = AccountActivationToken.create_for_user(user.id)
    AccountActivationTokenRepository.create(token)

    stored_token = AccountActivationTokenRepository.get_by_token_hash(hash_token(raw_token))
    assert stored_token is not None
    assert AccountActivationTokenRepository.get_latest_for_user(user.id).id == stored_token.id

    AccountActivationTokenRepository.invalidate_unused_tokens_for_user(user.id)
    stored_token_after_invalidation = AccountActivationTokenRepository.get_by_token_hash(hash_token(raw_token))
    assert stored_token_after_invalidation.is_used()


def test_password_reset_token_repository_workflow(user_factory):
    user = user_factory(
        email="reset@cadri.local",
        role_name="agent",
        password="ResetPass1",
        is_active=True,
    )

    token, raw_token = PasswordResetToken.create_for_user(user.id)
    PasswordResetTokenRepository.create(token)

    stored_token = PasswordResetTokenRepository.get_by_token_hash(hash_token(raw_token))
    assert stored_token is not None
    assert PasswordResetTokenRepository.get_latest_for_user(user.id).id == stored_token.id

    PasswordResetTokenRepository.invalidate_unused_tokens_for_user(user.id)
    stored_token_after_invalidation = PasswordResetTokenRepository.get_by_token_hash(hash_token(raw_token))
    assert stored_token_after_invalidation.is_used()


def test_refresh_token_repository_workflow(user_factory):
    user = user_factory(
        email="refresh@cadri.local",
        role_name="admin",
        password="RefreshPass1",
        is_active=True,
    )

    token, raw_token = RefreshToken.create_for_user(user.id)
    RefreshTokenRepository.create(token)

    stored_token = RefreshTokenRepository.get_by_token_hash(hash_token(raw_token))
    assert stored_token is not None
    assert RefreshTokenRepository.get_latest_for_user(user.id).id == stored_token.id

    RefreshTokenRepository.revoke_all_for_user(user.id)
    revoked_token = RefreshTokenRepository.get_by_token_hash(hash_token(raw_token))
    assert revoked_token.is_revoked()
