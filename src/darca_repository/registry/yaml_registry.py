# registry/yaml_registry.py
# License: MIT

import os
from typing import Dict, List

import yaml

from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.models import Repository
from darca_repository.registry.base import RepositoryRegistry


class YamlRepositoryRegistry(RepositoryRegistry):
    """
    Loads repository profiles from a YAML directory.

    Each YAML file represents a single repository profile.
    """

    def __init__(self, directory: str):
        self._directory = os.path.abspath(directory)
        self._profiles: Dict[str, Repository] = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Repository]:
        profiles = {}
        if not os.path.isdir(self._directory):
            raise FileNotFoundError(
                f"Repository directory does not exist: {self._directory}"
            )

        for fname in os.listdir(self._directory):
            if not fname.endswith(".yaml"):
                continue
            path = os.path.join(self._directory, fname)
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                profile = Repository(**data)
                profiles[profile.name] = profile

        return profiles

    def get_profile(self, name: str) -> Repository:
        try:
            return self._profiles[name]
        except KeyError:
            raise RepositoryNotFoundError(
                f"No repository named '{name}' found in {self._directory}."
            )

    def list_profiles(self) -> List[Repository]:
        return list(self._profiles.values())
