"""Custom application exceptions.

These are raised throughout services/routers and translated into JSON
responses by the exception handlers registered in main.py.
"""


class AppException(Exception):
    """Base class for all custom application exceptions."""

    def __init__(self, message: str, code: str, status_code: int = 500) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(f"{resource} not found", "NOT_FOUND", 404)


class ConflictError(AppException):
    """Raised when an operation conflicts with existing state (e.g. duplicate)."""

    def __init__(self, message: str = "Conflict with existing resource") -> None:
        super().__init__(message, "CONFLICT", 409)


class ForbiddenError(AppException):
    """Raised when an authenticated user lacks permission for an action."""

    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(message, "FORBIDDEN", 403)


class UnauthorizedError(AppException):
    """Raised when authentication is missing or invalid."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, "UNAUTHORIZED", 401)
