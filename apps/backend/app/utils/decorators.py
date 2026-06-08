"""Reusable decorators for route-level authorization checks."""

from functools import wraps
from typing import Any, Callable

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.repositories.user_repository import UserRepository

RouteHandler = Callable[..., Any]


def require_roles(*allowed_roles: str) -> Callable[[RouteHandler], RouteHandler]:
    """Restrict access to authenticated users whose role is explicitly allowed."""

    def decorator(function: RouteHandler) -> RouteHandler:
        @wraps(function)
        @jwt_required()
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user_id = get_jwt_identity()
            current_user = UserRepository.get_by_id(user_id)

            if current_user is None:
                return {"error": "Current user not found."}, 404

            if current_user.role is None:
                return {"error": "User role is not defined."}, 403

            if current_user.role.name not in allowed_roles:
                return {"error": "You are not allowed to access this resource."}, 403

            return function(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
