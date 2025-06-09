import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
from sqlalchemy.dialects.mysql import JSON
from typing import List, Optional
from datetime import datetime

from darca_repository.object_vault.interfaces import ObjectVault
from darca_repository.object_vault.models import RepositoryObject
from darca_repository.exceptions import ObjectNotFoundError
from darca_repository.config import get_config


class Base(DeclarativeBase):
    pass


class ObjectTable(Base):
    __tablename__ = "repository_objects"

    repository_name: Mapped[str] = mapped_column(primary_key=True)
    object_path: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[Optional[str]]
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    creation_time: Mapped[str]
    modification_time: Mapped[Optional[str]]
    object_id: Mapped[Optional[int]] = mapped_column(sa.Integer)

    def to_model(self) -> RepositoryObject:
        return RepositoryObject(
            object_path=self.object_path,
            type=self.type,
            metadata=self.metadata,
            creation_time=self.creation_time,
            modification_time=self.modification_time,
            object_id=self.object_id,
        )


class MySQLObjectVault(ObjectVault):
    def __init__(self):
        cfg = get_config()
        url = f"mysql+asyncmy://{cfg.mysql_user}:{cfg.mysql_password}@{cfg.mysql_host}/{cfg.mysql_database}"
        self._engine = sa_async.create_async_engine(url, future=True)
        self._sessionmaker = sa_async.async_sessionmaker(self._engine, expire_on_commit=False)

    async def _get(self, repository_name: str, object_path: str) -> ObjectTable:
        async with self._sessionmaker() as session:
            stmt = sa.select(ObjectTable).where(
                ObjectTable.repository_name == repository_name,
                ObjectTable.object_path == object_path,
            )
            result = await session.scalar(stmt)
            if not result:
                raise ObjectNotFoundError(repository_name, object_path)
            return result

    async def get_object(self, repository_name: str, object_path: str) -> RepositoryObject:
        row = await self._get(repository_name, object_path)
        return row.to_model()

    async def list_objects(self, repository_name: str) -> List[RepositoryObject]:
        async with self._sessionmaker() as session:
            stmt = sa.select(ObjectTable).where(ObjectTable.repository_name == repository_name)
            results = await session.scalars(stmt)
            return [r.to_model() for r in results]

    async def add_object(
        self,
        repository_name: str,
        object_path: str,
        *,
        type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        obj = ObjectTable(
            repository_name=repository_name,
            object_path=object_path,
            type=type,
            metadata=metadata,
            creation_time=now,
            modification_time=now,
        )
        async with self._sessionmaker() as session:
            session.add(obj)
            await session.commit()

    async def remove_object(self, repository_name: str, object_path: str) -> None:
        async with self._sessionmaker() as session:
            stmt = sa.delete(ObjectTable).where(
                ObjectTable.repository_name == repository_name,
                ObjectTable.object_path == object_path,
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise ObjectNotFoundError(repository_name, object_path)
            await session.commit()

    async def update_type(self, repository_name: str, object_path: str, type: Optional[str]) -> None:
        obj = await self._get(repository_name, object_path)
        obj.type = type
        obj.modification_time = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            session.add(obj)
            await session.commit()

    async def update_metadata(self, repository_name: str, object_path: str, metadata: Optional[dict]) -> None:
        obj = await self._get(repository_name, object_path)
        obj.metadata = metadata
        obj.modification_time = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            session.add(obj)
            await session.commit()

    async def touch_object(self, repository_name: str, object_path: str) -> None:
        obj = await self._get(repository_name, object_path)
        obj.modification_time = datetime.utcnow().isoformat()
        async with self._sessionmaker() as session:
            session.add(obj)
            await session.commit()
