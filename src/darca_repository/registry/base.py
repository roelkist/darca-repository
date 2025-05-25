# registry/base.py
# License: MIT

from abc import ABC, abstractmethod
from typing import List

from darca_repository.models import Repository


class RepositoryRegistry(ABC):
    """
    Abstract interface for loading and managing repository profiles.

    Implementations may load profiles from:
    - Local YAML files
    - SQL databases (MySQL, PostgreSQL, etc.)
    - Remote config services
    """

    @abstractmethod
    def get_profile(self, name: str) -> Repository:
        """
        Retrieve a single repository profile by its name.

        Raises:
            KeyError: if the profile does not exist.
        """
        ...

    @abstractmethod
    def list_profiles(self) -> List[Repository]:
        """
        Return a list of all available repository profiles.
        """
        ...
