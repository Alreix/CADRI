"""Integration tests for repository helpers."""

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


def test_role_repository_get_by_name(roles_services):
    role = RoleRepository.get_by_name("admin")
    assert role is not None
    assert role.name == "admin"


def test_service_repository_get_by_name(roles_services):
    service = ServiceRepository.get_by_name("green_spaces")
    assert service is not None
    assert service.name == "green_spaces"


def test_user_repository_get_by_email(roles_services):
    user = User(
        first_name="Repo",
        last_name="User",
        email="repo@example.com",
        role_id=roles_services["agent_role_id"],
        service_id=roles_services["green_spaces_id"],
        is_active=True,
    )
    user.set_password("StrongPass1")
    db.session.add(user)
    db.session.commit()

    found_user = UserRepository.get_by_email("repo@example.com")
    assert found_user is not None
    assert found_user.email == "repo@example.com"


def test_account_activation_token_repository_get_by_token_hash(admin_user):
    token, raw_token = AccountActivationToken.create_for_user(admin_user.id, 24)
    AccountActivationTokenRepository.create(token)

    found_token = AccountActivationTokenRepository.get_by_token_hash(token.token_hash)

    assert found_token is not None
    assert found_token.verify_token(raw_token) is True


def test_password_reset_token_repository_get_by_token_hash(admin_user):
    token, raw_token = PasswordResetToken.create_for_user(admin_user.id, 2)
    PasswordResetTokenRepository.create(token)

    found_token = PasswordResetTokenRepository.get_by_token_hash(token.token_hash)

    assert found_token is not None
    assert found_token.verify_token(raw_token) is True


def test_refresh_token_repository_get_by_token_hash(admin_user):
    token, raw_token = RefreshToken.create_for_user(admin_user.id, 7)
    RefreshTokenRepository.create(token)

    found_token = RefreshTokenRepository.get_by_token_hash(token.token_hash)

    assert found_token is not None
    assert found_token.verify_token(raw_token) is True
