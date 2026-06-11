"""Unit tests for token helpers."""

from app.utils.tokens import generate_raw_token, hash_token


def test_generate_raw_token_returns_different_values():
    first = generate_raw_token()
    second = generate_raw_token()

    assert first
    assert second
    assert first != second


def test_hash_token_is_stable_and_does_not_store_raw_value():
    raw_token = "example-token"

    first_hash = hash_token(raw_token)
    second_hash = hash_token(raw_token)

    assert first_hash == second_hash
    assert first_hash != raw_token
