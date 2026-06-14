import os
import yaml
import aiofiles
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from darca_repository.object_vault.interfaces import ObjectVault
from darca_repository.object_vault.models import RepositoryObject
from darca_repository.exceptions import ObjectNotFoundError
from darca_repository.config import get_config


class YamlObjectVault(ObjectVault):
    def __init__(self, base_path: Optional[Path] = None):
        cfg = get_config()
        self._directory = Path(base_path or cfg.object_vault_dir)
        self._directory.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, repository_name: str) -> Path:
        return self._directory / f"{repository_name}_objects.yaml"

    async def get_object(self, repository_name: str, object_path: str) -> RepositoryObject:
        objects = await self._load(repository_name)
        for obj in objects:
            if obj.object_path == object_path:
                return obj
        raise ObjectNotFoundError(repository_name, object_path)

    async def list_objects(self, repository_name: str) -> List[RepositoryObject]:
        return await self._load(repository_name)

    async def add_object(
        self,
        repository_name: str,
        object_path: str,
        *,
        type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        objects = await self._load(repository_name)
        now = datetime.utcnow().isoformat()
        objects.append(
            RepositoryObject(
                object_path=object_path,
                type=type,
                metadata=metadata,
                creation_time=now,
                modification_time=now,
            )
        )
        await self._save(repository_name, objects)

    async def remove_object(self, repository_name: str, object_path: str) -> None:
        objects = await self._load(repository_name)
        new_objects = [o for o in objects if o.object_path != object_path]
        if len(new_objects) == len(objects):
            raise ObjectNotFoundError(repository_name, object_path)
        await self._save(repository_name, new_objects)

    async def update_type(self, repository_name: str, object_path: str, type: Optional[str]) -> None:
        obj = await self.get_object(repository_name, object_path)
        obj.type = type
        obj.modification_time = datetime.utcnow().isoformat()
        await self._replace_object(repository_name, obj)

    async def update_metadata(self, repository_name: str, object_path: str, metadata: Optional[dict]) -> None:
        obj = await self.get_object(repository_name, object_path)
        obj.metadata = metadata
        obj.modification_time = datetime.utcnow().isoformat()
        await self._replace_object(repository_name, obj)

    async def touch_object(self, repository_name: str, object_path: str) -> None:
        obj = await self.get_object(repository_name, object_path)
        obj.modification_time = datetime.utcnow().isoformat()
        await self._replace_object(repository_name, obj)

    async def _replace_object(self, repository_name: str, updated_obj: RepositoryObject) -> None:
        objects = await self._load(repository_name)
        updated = [o if o.object_path != updated_obj.object_path else updated_obj for o in objects]
        await self._save(repository_name, updated)

    async def _load(self, repository_name: str) -> List[RepositoryObject]:
        path = self._get_file_path(repository_name)
        if not path.exists():
            return []
        async with aiofiles.open(path, "r") as f:
            raw = await f.read()
        data = yaml.safe_load(raw)
        return [RepositoryObject(**item) for item in (data or [])]

    async def _save(self, repository_name: str, objects: List[RepositoryObject]) -> None:
        path = self._get_file_path(repository_name)
        async with aiofiles.open(path, "w") as f:
            await f.write(yaml.safe_dump([o.model_dump(mode="json") for o in objects]))
