# registry/yaml_registry.py

import os
from typing import List, Optional
from pathlib import Path

import yaml
import aiofiles

from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.registry.models import RegistryProfile
from darca_repository.registry.interfaces import Registry
from darca_repository.config import get_config


class YamlRegistry(Registry):
    """
    Async YAML-backed implementation of the Registry interface.

    Each profile is stored in its own file under `registry_profile_dir`.
    """

    def __init__(self, base_path: Optional[Path] = None):
        cfg = get_config()
        self._directory = Path(base_path or cfg.registry_profile_dir).expanduser().resolve()
        self._directory.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, name: str) -> Path:
        return self._directory / f"{name}.yaml"

    async def get_profile(self, name: str) -> RegistryProfile:
        path = self._get_file_path(name)
        if not path.exists():
            raise RepositoryNotFoundError(name)
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
        data = yaml.safe_load(content)
        return RegistryProfile(**data)

    async def list_profiles(self, *, enabled_only: bool = False, tag: Optional[str] = None) -> List[RegistryProfile]:
        results = []
        for file in self._directory.glob("*.yaml"):
            async with aiofiles.open(file, "r") as f:
                content = await f.read()
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                continue
            profile = RegistryProfile(**data)
            if enabled_only and not profile.enabled:
                continue
            if tag and (not profile.tags or tag not in profile.tags):
                continue
            results.append(profile)
        return results

    async def add_profile(self, profile: RegistryProfile) -> None:
        path = self._get_file_path(profile.name)
        async with aiofiles.open(path, "w") as f:
            await f.write(yaml.safe_dump(profile.model_dump(mode="json")))

    async def remove_profile(self, name: str) -> None:
        path = self._get_file_path(name)
        if not path.exists():
            raise RepositoryNotFoundError(name)
        path.unlink()

    async def reload(self) -> None:
        # No-op for compatibility; data is always loaded from file
        return
