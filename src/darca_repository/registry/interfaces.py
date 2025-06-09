# registry/interfaces.py
# License: MIT

from abc import ABC, abstractmethod
from typing import List, Optional

from darca_repository.registry.models import RegistryProfile


class Registry(ABC):
    """
    Abstract interface for loading and managing repository profiles.

    Implementations may load profiles from:
    - Local YAML files
    - SQL databases (MySQL, PostgreSQL, etc.)
    - Remote config services
    """

    @abstractmethod
    def get_profile(self, name: str) -> RegistryProfile:
        """
        Retrieve a single repository profile by its name.

        Raises:
            RepositoryNotFoundError: if the profile does not exist.
        """
        ...

    @abstractmethod
    def list_profiles(self, *, enabled_only: bool = False, tag: Optional[str] = None) -> List[RegistryProfile]:
        """
        Return a list of all available repository profiles.

        Args:
            enabled_only (bool): If True, filters to enabled repositories only.
            tag (str | None): If provided, filters to repositories containing the tag.
        """
        ...

    @abstractmethod
    def add_profile(self, repository: RegistryProfile) -> None:
        """
        Add or overwrite a repository profile.
        """
        ...

    @abstractmethod
    def remove_profile(self, name: str) -> None:
        """
        Delete a repository profile by name.

        Raises:
            RepositoryNotFoundError: if the profile does not exist.
        """
        ...
