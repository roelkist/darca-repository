import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
from sqlalchemy.dialects.mysql import JSON
from typing import List, Optional
from datetime import datetime

from darca_repository.repository_vault.interfaces import RepositoryVault
from darca_repository.repository_vault.models import Repository
from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.config import get_config


class Base(DeclarativeBase):
    pass


class RepositoryTable(Base):
    __tablename__ = "repositories"

    repository_name: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]]
    creation_time: Mapped[str]
    modification_time: Mapped[Optional[str]]
    priority: Mapped[Optional[int]]
    tags: Mapped[Optional[list]] = mapped_column(JSON)
    repository_id: Mapped[Optional[int]] = mapped_column(sa.Integer)

    def to_model(self) -> Repository:
        return Repository(
            repository_name=self.repository_name,
            description=self.description,
            creation_time=self.creation_time,
            modification_time=self.modification_time,
            priority=self.priority,
            tags=self.tags,
            repository_id=self.repository_id,
        )


class MySQLRepositoryVault(RepositoryVault):
    def __init__(self):
        cfg = get_config()
        url = f"mysql+asyncmy://{cfg.mysql_user}:{cfg.mysql_password}@{cfg.mysql_host}/{cfg.mysql_database}"
        self._engine = sa_async.create_async_engine(url, future=True)
        self._sessionmaker = sa_async.async_sessionmaker(self._engine, expire_on_commit=False)

    async def _get(self, name: str) -> RepositoryTable:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryTable).where(RepositoryTable.repository_name == name)
            result = await session.scalar(stmt)
            if not result:
                raise RepositoryNotFoundError(name)
            return result

    async def create_repository(self, name: str, *, description=None, tags=None, priority=None) -> None:
        now = datetime.utcnow().isoformat()
        repo = RepositoryTable(
            repository_name=name,
            description=description,
            creation_time=now,
            modification_time=now,
            tags=tags or [],
            priority=priority,
        )
        async with self._sessionmaker() as session:
            session.add(repo)
            await session.commit()

    async def get_repository(self, name: str) -> Repository:
        row = await self._get(name)
        return row.to_model()

    async def list_repositories(self, *, tag: Optional[str] = None) -> List[Repository]:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryTable)
            rows = await session.scalars(stmt)
            if tag:
                return [r.to_model() for r in rows if r.tags and tag in r.tags]
            return [r.to_model() for r in rows]

    async def remove_repository(self, name: str) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.delete(RepositoryTable).where(RepositoryTable.repository_name == name)
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise RepositoryNotFoundError(name)
            await session.commit()

    async def update_description(self, name: str, description: Optional[str]) -> None:
        repo = await self._get(name)
        repo.description = description
        repo.modification_time = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            session.add(repo)
            await session.commit()

    async def update_tags(self, name: str, tags: Optional[List[str]]) -> None:
        repo = await self._get(name)
        repo.tags = tags
        repo.modification_time = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            session.add(repo)
            await session.commit()

    async def update_priority(self, name: str, priority: Optional[int]) -> None:
        repo = await self._get(name)
        repo.priority = priority
        repo.modification_time = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            session.add(repo)
            await session.commit()
