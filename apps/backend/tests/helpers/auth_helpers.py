"""Authentication helper functions used by route tests."""


def auth_headers(access_token: str) -> dict[str, str]:
    """Return the Authorization header expected by protected routes."""
    return {"Authorization": f"Bearer {access_token}"}
