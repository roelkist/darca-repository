from abc import ABC, abstractmethod
from typing import List, Optional
from darca_repository.manager.models import RepositoryBinding
from darca_repository.manager.object_vault.models import BucketObject


class RepositoryManager(ABC):
    """
    Public API for managing DARCA repositories and their contents.
    Internally binds each repository to a registry profile and object vault bucket.
    """

    # ─────────────────────────────
    # Repository Lifecycle
    # ─────────────────────────────

    @abstractmethod
    async def create_repository(
        self,
        name: str,
        profile_name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None,
    ) -> RepositoryBinding:
        """
        Creates a new repository and binds it to a named registry profile.
        Repository name also serves as object bucket name.
        """
        ...

    @abstractmethod
    async def get_repository_binding(self, name: str) -> RepositoryBinding:
        ...

    @abstractmethod
    async def list_repositories(self, tag: Optional[str] = None) -> List[RepositoryBinding]:
        ...

    @abstractmethod
    async def remove_repository(self, name: str) -> None:
        ...

    # ─────────────────────────────
    # Object Lifecycle
    # ─────────────────────────────

    @abstractmethod
    async def list_objects(self, repository_name: str) -> List[BucketObject]:
        ...

    @abstractmethod
    async def get_object(self, repository_name: str, object_path: str) -> BucketObject:
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
    async def update_object_type(self, repository_name: str, object_path: str, type: Optional[str]) -> None:
        ...

    @abstractmethod
    async def touch_object(self, repository_name: str, object_path: str) -> None:
        ...
