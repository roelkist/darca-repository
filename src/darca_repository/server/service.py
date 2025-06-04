# src/darca_repository/server/service.py

from darca_repository.registry.base import RepositoryRegistry
from darca_repository.instance import RepositoryInstance

async def connect_to_repository(name: str, registry: RepositoryRegistry) -> bool:
    profile = registry.get_profile(name)
    instance = RepositoryInstance(profile)
    return await instance.test_connection()
