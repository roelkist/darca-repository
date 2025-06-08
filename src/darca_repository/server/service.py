# src/darca_repository/server/service.py
# License: MIT

from typing import Dict

from darca_repository.registry.interfaces import RepositoryRegistry
from darca_repository.instance import RepositoryInstance

# In-memory cache for repository instances (process-wide)
_repository_instance_cache: Dict[str, RepositoryInstance] = {}


async def get_or_create_instance(name: str, registry: RepositoryRegistry) -> RepositoryInstance:
    """
    Retrieves or creates a cached RepositoryInstance for the given repository name.
    Ensures that only one active instance exists per repository in memory.
    """
    if name not in _repository_instance_cache:
        profile = registry.get_profile(name)
        instance = RepositoryInstance(profile)
        await instance.connect()
        _repository_instance_cache[name] = instance

    return _repository_instance_cache[name]


async def connect_to_repository(name: str, registry: RepositoryRegistry) -> bool:
    """
    Tests whether a repository is reachable by probing its root directory.
    """
    instance = await get_or_create_instance(name, registry)
    return await instance.test_connection()


async def clear_instance_cache(name: str) -> None:
    """
    Disconnect and remove a repository instance from the cache.
    Useful for teardown or reload operations.
    """
    instance = _repository_instance_cache.pop(name, None)
    if instance:
        await instance.disconnect()
