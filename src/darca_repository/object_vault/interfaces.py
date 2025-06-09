from abc import ABC, abstractmethod
from typing import List, Optional
from darca_repository.object_vault.models import RepositoryObject


class ObjectVault(ABC):
    """Async interface for managing repository-scoped objects."""

    @abstractmethod
    async def get_object(self, repository_name: str, object_path: str) -> RepositoryObject:
        """Return a single object by its path."""
        ...

    @abstractmethod
    async def list_objects(self, repository_name: str) -> List[RepositoryObject]:
        """Return all objects in a repository."""
        ...

    @abstractmethod
    async def add_object(
        self,
        repository_name: str,
        object_path: str,
        *,
        type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        ...

    @abstractmethod
    async def remove_object(self, repository_name: str, object_path: str) -> None:
        ...

    @abstractmethod
    async def update_type(self, repository_name: str, object_path: str, type: Optional[str]) -> None:
        ...

    @abstractmethod
    async def update_metadata(self, repository_name: str, object_path: str, metadata: Optional[dict]) -> None:
        ...

    @abstractmethod
    async def touch_object(self, repository_name: str, object_path: str) -> None:
        ...
