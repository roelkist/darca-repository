# tests/test_instance.py
# License: MIT

import pytest
from darca_repository.models import Repository, StorageScheme
from darca_repository.instance import RepositoryInstance
from darca_repository.exceptions import RepositoryConnectionError

@pytest.fixture
def minimal_repository():
    return Repository(
        name="integration-repo",
        storage_url="file:///tmp/test-repo",
        scheme=StorageScheme.FILE,
        parameters={"base_path": "test-data"}
    )

@pytest.mark.asyncio
async def test_repository_instance_connection(minimal_repository):
    instance = RepositoryInstance(minimal_repository)
    client = await instance.connect()
    assert client is not None
    assert instance.client is client
    assert await instance.test_connection()

@pytest.mark.asyncio
async def test_repository_write_and_read(minimal_repository):
    instance = RepositoryInstance(minimal_repository)
    client = await instance.connect()

    await client.write("foo.txt", "bar")
    content = await client.read("foo.txt")
    assert content == "bar"
