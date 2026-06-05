"""Unit tests for model-level behavior."""

from datetime import datetime, timedelta, timezone

from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.role import Role
from app.models.service import Service
from app.models.refresh_token import RefreshToken
from app.models.user import User


def test_user_set_password_and_check_password(roles_services):
    agent_role = Role(name="agent", label="Agent")
    green_spaces = Service(name="green_spaces", label="Espaces verts")

    user = User(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        role_id=roles_services["agent_role_id"],
        service_id=roles_services["green_spaces_id"],
        is_active=False,
    )
    user.role = agent_role
    user.service = green_spaces

    user.set_password("StrongPass1")

    assert user.password_hash is not None
    assert user.check_password("StrongPass1") is True
    assert user.check_password("WrongPass1") is False


def test_user_activate_account(roles_services):
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        role_id=roles_services["agent_role_id"],
        service_id=roles_services["green_spaces_id"],
        is_active=False,
    )

    user.activate_account()
    assert user.is_active is True


def test_user_to_dict_returns_expected_fields(roles_services):
    agent_role = Role(name="agent", label="Agent")
    green_spaces = Service(name="green_spaces", label="Espaces verts")

    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        role_id=roles_services["agent_role_id"],
        service_id=roles_services["green_spaces_id"],
        is_active=False,
    )
    user.role = agent_role
    user.service = green_spaces

    data = user.to_dict()

    assert data["first_name"] == "Jane"
    assert data["email"] == "jane@example.com"
    assert data["role"]["name"] == "agent"
    assert data["service"]["name"] == "green_spaces"


def test_account_activation_token_create_for_user():
    token, raw_token = AccountActivationToken.create_for_user("user-id", 24)

    assert token.user_id == "user-id"
    assert isinstance(raw_token, str)
    assert token.token_hash is not None
    assert token.expires_at is not None


def test_account_activation_token_verify_token():
    token, raw_token = AccountActivationToken.create_for_user("user-id", 24)
    assert token.verify_token(raw_token) is True
    assert token.verify_token("wrong-token") is False


def test_account_activation_token_mark_as_used():
    token, _ = AccountActivationToken.create_for_user("user-id", 24)
    assert token.is_used() is False
    token.mark_as_used()
    assert token.is_used() is True


def test_account_activation_token_is_expired():
    token, _ = AccountActivationToken.create_for_user("user-id", 24)
    token.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    assert token.is_expired() is True


def test_password_reset_token_verify_token():
    token, raw_token = PasswordResetToken.create_for_user("user-id", 2)
    assert token.verify_token(raw_token) is True
    assert token.verify_token("wrong-token") is False


def test_refresh_token_is_valid_flow():
    token, raw_token = RefreshToken.create_for_user("user-id", 7)

    assert token.verify_token(raw_token) is True
    assert token.is_valid() is True

    token.revoke()

    assert token.is_revoked() is True
    assert token.is_valid() is False
