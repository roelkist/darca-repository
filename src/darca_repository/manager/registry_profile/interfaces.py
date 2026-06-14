# registry/interfaces.py

from abc import ABC, abstractmethod
from typing import List, Optional

from darca_repository.registry.models import RegistryProfile


class Registry(ABC):
    """
    Async interface for managing registry profiles (storage backends).

    Implementations may persist profiles via:
    - Local YAML files
    - SQL databases (e.g., MySQL)
    - Remote configuration stores
    """

    @abstractmethod
    async def get_profile(self, name: str) -> RegistryProfile:
        """
        Retrieve a repository profile by name.

        Raises:
            RepositoryNotFoundError: if the profile does not exist.
        """
        ...

    @abstractmethod
    async def list_profiles(
        self, *, enabled_only: bool = False, tag: Optional[str] = None
    ) -> List[RegistryProfile]:
        """
        List available profiles, optionally filtering by 'enabled' or tag.

        Args:
            enabled_only: Filter only enabled profiles.
            tag: Filter by presence of tag.
        """
        ...

    @abstractmethod
    async def add_profile(self, profile: RegistryProfile) -> None:
        """
        Add or overwrite a repository profile.
        """
        ...

    @abstractmethod
    async def remove_profile(self, name: str) -> None:
        """
        Delete a repository profile by name.

        Raises:
            RepositoryNotFoundError: if the profile does not exist.
        """
        ...
