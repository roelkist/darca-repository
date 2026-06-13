import yaml
import aiofiles
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from darca_repository.config import get_config
from darca_repository.manager.interfaces import RepositoryManager
from darca_repository.manager.models import RepositoryBinding
from darca_repository.manager.repository_store.factory import get_repository_vault
from darca_repository.manager.registry_profile.factory import get_repository_registry
from darca_repository.manager.object_store.factory import get_object_vault
from darca_repository.manager.repository_store.models import Repository
from darca_repository.manager.object_store.models import BucketObject
from darca_repository.exceptions import RepositoryNotFoundError, ObjectNotFoundError


class YamlRepositoryManager(RepositoryManager):
    def __init__(self):
        cfg = get_config()
        self._binding_file = Path(cfg.repository_vault_dir) / "_bindings.yaml"
        self._bindings: List[RepositoryBinding] = []
        self._vault = get_repository_vault()
        self._registry = get_repository_registry()
        self._objects = get_object_vault()

    async def _load_bindings(self):
        if not self._binding_file.exists():
            self._bindings = []
            return
        async with aiofiles.open(self._binding_file, "r") as f:
            raw = await f.read()
        data = yaml.safe_load(raw) or []
        self._bindings = [RepositoryBinding(**b) for b in data]

    async def _save_bindings(self):
        async with aiofiles.open(self._binding_file, "w") as f:
            await f.write(yaml.safe_dump([b.model_dump(mode="json") for b in self._bindings]))

    async def create_repository(self, name: str, profile_name: str, *, description=None, tags=None, priority=None) -> RepositoryBinding:
        await self._load_bindings()

        if any(b.repository_name == name for b in self._bindings):
            raise ValueError(f"Repository '{name}' already exists.")

        profile = await self._registry.get_profile(profile_name)
        await self._vault.create_repository(name, description=description, tags=tags, priority=priority)

        repo = await self._vault.get_repository(name)
        binding = RepositoryBinding(
            binding_id=len(self._bindings) + 1,
            repository_id=repo.repository_id or hash(name),
            profile_id=profile.profile_id or hash(profile_name),
            bucket_id=repo.repository_id or hash(name),
            repository_name=name,
            created_at=datetime.utcnow().isoformat(),
        )
        self._bindings.append(binding)
        await self._save_bindings()
        return binding

    async def get_repository_binding(self, name: str) -> RepositoryBinding:
        await self._load_bindings()
        for b in self._bindings:
            if b.repository_name == name:
                return b
        raise RepositoryNotFoundError(name)

    async def list_repositories(self, tag: Optional[str] = None) -> List[RepositoryBinding]:
        await self._load_bindings()
        if tag is None:
            return self._bindings
        filtered = []
        for b in self._bindings:
            try:
                repo = await self._vault.get_repository(b.repository_name)
                if repo.tags and tag in repo.tags:
                    filtered.append(b)
            except RepositoryNotFoundError:
                continue
        return filtered

    async def remove_repository(self, name: str) -> None:
        await self._load_bindings()
        self._bindings = [b for b in self._bindings if b.repository_name != name]
        await self._save_bindings()
        await self._vault.remove_repository(name)

    async def list_objects(self, repository_name: str) -> List[BucketObject]:
        return await self._objects.list_objects(repository_name)

    async def get_object(self, repository_name: str, object_path: str) -> BucketObject:
        return await self._objects.get_object(repository_name, object_path)

    async def add_object(self, repository_name: str, object_path: str, *, type=None, metadata=None) -> None:
        await self._load_bindings()
        if not any(b.repository_name == repository_name for b in self._bindings):
            raise RepositoryNotFoundError(repository_name)
        await self._objects.add_object(repository_name, object_path, type=type, metadata=metadata)

    async def remove_object(self, repository_name: str, object_path: str) -> None:
        await self._objects.remove_object(repository_name, object_path)

    async def update_object_type(self, repository_name: str, object_path: str, type: Optional[str]) -> None:
        await self._objects.update_type(repository_name, object_path, type)

    async def touch_object(self, repository_name: str, object_path: str) -> None:
        await self._objects.touch_object(repository_name, object_path)
