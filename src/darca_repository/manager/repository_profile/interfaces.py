# repository_vault/interfaces.py

from abc import ABC, abstractmethod
from typing import List, Optional
from darca_repository.repository_vault.models import Repository


class RepositoryVault(ABC):
    """Async interface for managing repositories."""

    @abstractmethod
    async def create_repository(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None,
    ) -> None:
        ...

    @abstractmethod
    async def get_repository(self, name: str) -> Repository:
        ...

    @abstractmethod
    async def list_repositories(self, *, tag: Optional[str] = None) -> List[Repository]:
        ...

    @abstractmethod
    async def remove_repository(self, name: str) -> None:
        ...

    @abstractmethod
    async def update_description(self, name: str, description: Optional[str]) -> None:
        ...

    @abstractmethod
    async def update_tags(self, name: str, tags: Optional[List[str]]) -> None:
        ...

    @abstractmethod
    async def update_priority(self, name: str, priority: Optional[int]) -> None:
        ...
