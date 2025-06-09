# exceptions.py
# License: MIT

from darca_exception import DarcaException
from typing import Optional


class RepositoryException(DarcaException):
    """
    General-purpose exception for repository-related failures.
    Supports root cause chaining and optional structured metadata.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "REPOSITORY_ERROR",
        metadata: Optional[dict] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            metadata=metadata,
            cause=cause,
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
        self, name: str, *, message: Optional[str] = None, cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message or f"Connection failed to repository '{name}'.",
            error_code="REPOSITORY_CONNECTION_ERROR",
            metadata={"repository": name},
            cause=cause,
        )


class RepositoryAccessDenied(RepositoryException):
    def __init__(self, name: str, user: Optional[str] = None):
        super().__init__(
            message=f"Access denied to repository '{name}' for user '{user}'.",
            error_code="REPOSITORY_ACCESS_DENIED",
            metadata={"repository": name, "user": user},
        )


class RepositoryValidationError(RepositoryException):
    """Raised when a repository fails validation checks."""

    def __init__(self, message: str, *, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code="REPOSITORY_VALIDATION_ERROR",
            metadata=None,
            cause=cause,
        )

class RepositoryNotConnectedError(RepositoryException):
    def __init__(self, name: str):
        super().__init__(
            message=f"Repository '{name}' is not connected.",
            error_code="REPOSITORY_NOT_CONNECTED",
            metadata={"repository": name},
        )


class RepositoryIOError(RepositoryException):
    def __init__(self, message: str, *, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code="REPOSITORY_IO_ERROR",
            cause=cause,
        )


class RepositoryAlreadyExistsError(Exception):
    def __init__(self, name: str):
        super().__init__(f"Repository '{name}' already exists.")


class ObjectNotFoundError(Exception):
    def __init__(self, repository_name: str, object_path: str):
        super().__init__(f"Object '{object_path}' not found in repository '{repository_name}'.")


class ObjectAlreadyExistsError(Exception):
    def __init__(self, repository_name: str, object_path: str):
        super().__init__(f"Object '{object_path}' already exists in repository '{repository_name}'.")
