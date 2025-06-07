# tests/test_exceptions.py

from darca_repository.exceptions import (
    RepositoryException,
    RepositoryNotFound,
    RepositoryNotFoundError,
    RepositoryConnectionError,
    RepositoryAccessDenied,
    RepositoryValidationError,
)


def test_repository_exception_base():
    exc = RepositoryException("Generic failure", metadata={"key": "value"})
    assert exc.message == "Generic failure"
    assert exc.metadata["key"] == "value"


def test_repository_not_found():
    exc = RepositoryNotFound(name="demo")
    assert exc.error_code == "REPOSITORY_NOT_FOUND"
    assert "demo" in str(exc)


def test_repository_not_found_error():
    exc = RepositoryNotFoundError(name="demo")
    assert exc.error_code == "REPOSITORY_NOT_FOUND_ERROR"


def test_repository_connection_error():
    cause = ValueError("bad url")
    exc = RepositoryConnectionError(name="repo1", message="fail", cause=cause)
    assert exc.error_code == "REPOSITORY_CONNECTION_ERROR"
    assert exc.cause == cause


def test_repository_access_denied():
    exc = RepositoryAccessDenied(name="repo2", user="alice")
    assert "alice" in exc.message
    assert exc.error_code == "REPOSITORY_ACCESS_DENIED"


def test_repository_validation_error():
    exc = RepositoryValidationError("invalid config")
    assert exc.error_code == "REPOSITORY_VALIDATION_ERROR"
