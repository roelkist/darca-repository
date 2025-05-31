# registry/factory.py
# License: MIT

import os

from darca_repository.registry.base import RepositoryRegistry

# from darca_repository.registry.mysql_registry import MySQLRepositoryRegistry
from darca_repository.registry.yaml_registry import YamlRepositoryRegistry


def get_repository_registry() -> RepositoryRegistry:
    """
    Factory to instantiate the appropriate RepositoryRegistry backend
    based on the DARCA_REPOSITORY_MODE environment variable.
    """
    mode = os.getenv("DARCA_REPOSITORY_MODE", "yaml").lower()

    if mode == "yaml":
        profile_dir = os.getenv(
            "DARCA_REPOSITORY_PROFILE_DIR",
            os.path.expanduser("~/.local/share/darca_repository/profiles"),
        )
        return YamlRepositoryRegistry(profile_dir)

    if mode == "mysql":
        raise NotImplementedError("MySQL registry is not implemented.")
        # return MySQLRepositoryRegistry(
        #     connection_url=os.getenv("DARCA_REPOSITORY_DB_URL"),
        #     user=os.getenv("DARCA_REPOSITORY_DB_USER"),
        #     password=os.getenv("DARCA_REPOSITORY_DB_PASSWORD"),
        # )

    raise ValueError(f"Unsupported DARCA_REPOSITORY_MODE: {mode}")
