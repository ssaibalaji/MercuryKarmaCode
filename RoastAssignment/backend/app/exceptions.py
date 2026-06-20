"""Custom application exceptions.

All domain-specific errors should subclass AppException so the global
exception handler in app/main.py can convert them into a consistent
JSON error response: {"code": ..., "message": ...}.
"""


class AppException(Exception):
    """Base class for all application-specific exceptions."""

    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", "NOT_FOUND", 404)


class ConflictError(AppException):
    """Raised when an operation conflicts with the current state (e.g. duplicate)."""

    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)


class UnauthorizedError(AppException):
    """Raised when authentication is missing or invalid."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED", 401)


class ForbiddenError(AppException):
    """Raised when an authenticated user lacks permission for the resource."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN", 403)


class ValidationError(AppException):
    """Raised when input data fails validation."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR", 400)
