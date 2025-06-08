# src/darca_repository/registry/factory.py

import os
from importlib.metadata import entry_points

from darca_repository.registry.interfaces import Registry
from darca_repository.registry.yaml_registry import YamlRegistry


def get_repository_registry() -> Registry:
    """
    Factory to instantiate the appropriate Registry backend
    based on the DARCA_REPOSITORY_MODE environment variable.
    """
    mode = os.getenv("DARCA_REPOSITORY_MODE", "yaml").lower()

    # Entry-point plugin loading
    for entry_point in entry_points(group="darca_repository.registries"):
        if entry_point.name == mode:
            return entry_point.load()()

    if mode == "yaml":
        profile_dir = os.getenv(
            "DARCA_REPOSITORY_PROFILE_DIR",
            os.path.expanduser("~/.local/share/darca_repository/profiles"),
        )
        return YamlRegistry(profile_dir)

    if mode == "mysql":
        from darca_repository.registry.mysql_registry import MySQLRegistry

        host = os.getenv("DARCA_REPOSITORY_MYSQL_HOST", "localhost")
        user = os.getenv("DARCA_REPOSITORY_MYSQL_USER", "darca_user")
        database = os.getenv("DARCA_REPOSITORY_MYSQL_DATABASE", "darca_database")
        password = os.getenv("DARCA_REPOSITORY_MYSQL_PASSWORD", "darca_password")
        url = f"{host}/{database}"
        return MySQLRegistry(connection_url=url, user=user, password=password)

    raise ValueError(f"Unsupported DARCA_REPOSITORY_MODE: {mode}")
