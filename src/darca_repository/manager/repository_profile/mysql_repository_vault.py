from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, selectinload
from sqlalchemy.exc import ProgrammingError

from darca_repository.config import get_config
from darca_repository.exceptions import RepositoryNotFoundError
from darca_repository.repository_vault.interfaces import RepositoryVault
from darca_repository.repository_vault.models import Repository


class Base(DeclarativeBase):
    pass


class RepositoryTable(Base):
    __tablename__ = "repositories"

    repository_name: Mapped[str] = mapped_column(sa.String(255), primary_key=True)
    priority: Mapped[Optional[int]] = mapped_column(sa.Integer)
    creation_time: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    modification_time: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    description_entry: Mapped["RepositoryDescriptionTable"] = relationship("RepositoryDescriptionTable", back_populates="repository", uselist=False, cascade="all, delete-orphan")
    tags_entry: Mapped["RepositoryTagsTable"] = relationship("RepositoryTagsTable", back_populates="repository", uselist=False, cascade="all, delete-orphan")


class RepositoryDescriptionTable(Base):
    __tablename__ = "repository_descriptions"

    repository_name: Mapped[str] = mapped_column(sa.String(255), sa.ForeignKey("repositories.repository_name", ondelete="CASCADE"), primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(sa.Text)

    repository: Mapped[RepositoryTable] = relationship("RepositoryTable", back_populates="description_entry")


class RepositoryTagsTable(Base):
    __tablename__ = "repository_tags"

    repository_name: Mapped[str] = mapped_column(sa.String(255), sa.ForeignKey("repositories.repository_name", ondelete="CASCADE"), primary_key=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(sa.JSON)

    repository: Mapped[RepositoryTable] = relationship("RepositoryTable", back_populates="tags_entry")


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

    async def create_repository(self, name: str, *, description=None, tags=None, priority=None):
        now = datetime.utcnow().isoformat()
        try:
            async with self._sessionmaker() as session:
                repo = RepositoryTable(
                    repository_name=name,
                    priority=priority,
                    creation_time=now,
                    modification_time=now
                )
                session.add(repo)
                session.add_all([
                    RepositoryDescriptionTable(repository_name=name, description=description),
                    RepositoryTagsTable(repository_name=name, tags=tags)
                ])
                await session.commit()
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                await self._ensure_schema()
                await self.create_repository(name, description=description, tags=tags, priority=priority)
            else:
                raise

    async def get_repository(self, name: str) -> Repository:
        try:
            async with self._sessionmaker() as session:
                stmt = sa.select(RepositoryTable).options(
                    selectinload(RepositoryTable.description_entry),
                    selectinload(RepositoryTable.tags_entry)
                ).where(RepositoryTable.repository_name == name)
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row is None:
                    raise RepositoryNotFoundError(name)
                return self._to_model(row)
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                raise RepositoryNotFoundError(name)
            raise

    async def list_repositories(self, tag: Optional[str] = None) -> List[Repository]:
        try:
            async with self._sessionmaker() as session:
                stmt = sa.select(RepositoryTable).options(
                    selectinload(RepositoryTable.description_entry),
                    selectinload(RepositoryTable.tags_entry)
                )
                result = await session.execute(stmt)
                rows = result.scalars().all()
                if tag:
                    rows = [r for r in rows if r.tags_entry and r.tags_entry.tags and tag in r.tags_entry.tags]
                return [self._to_model(r) for r in rows]
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                return []
            raise

    async def remove_repository(self, name: str) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryTable).where(RepositoryTable.repository_name == name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise RepositoryNotFoundError(name)
            await session.delete(row)
            await session.commit()

    async def update_description(self, name: str, description: Optional[str]) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryDescriptionTable).where(RepositoryDescriptionTable.repository_name == name)
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()
            if not entry:
                raise RepositoryNotFoundError(name)
            entry.description = description
            await session.commit()

    async def update_tags(self, name: str, tags: Optional[List[str]]) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryTagsTable).where(RepositoryTagsTable.repository_name == name)
            result = await session.execute(stmt)
            entry = result.scalar_one_or_none()
            if not entry:
                raise RepositoryNotFoundError(name)
            entry.tags = tags
            await session.commit()

    async def update_priority(self, name: str, priority: Optional[int]) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryTable).where(RepositoryTable.repository_name == name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise RepositoryNotFoundError(name)
            row.priority = priority
            row.modification_time = datetime.utcnow().isoformat()
            await session.commit()

    def _to_model(self, row: RepositoryTable) -> Repository:
        return Repository(
            repository_name=row.repository_name,
            description=row.description_entry.description if row.description_entry else None,
            tags=row.tags_entry.tags if row.tags_entry else None,
            priority=row.priority,
            creation_time=row.creation_time,
            modification_time=row.modification_time,
            repository_id=None
        )
