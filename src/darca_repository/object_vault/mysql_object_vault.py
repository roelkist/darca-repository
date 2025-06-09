import asyncio
from datetime import datetime
from typing import List, Optional, Dict

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.exc import ProgrammingError

from darca_repository.config import get_config
from darca_repository.exceptions import ObjectNotFoundError
from darca_repository.object_vault.interfaces import ObjectVault
from darca_repository.object_vault.models import RepositoryObject


class Base(DeclarativeBase):
    pass


class RepositoryObjectTable(Base):
    __tablename__ = "repository_objects"

    repository_name: Mapped[str] = mapped_column(primary_key=True)
    object_path: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[Optional[str]]
    metadata: Mapped[Optional[Dict]] = mapped_column(sa.JSON)
    creation_time: Mapped[str]
    modification_time: Mapped[str]


class MySQLObjectVault(ObjectVault):
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

    async def get_object(self, repository: str, path: str) -> RepositoryObject:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryObjectTable).where(
                RepositoryObjectTable.repository_name == repository,
                RepositoryObjectTable.object_path == path,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise ObjectNotFoundError(repository, path)
            return self._to_model(row)

    async def list_objects(self, repository: str) -> List[RepositoryObject]:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryObjectTable).where(
                RepositoryObjectTable.repository_name == repository
            )
            result = await session.execute(stmt)
            return [self._to_model(r) for r in result.scalars().all()]

    async def add_object(
        self,
        repository: str,
        path: str,
        *,
        type: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        obj = RepositoryObjectTable(
            repository_name=repository,
            object_path=path,
            type=type,
            metadata=metadata,
            creation_time=now,
            modification_time=now,
        )
        try:
            async with self._sessionmaker() as session:
                session.add(obj)
                await session.commit()
        except ProgrammingError as e:
            if "doesn't exist" in str(e):
                await self._ensure_schema()
                await self.add_object(repository, path, type=type, metadata=metadata)
            else:
                raise

    async def remove_object(self, repository: str, path: str) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.delete(RepositoryObjectTable).where(
                RepositoryObjectTable.repository_name == repository,
                RepositoryObjectTable.object_path == path,
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise ObjectNotFoundError(repository, path)
            await session.commit()

    async def update_type(self, repository: str, path: str, type: Optional[str]) -> None:
        await self._update_fields(repository, path, {"type": type})

    async def update_metadata(self, repository: str, path: str, metadata: Dict) -> None:
        await self._update_fields(repository, path, {"metadata": metadata})

    async def touch_object(self, repository: str, path: str) -> None:
        await self._update_fields(repository, path, {})

    async def _update_fields(self, repository: str, path: str, updates: dict) -> None:
        updates["modification_time"] = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            stmt = sa.update(RepositoryObjectTable).where(
                RepositoryObjectTable.repository_name == repository,
                RepositoryObjectTable.object_path == path,
            ).values(**updates)
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise ObjectNotFoundError(repository, path)
            await session.commit()

    def _to_model(self, row: RepositoryObjectTable) -> RepositoryObject:
        return RepositoryObject(
            repository_name=row.repository_name,
            object_path=row.object_path,
            type=row.type,
            metadata=row.metadata,
            creation_time=row.creation_time,
            modification_time=row.modification_time,
        )
