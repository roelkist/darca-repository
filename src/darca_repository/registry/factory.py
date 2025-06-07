# src/darca_repository/registry/factory.py

import os
from importlib.metadata import entry_points

from darca_repository.registry.base import RepositoryRegistry
from darca_repository.registry.yaml_registry import YamlRepositoryRegistry


def get_repository_registry() -> RepositoryRegistry:
    """
    Factory to instantiate the appropriate RepositoryRegistry backend
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
        return YamlRepositoryRegistry(profile_dir)

    if mode == "mysql":
        raise NotImplementedError("MySQL registry is not implemented.")

    raise ValueError(f"Unsupported DARCA_REPOSITORY_MODE: {mode}")
