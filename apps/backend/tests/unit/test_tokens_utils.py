"""Unit tests for token utility helpers."""

from app.utils.tokens import generate_raw_token, hash_token


def test_generate_raw_token_returns_string():
    token = generate_raw_token()
    assert isinstance(token, str)
    assert len(token) > 0


def test_generate_raw_token_returns_different_values():
    token_one = generate_raw_token()
    token_two = generate_raw_token()
    assert token_one != token_two


def test_hash_token_returns_deterministic_hash():
    assert hash_token("my-token") == hash_token("my-token")


def test_hash_token_returns_different_hash_for_different_inputs():
    assert hash_token("token-a") != hash_token("token-b")
