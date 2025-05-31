# tests/conftest.py
# License: MIT

import pytest

from darca_repository.models import Repository, StorageScheme


@pytest.fixture
def repository_no_credentials(tmp_path):
    path = tmp_path / "darca_test_repo"
    path.mkdir(parents=True, exist_ok=True)

    return Repository(
        name="test-no-auth",
        storage_url=f"file://{path}",
        scheme=StorageScheme.FILE,
        tags={"env": "test"},
    )


@pytest.fixture
def repository_with_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("DUMMY_TOKEN", "secret123")
    path = tmp_path / "darca_test_repo_secure"
    path.mkdir(parents=True, exist_ok=True)

    return Repository(
        name="test-auth",
        storage_url=f"file://{path}",
        scheme=StorageScheme.FILE,
        credentials={"token": "${DUMMY_TOKEN}"},
        parameters={"cache": "false"},
        tags={"secure": "yes"},
    )
