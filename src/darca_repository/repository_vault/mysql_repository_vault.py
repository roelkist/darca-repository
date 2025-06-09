from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.exc import ProgrammingError

from darca_repository.config import get_config
from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.repository_vault.interfaces import RepositoryVault
from darca_repository.repository_vault.models import Repository


class Base(DeclarativeBase):
    pass


class RepositoryTable(Base):
    __tablename__ = "repositories"

    repository_name: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]]
    tags: Mapped[Optional[List[str]]] = mapped_column(sa.JSON)
    priority: Mapped[Optional[int]]
    creation_time: Mapped[str]
    modification_time: Mapped[str]
    repository_id: Mapped[Optional[int]] = mapped_column(sa.Integer, autoincrement=True)


class MySQLRepositoryVault(RepositoryVault):
    def __init__(self):
        cfg = get_config()
        url = f"mysql+asyncmy://{cfg.mysql_user}:{cfg.mysql_password}@{cfg.mysql_host}/{cfg.mysql_database}"
        self._engine = sa_async.create_async_engine(url, future=True)
        self._sessionmaker = sa_async.async_sessionmaker(self._engine, expire_on_commit=False)
        self._schema_initialized = False

    async def _ensure_schema(self):
        if not self._schema_initialized:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._schema_initialized = True

    async def get_repository(self, name: str) -> Repository:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryTable).where(RepositoryTable.repository_name == name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise RepositoryNotFoundError(name)
            return self._to_model(row)

    async def list_repositories(self, tag: Optional[str] = None) -> List[Repository]:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryTable)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            if tag:
                rows = [r for r in rows if r.tags and tag in r.tags]
            return [self._to_model(r) for r in rows]

    async def create_repository(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        repo = RepositoryTable(
            repository_name=name,
            description=description,
            tags=tags,
            priority=priority,
            creation_time=now,
            modification_time=now,
        )
        try:
            async with self._sessionmaker() as session:
                session.add(repo)
                await session.commit()
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                await self._ensure_schema()
                await self.create_repository(name, description=description, tags=tags, priority=priority)
            else:
                raise

    async def remove_repository(self, name: str) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.delete(RepositoryTable).where(RepositoryTable.repository_name == name)
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise RepositoryNotFoundError(name)
            await session.commit()

    async def update_description(self, name: str, description: Optional[str]) -> None:
        await self._update_field(name, {"description": description})

    async def update_tags(self, name: str, tags: Optional[List[str]]) -> None:
        await self._update_field(name, {"tags": tags})

    async def update_priority(self, name: str, priority: Optional[int]) -> None:
        await self._update_field(name, {"priority": priority})

    async def _update_field(self, name: str, updates: dict) -> None:
        updates["modification_time"] = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            stmt = sa.update(RepositoryTable).where(
                RepositoryTable.repository_name == name
            ).values(**updates)
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise RepositoryNotFoundError(name)
            await session.commit()

    def _to_model(self, row: RepositoryTable) -> Repository:
        return Repository(
            repository_name=row.repository_name,
            description=row.description,
            tags=row.tags,
            priority=row.priority,
            creation_time=row.creation_time,
            modification_time=row.modification_time,
            repository_id=row.repository_id,
        )
