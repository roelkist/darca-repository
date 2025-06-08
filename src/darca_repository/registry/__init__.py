# registry/__init__.py
# License: MIT

from darca_repository.registry.interfaces import Registry
from darca_repository.registry.factory import get_repository_registry

__all__ = [
    "Registry",
    "get_repository_registry",
]
