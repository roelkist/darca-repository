# src/darca_repository/server/dependencies.py

from functools import lru_cache
from darca_repository.registry.factory import get_repository_registry

@lru_cache
def get_registry():
    return get_repository_registry()
