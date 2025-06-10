from datetime import datetime, timezone
from typing import List, Optional

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.exc import ProgrammingError

from darca_repository.config import get_config
from darca_repository.exceptions import ObjectNotFoundError
from darca_repository.object_vault.interfaces import ObjectVault
from darca_repository.object_vault.models import BucketObject


class Base(DeclarativeBase):
    pass


class BucketTable(Base):
    __tablename__ = "buckets"

    bucket_id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    bucket_name: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    object_table_name: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    creation_time: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    modification_time: Mapped[str] = mapped_column(sa.String(64), nullable=True)


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

    def _get_object_table_class(self, table_name: str):
        class BucketObjectTable(Base):
            __tablename__ = table_name
            __table_args__ = {'extend_existing': True}

            object_id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
            object_path: Mapped[str] = mapped_column(sa.Text, nullable=False)
            type: Mapped[Optional[str]] = mapped_column(sa.String(64))
            creation_time: Mapped[str] = mapped_column(sa.String(64), nullable=False)
            modification_time: Mapped[str] = mapped_column(sa.String(64), nullable=False)

        return BucketObjectTable

    async def _get_or_create_bucket(self, name: str) -> str:
        await self._ensure_schema()
        now = datetime.now(tz=timezone.utc).isoformat()
        table_name = f"bucket_{name}_objects"

        async with self._sessionmaker() as session:
            stmt = sa.select(BucketTable).where(BucketTable.bucket_name == name)
            result = await session.execute(stmt)
            bucket = result.scalar_one_or_none()

            if bucket:
                # update modification_time
                bucket.modification_time = now
                await session.commit()
                return bucket.object_table_name

            new_bucket = BucketTable(
                bucket_name=name,
                object_table_name=table_name,
                creation_time=now,
                modification_time=now
            )
            session.add(new_bucket)
            await session.flush()

            table_cls = self._get_object_table_class(table_name)
            async with self._engine.begin() as conn:
                await conn.run_sync(table_cls.metadata.create_all)

            await session.commit()
            return table_name

    async def add_object(self, bucket: str, path: str, *, type=None, metadata=None):
        now = datetime.now(tz=timezone.utc).isoformat()
        try:
            table_name = await self._get_or_create_bucket(bucket)
            table_cls = self._get_object_table_class(table_name)
            async with self._sessionmaker() as session:
                obj = table_cls(
                    object_path=path,
                    type=type,
                    creation_time=now,
                    modification_time=now
                )
                session.add(obj)
                await session.commit()
        except ProgrammingError as e:
            if "doesn't exist" in str(e).lower():
                await self._ensure_schema()
                await self.add_object(bucket, path, type=type, metadata=metadata)
            else:
                raise

    async def get_object(self, bucket: str, path: str) -> BucketObject:
        table_name = await self._get_or_create_bucket(bucket)
        table_cls = self._get_object_table_class(table_name)
        async with self._sessionmaker() as session:
            stmt = sa.select(table_cls).where(table_cls.object_path == path)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise ObjectNotFoundError(bucket, path)
            return self._to_model(row)

    async def list_objects(self, bucket: str) -> List[BucketObject]:
        table_name = await self._get_or_create_bucket(bucket)
        table_cls = self._get_object_table_class(table_name)
        async with self._sessionmaker() as session:
            stmt = sa.select(table_cls)
            result = await session.execute(stmt)
            return [self._to_model(r) for r in result.scalars().all()]

    async def remove_object(self, bucket: str, path: str) -> None:
        table_name = await self._get_or_create_bucket(bucket)
        table_cls = self._get_object_table_class(table_name)
        async with self._sessionmaker() as session:
            stmt = sa.select(table_cls).where(table_cls.object_path == path)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise ObjectNotFoundError(bucket, path)
            await session.delete(row)
            await session.commit()

    async def update_type(self, bucket: str, path: str, type: Optional[str]) -> None:
        await self._update_fields(bucket, path, {"type": type})

    async def touch_object(self, bucket: str, path: str) -> None:
        await self._update_fields(bucket, path, {})

    async def _update_fields(self, bucket: str, path: str, updates: dict) -> None:
        updates["modification_time"] = datetime.now(tz=timezone.utc).isoformat()
        table_name = await self._get_or_create_bucket(bucket)
        table_cls = self._get_object_table_class(table_name)
        async with self._sessionmaker() as session:
            stmt = sa.select(table_cls).where(table_cls.object_path == path)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                raise ObjectNotFoundError(bucket, path)
            for key, value in updates.items():
                setattr(obj, key, value)
            await session.commit()

    def _to_model(self, row) -> BucketObject:
        return BucketObject(
            object_path=row.object_path,
            type=row.type,
            creation_time=row.creation_time,
            modification_time=row.modification_time,
        )
