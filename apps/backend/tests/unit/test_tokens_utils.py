"""Unit tests for token utility helpers."""

from __future__ import annotations

from app.utils.tokens import generate_raw_token, hash_token


def test_generate_raw_token_returns_url_safe_strings():
    first_token = generate_raw_token()
    second_token = generate_raw_token()

    assert isinstance(first_token, str)
    assert isinstance(second_token, str)
    assert first_token
    assert second_token
    assert first_token != second_token
    assert all(character.isalnum() or character in "-_" for character in first_token)
    assert all(character.isalnum() or character in "-_" for character in second_token)


def test_generate_raw_token_respects_length_argument():
    token = generate_raw_token(16)

    assert isinstance(token, str)
    assert token


def test_hash_token_is_deterministic_and_hex_encoded():
    raw_token = "cadri-token"

    hashed_first = hash_token(raw_token)
    hashed_second = hash_token(raw_token)

    assert hashed_first == hashed_second
    assert len(hashed_first) == 64
    assert all(character in "0123456789abcdef" for character in hashed_first)
