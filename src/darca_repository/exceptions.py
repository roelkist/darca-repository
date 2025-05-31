# exceptions.py
# License: MIT

from darca_exception import DarcaException


class RepositoryException(DarcaException):
    """
    General-purpose exception for repository-related failures.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "REPOSITORY_ERROR",
        metadata: dict | None = None,
        cause: Exception | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            metadata=metadata,
            cause=cause,
        )


class RepositoryNotFound(RepositoryException):
    def __init__(self, name: str):
        super().__init__(
            message=f"Repository '{name}' not found.",
            error_code="REPOSITORY_NOT_FOUND",
            metadata={"repository": name},
        )


class RepositoryNotFoundError(RepositoryException):
    def __init__(self, name: str):
        super().__init__(
            message=f"Repository '{name}' not found.",
            error_code="REPOSITORY_NOT_FOUND_ERROR",
            metadata={"repository": name},
        )


class RepositoryConnectionError(RepositoryException):
    def __init__(
        self, name: str, *, message: str = None, cause: Exception = None
    ):
        super().__init__(
            message=message or f"Connection failed to repository '{name}'.",
            error_code="REPOSITORY_CONNECTION_ERROR",
            metadata={"repository": name},
            cause=cause,
        )


class RepositoryAccessDenied(RepositoryException):
    def __init__(self, name: str, user: str | None = None):
        super().__init__(
            message=f"Access denied to repository '{name}' for user '{user}'.",
            error_code="REPOSITORY_ACCESS_DENIED",
            metadata={"repository": name, "user": user},
        )


class RepositoryValidationError(RepositoryException):
    """Raised when a repository fails validation checks."""

    def __init__(self, message: str, *, cause: Exception = None):
        super().__init__(
            message=message,
            error_code="REPOSITORY_VALIDATION_ERROR",
            metadata=None,
            cause=cause,
        )
