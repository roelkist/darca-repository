# tests/test_system.py

import pytest
from darca_repository.models import Repository, StorageScheme, RepositoryConnectionInfo
from darca_repository.instance import RepositoryInstance

@pytest.mark.asyncio
async def test_repository_instance_connection(tmp_path):
    repo = Repository(
        name="unit_test_repo",
        connection=RepositoryConnectionInfo(
            storage_url=f"file://{tmp_path}",
            scheme=StorageScheme.FILE,
        )
    )
    instance = RepositoryInstance(repo)
    client = await instance.connect()
    assert await client.exists(".")

def test_list_repositories(client):
    response = client.get("/repositories/")
    assert response.status_code == 200
    data = response.json()
    assert any(repo["name"] == "test_local_repo" for repo in data)

def test_get_repository(client):
    response = client.get("/repositories/test_local_repo")
    assert response.status_code == 200
    repo = response.json()
    assert "connection" in repo
    assert repo["connection"]["storage_url"].startswith("file://")

def test_get_repository_not_found(client):
    response = client.get("/repositories/missing_repo")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_repository_connection(client):
    response = client.get("/repositories/test_local_repo/test")
    assert response.status_code == 200
    assert response.json() == {"success": True}

def test_repository_connection_failure(monkeypatch, client):
    from darca_storage.factory import StorageConnectorFactory

    async def broken_factory(*args, **kwargs):
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(StorageConnectorFactory, "from_url", broken_factory)

    response = client.get("/repositories/test_local_repo/test")
    assert response.status_code == 500
    assert "Simulated failure" in response.json()["detail"]

def test_add_repository(client, tmp_path):
    repo_data = {
        "name": "test_add",
        "connection": {
            "storage_url": f"file://{tmp_path}/add-test",
            "scheme": "file",
            "parameters": {},
            "tags": {"added": "yes"}
        }
    }
    response = client.post("/repositories/", json=repo_data)
    assert response.status_code == 200
    assert response.json()["name"] == "test_add"

def test_add_invalid_repository(client):
    bad_data = {"invalid": "field"}
    response = client.post("/repositories/", json=bad_data)
    assert response.status_code == 422

def test_delete_repository(client):
    repo_data = {
        "name": "to_delete",
        "connection": {
            "storage_url": "file:///tmp/darca-delete-test",
            "scheme": "file",
            "parameters": {},
            "tags": {}
        }
    }
    add_resp = client.post("/repositories/", json=repo_data)
    assert add_resp.status_code == 200

    delete_resp = client.delete("/repositories/to_delete")
    assert delete_resp.status_code == 200
    assert "removed" in delete_resp.json()["message"].lower()

def test_delete_missing_repository(client):
    response = client.delete("/repositories/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
