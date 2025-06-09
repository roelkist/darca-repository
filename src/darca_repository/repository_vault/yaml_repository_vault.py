import os
import yaml
import aiofiles
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from darca_repository.repository_vault.interfaces import RepositoryVault
from darca_repository.repository_vault.models import Repository
from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.config import get_config


class YamlRepositoryVault(RepositoryVault):
    def __init__(self, base_path: Optional[Path] = None):
        cfg = get_config()
        self._directory = Path(base_path or cfg.repository_vault_dir)
        self._directory.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, name: str) -> Path:
        return self._directory / f"{name}.yaml"

    async def create_repository(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        repo = Repository(
            repository_name=name,
            description=description,
            creation_time=now,
            modification_time=now,
            tags=tags,
            priority=priority,
        )
        await self._save(repo)

    async def get_repository(self, name: str) -> Repository:
        path = self._get_file_path(name)
        if not path.exists():
            raise RepositoryNotFoundError(name)
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
        data = yaml.safe_load(content)
        return Repository(**data)

    async def list_repositories(self, *, tag: Optional[str] = None) -> List[Repository]:
        results = []
        for file in self._directory.glob("*.yaml"):
            async with aiofiles.open(file, "r") as f:
                content = await f.read()
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                continue
            repo = Repository(**data)
            if tag is None or (repo.tags and tag in repo.tags):
                results.append(repo)
        return results

    async def remove_repository(self, name: str) -> None:
        path = self._get_file_path(name)
        if not path.exists():
            raise RepositoryNotFoundError(name)
        path.unlink()

    async def update_description(self, name: str, description: Optional[str]) -> None:
        repo = await self.get_repository(name)
        repo.description = description
        repo.modification_time = datetime.utcnow().isoformat()
        await self._save(repo)

    async def update_tags(self, name: str, tags: Optional[List[str]]) -> None:
        repo = await self.get_repository(name)
        repo.tags = tags
        repo.modification_time = datetime.utcnow().isoformat()
        await self._save(repo)

    async def update_priority(self, name: str, priority: Optional[int]) -> None:
        repo = await self.get_repository(name)
        repo.priority = priority
        repo.modification_time = datetime.utcnow().isoformat()
        await self._save(repo)

    async def _save(self, repo: Repository) -> None:
        path = self._get_file_path(repo.repository_name)
        async with aiofiles.open(path, "w") as f:
            await f.write(yaml.safe_dump(repo.model_dump(mode="json")))
