class AppError(Exception):
    """Base exception type for errors that should become API responses."""

    status_code = 400

    def __init__(self, message, status_code=None):
        """Store the public error message and optional HTTP status code."""
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        """Serialize the error in the response format used by routes."""
        return {"error": self.message}


class ValidationError(AppError):
    """Raised when client-provided data fails validation."""

    status_code = 400


class AuthenticationError(AppError):
    """Raised when credentials or session tokens are invalid."""

    status_code = 401


class AuthorizationError(AppError):
    """Raised when an authenticated user lacks required permissions."""

    status_code = 403


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = 404


class ConflictError(AppError):
    """Raised when the requested operation conflicts with current state."""

    status_code = 409


class GoneError(AppError):
    """Raised when a previously valid resource is expired or consumed."""

    status_code = 410
