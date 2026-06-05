"""Unit tests for model-level behavior."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.account_activation_token import AccountActivationToken
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.utils.tokens import generate_raw_token, hash_token


def test_user_password_and_profile_helpers(app):
    user = User(
        id=uuid4(),
        first_name="Test",
        last_name="User",
        email="test.user@cadri.local",
        role_id=uuid4(),
        service_id=uuid4(),
        is_active=False,
    )

    user.set_password("Password1")

    assert user.password_hash
    assert user.check_password("Password1")
    assert not user.check_password("WrongPass1")

    user.activate_account()
    user.update_profile(first_name="Updated", last_name="Name", email="updated.name@cadri.local")

    assert user.is_active is True
    assert user.first_name == "Updated"
    assert user.last_name == "Name"
    assert user.email == "updated.name@cadri.local"


def test_base_model_to_dict_serializes_uuid_and_datetimes():
    now = datetime.now(timezone.utc)
    role = Role(
        id=uuid4(),
        name="agent",
        label="Agent",
        description="Consults and updates assigned missions.",
        created_at=now,
        updated_at=now,
    )

    payload = role.to_dict()

    assert payload["id"] == str(role.id)
    assert payload["created_at"] == now.isoformat()
    assert payload["updated_at"] == now.isoformat()
    assert payload["name"] == "agent"
    assert payload["label"] == "Agent"


def test_account_activation_token_lifecycle_in_memory():
    user_id = uuid4()
    token, raw_token = AccountActivationToken.create_for_user(user_id)

    assert token.user_id == user_id
    assert token.verify_token(raw_token)
    assert not token.is_used()
    assert not token.is_expired()

    token.mark_as_used()

    assert token.is_used()


def test_password_reset_token_lifecycle_in_memory():
    user_id = uuid4()
    token, raw_token = PasswordResetToken.create_for_user(user_id)

    assert token.user_id == user_id
    assert token.verify_token(raw_token)
    assert not token.is_used()
    assert not token.is_expired()

    token.mark_as_used()

    assert token.is_used()


def test_refresh_token_rotation_marks_token_invalid():
    user_id = uuid4()
    token, raw_token = RefreshToken.create_for_user(user_id)
    replacement_raw_token = generate_raw_token()

    assert token.user_id == user_id
    assert token.verify_token(raw_token)
    assert token.is_valid()

    token.rotate(replacement_raw_token)

    assert token.is_revoked()
    assert token.is_replaced()
    assert not token.is_valid()
    assert token.replaced_by_token_hash == hash_token(replacement_raw_token)
