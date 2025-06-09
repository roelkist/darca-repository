from datetime import datetime
from typing import List, Optional, Dict

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship, selectinload
from sqlalchemy.exc import ProgrammingError

from darca_repository.config import get_config
from darca_repository.exceptions import ObjectNotFoundError
from darca_repository.object_vault.interfaces import ObjectVault
from darca_repository.object_vault.models import RepositoryObject


class Base(DeclarativeBase):
    pass


class RepositoryObjectTable(Base):
    __tablename__ = "repository_objects"

    object_id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    repository_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(sa.String(64))
    creation_time: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    modification_time: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    path: Mapped["ObjectPathTable"] = relationship("ObjectPathTable", back_populates="object", uselist=False, cascade="all, delete-orphan")
    meta_entry: Mapped["ObjectMetadataTable"] = relationship("ObjectMetadataTable", back_populates="object", uselist=False, cascade="all, delete-orphan")


class ObjectPathTable(Base):
    __tablename__ = "object_paths"

    object_id: Mapped[int] = mapped_column(sa.BigInteger, sa.ForeignKey("repository_objects.object_id", ondelete="CASCADE"), primary_key=True)
    object_path: Mapped[str] = mapped_column(sa.Text, nullable=False)

    object: Mapped[RepositoryObjectTable] = relationship("RepositoryObjectTable", back_populates="path")


class ObjectMetadataTable(Base):
    __tablename__ = "object_metadata"

    object_id: Mapped[int] = mapped_column(sa.BigInteger, sa.ForeignKey("repository_objects.object_id", ondelete="CASCADE"), primary_key=True)
    meta: Mapped[Optional[Dict]] = mapped_column("metadata", sa.JSON)

    object: Mapped[RepositoryObjectTable] = relationship("RepositoryObjectTable", back_populates="meta_entry")


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

    async def add_object(self, repository: str, path: str, *, type=None, metadata=None):
        now = datetime.utcnow().isoformat()
        try:
            async with self._sessionmaker() as session:
                obj = RepositoryObjectTable(
                    repository_name=repository,
                    type=type,
                    creation_time=now,
                    modification_time=now
                )
                session.add(obj)
                await session.flush()

                session.add_all([
                    ObjectPathTable(object_id=obj.object_id, object_path=path),
                    ObjectMetadataTable(object_id=obj.object_id, meta=metadata)
                ])
                await session.commit()
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                await self._ensure_schema()
                await self.add_object(repository, path, type=type, metadata=metadata)
            else:
                raise

    async def get_object(self, repository: str, path: str) -> RepositoryObject:
        try:
            async with self._sessionmaker() as session:
                stmt = sa.select(RepositoryObjectTable).join(ObjectPathTable).options(
                    selectinload(RepositoryObjectTable.path),
                    selectinload(RepositoryObjectTable.meta_entry)
                ).where(
                    RepositoryObjectTable.repository_name == repository,
                    ObjectPathTable.object_path == path
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if not row:
                    raise ObjectNotFoundError(repository, path)
                return self._to_model(row)
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                raise ObjectNotFoundError(repository, path)
            raise

    async def list_objects(self, repository: str) -> List[RepositoryObject]:
        try:
            async with self._sessionmaker() as session:
                stmt = sa.select(RepositoryObjectTable).options(
                    selectinload(RepositoryObjectTable.path),
                    selectinload(RepositoryObjectTable.meta_entry)
                ).where(
                    RepositoryObjectTable.repository_name == repository
                )
                result = await session.execute(stmt)
                return [self._to_model(r) for r in result.scalars().all()]
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                return []
            raise

    async def remove_object(self, repository: str, path: str) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryObjectTable).join(ObjectPathTable).where(
                RepositoryObjectTable.repository_name == repository,
                ObjectPathTable.object_path == path
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise ObjectNotFoundError(repository, path)
            await session.delete(row)
            await session.commit()

    async def update_type(self, repository: str, path: str, type: Optional[str]) -> None:
        await self._update_fields(repository, path, {"type": type})

    async def update_metadata(self, repository: str, path: str, metadata: Dict) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.select(ObjectMetadataTable).select_from(
                ObjectMetadataTable
            ).join(
                RepositoryObjectTable, ObjectMetadataTable.object_id == RepositoryObjectTable.object_id
            ).join(
                ObjectPathTable, ObjectMetadataTable.object_id == ObjectPathTable.object_id
            ).where(
                RepositoryObjectTable.repository_name == repository,
                ObjectPathTable.object_path == path
            )
            result = await session.execute(stmt)
            meta_row = result.scalar_one_or_none()
            if not meta_row:
                raise ObjectNotFoundError(repository, path)
            meta_row.meta = metadata
            await session.commit()

    async def touch_object(self, repository: str, path: str) -> None:
        await self._update_fields(repository, path, {})

    async def _update_fields(self, repository: str, path: str, updates: dict) -> None:
        updates["modification_time"] = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryObjectTable).join(ObjectPathTable).where(
                RepositoryObjectTable.repository_name == repository,
                ObjectPathTable.object_path == path
            )
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                raise ObjectNotFoundError(repository, path)
            for key, value in updates.items():
                setattr(obj, key, value)
            await session.commit()

    def _to_model(self, row: RepositoryObjectTable) -> RepositoryObject:
        return RepositoryObject(
            object_path=row.path.object_path,
            type=row.type,
            metadata=row.meta_entry.meta if row.meta_entry else None,
            creation_time=row.creation_time,
            modification_time=row.modification_time,
        )
