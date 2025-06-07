# tests/conftest.py
# License: MIT

import pytest
import os 
from darca_repository.models import Repository, RepositoryConnectionInfo, StorageScheme
from fastapi.testclient import TestClient
from darca_repository.main import app
from pydantic import SecretStr

@pytest.fixture(scope="session", autouse=True)
def override_env():
    os.environ["DARCA_REPOSITORY_MODE"] = "yaml"
    os.environ["DARCA_REPOSITORY_PROFILE_DIR"] = os.path.abspath("tests/system/profiles")
    os.makedirs("/tmp/darca-test-repo", exist_ok=True)
    
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def repository_no_credentials(tmp_path):
    path = tmp_path / "darca_test_repo"
    path.mkdir(parents=True, exist_ok=True)

    return Repository(
        name="test_no_auth",
        tags={"env": "test"},  # ✅ moved to top-level
        connection=RepositoryConnectionInfo(
            storage_url=f"file://{path}",
            scheme=StorageScheme.FILE,
        )
    )

@pytest.fixture
def repository_with_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("DUMMY_TOKEN", "secret123")
    path = tmp_path / "darca_test_repo_secure"
    path.mkdir(parents=True, exist_ok=True)

    return Repository(
        name="test_auth",
        tags={"secure": "yes"},  # ✅ moved to top-level
        connection=RepositoryConnectionInfo(
            storage_url=f"file://{path}",
            scheme=StorageScheme.FILE,
            credentials={"token": SecretStr("${DUMMY_TOKEN}")},
            parameters={"cache": "false"},
        )
    )
