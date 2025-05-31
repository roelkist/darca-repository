# registry/mysql_registry.py
# License: MIT

from typing import List

from darca_repository.models import Repository
from darca_repository.registry.base import RepositoryRegistry


class MySQLRepositoryRegistry(RepositoryRegistry):
    """
    Future implementation: MySQL-backed repository registry.

    Intended to support centralized, mutable repository configurations.
    """

    def __init__(self, connection_url: str, user: str, password: str):
        # Placeholder attributes
        self._connection_url = connection_url
        self._user = user
        self._password = password
        raise NotImplementedError(
            "MySQLRepositoryRegistry is not yet implemented."
        )

    def get_profile(self, name: str) -> Repository:
        raise NotImplementedError

    def list_profiles(self) -> List[Repository]:
        raise NotImplementedError
