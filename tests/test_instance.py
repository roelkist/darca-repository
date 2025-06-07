# tests/test_instance.py
# License: MIT

import pytest
from darca_repository.exceptions import RepositoryConnectionError
from darca_repository.instance import RepositoryInstance

@pytest.mark.asyncio
async def test_connect_without_credentials(repository_no_credentials):
    instance = RepositoryInstance(repository_no_credentials)
    client = await instance.connect()

    assert client is not None
    assert client.session["repository_name"] == "test_no_auth"
    assert client.session["scheme"] == "file"
    assert client.session["tags"] == {"env": "test"}

    ctx = client.context()
    assert ctx["user"] is None
    assert ctx["backend_type"] == "ScopedFileBackend"
    assert ctx["credentials"] is None

@pytest.mark.asyncio
async def test_connect_with_credentials(repository_with_credentials):
    instance = RepositoryInstance(repository_with_credentials)
    client = await instance.connect()

    assert client is not None
    assert client.credentials["token"] == "secret123"
    assert client.session["repository_name"] == "test_auth"
    assert client.session["tags"] == {"secure": "yes"}

    ctx = client.context()
    assert "token" in client.credentials
    assert ctx["credentials"]["token"] == "***"

@pytest.mark.asyncio
async def test_reconnect_is_idempotent(repository_no_credentials):
    instance = RepositoryInstance(repository_no_credentials)
    client1 = await instance.connect()
    client2 = await instance.connect()
    assert client1 is client2

@pytest.mark.asyncio
async def test_test_connection_success(repository_no_credentials):
    instance = RepositoryInstance(repository_no_credentials)
    assert await instance.test_connection() is True

@pytest.mark.asyncio
async def test_connection_failure(monkeypatch, repository_no_credentials):
    from darca_storage.factory import StorageConnectorFactory

    async def broken_factory(*args, **kwargs):
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(StorageConnectorFactory, "from_url", broken_factory)

    instance = RepositoryInstance(repository_no_credentials)
    with pytest.raises(RepositoryConnectionError) as exc:
        await instance.connect()

    assert "Failed to connect to repository" in str(exc.value)
