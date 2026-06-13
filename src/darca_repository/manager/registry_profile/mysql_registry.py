# registry/mysql_registry.py

from typing import List, Optional
from datetime import datetime, timezone

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import ProgrammingError

from darca_repository.registry.models import RegistryProfile, StorageScheme
from darca_repository.registry.interfaces import Registry
from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.config import get_config


class Base(DeclarativeBase):
    pass


class RepositoryProfileTable(Base):
    __tablename__ = "repository_profiles"

    name: Mapped[str] = mapped_column(sa.String(255), primary_key=True)
    storage_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    scheme: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    credentials: Mapped[Optional[dict]] = mapped_column(sa.JSON, nullable=True)
    parameters: Mapped[Optional[dict]] = mapped_column(sa.JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(sa.JSON, nullable=True)


class MySQLRegistry(Registry):
    """
    Async MySQL-backed implementation of the Registry interface.
    """

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

    def _to_model(self, row: RepositoryProfileTable) -> RegistryProfile:
        return RegistryProfile(
            name=row.name,
            storage_url=row.storage_url,
            scheme=StorageScheme(row.scheme),
            credentials=row.credentials,
            parameters=row.parameters or {},
            enabled=row.enabled,
            tags=row.tags or [],
        )

    def _from_model(self, profile: RegistryProfile) -> RepositoryProfileTable:
        return RepositoryProfileTable(
            name=profile.name,
            storage_url=profile.storage_url,
            scheme=profile.scheme.value,
            credentials=profile.credentials,
            parameters=profile.parameters,
            enabled=profile.enabled,
            tags=profile.tags,
        )

    async def get_profile(self, name: str) -> RegistryProfile:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryProfileTable).where(RepositoryProfileTable.name == name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise RepositoryNotFoundError(name)
            return self._to_model(row)

    async def list_profiles(
        self, *, enabled_only: bool = False, tag: Optional[str] = None
    ) -> List[RegistryProfile]:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryProfileTable)
            if enabled_only:
                stmt = stmt.where(RepositoryProfileTable.enabled == True)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            if tag:
                rows = [r for r in rows if r.tags and tag in r.tags]
            return [self._to_model(r) for r in rows]

    async def add_profile(self, profile: RegistryProfile) -> None:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            obj = self._from_model(profile)
            await session.merge(obj)
            await session.commit()

    async def remove_profile(self, name: str) -> None:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryProfileTable).where(RepositoryProfileTable.name == name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise RepositoryNotFoundError(name)
            await session.delete(row)
            await session.commit()
