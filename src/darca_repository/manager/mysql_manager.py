import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import List, Optional
from datetime import datetime, timezone

from darca_repository.config import get_config
from darca_repository.manager.interfaces import RepositoryManager
from darca_repository.manager.models import RepositoryBinding
from darca_repository.manager.repository_vault.factory import get_repository_vault
from darca_repository.manager.registry_profile.factory import get_repository_registry
from darca_repository.manager.object_store.factory import get_object_vault
from darca_repository.manager.repository_vault.models import Repository
from darca_repository.manager.object_store.models import BucketObject
from darca_repository.exceptions import RepositoryNotFoundError


class Base(DeclarativeBase):
    pass


class RepositoryBindingTable(Base):
    __tablename__ = "repository_bindings"

    binding_id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int]
    profile_id: Mapped[int]
    bucket_id: Mapped[int]
    repository_name: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    updated_at: Mapped[Optional[str]] = mapped_column(sa.String(64), nullable=True)


class MySQLRepositoryManager(RepositoryManager):
    def __init__(self):
        cfg = get_config()
        url = f"mysql+asyncmy://{cfg.mysql_user}:{cfg.mysql_password}@{cfg.mysql_host}/{cfg.mysql_database}"
        self._engine = sa_async.create_async_engine(url, future=True)
        self._sessionmaker = sa_async.async_sessionmaker(self._engine, expire_on_commit=False)
        self._vault = get_repository_vault()
        self._registry = get_repository_registry()
        self._objects = get_object_vault()
        self._schema_initialized = False

    async def _ensure_schema(self):
        if not self._schema_initialized:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._schema_initialized = True

    async def create_repository(self, name: str, profile_name: str, *, description=None, tags=None, priority=None) -> RepositoryBinding:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryBindingTable).where(RepositoryBindingTable.repository_name == name)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError(f"Repository '{name}' already exists.")

            profile = await self._registry.get_profile(profile_name)
            await self._vault.create_repository(name, description=description, tags=tags, priority=priority)
            repo = await self._vault.get_repository(name)

            binding = RepositoryBindingTable(
                repository_id=repo.repository_id or hash(name),
                profile_id=profile.profile_id or hash(profile_name),
                bucket_id=repo.repository_id or hash(name),
                repository_name=name,
                created_at=datetime.now(timezone.utc).isoformat()
            )
            session.add(binding)
            await session.commit()

            return RepositoryBinding(
                binding_id=binding.binding_id,
                repository_id=binding.repository_id,
                profile_id=binding.profile_id,
                bucket_id=binding.bucket_id,
                repository_name=binding.repository_name,
                created_at=binding.created_at,
                updated_at=binding.updated_at,
            )

    async def get_repository_binding(self, name: str) -> RepositoryBinding:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryBindingTable).where(RepositoryBindingTable.repository_name == name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if not row:
                raise RepositoryNotFoundError(name)
            return RepositoryBinding(**row.__dict__)

    async def list_repositories(self, tag: Optional[str] = None) -> List[RepositoryBinding]:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryBindingTable)
            result = await session.execute(stmt)
            bindings = result.scalars().all()

            if tag is None:
                return [RepositoryBinding(**b.__dict__) for b in bindings]

            filtered = []
            for b in bindings:
                try:
                    repo = await self._vault.get_repository(b.repository_name)
                    if repo.tags and tag in repo.tags:
                        filtered.append(RepositoryBinding(**b.__dict__))
                except RepositoryNotFoundError:
                    continue
            return filtered

    async def remove_repository(self, name: str) -> None:
        await self._ensure_schema()
        async with self._sessionmaker() as session:
            stmt = sa.select(RepositoryBindingTable).where(RepositoryBindingTable.repository_name == name)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row:
                await session.delete(row)
                await session.commit()
        await self._vault.remove_repository(name)

    async def list_objects(self, repository_name: str) -> List[BucketObject]:
        return await self._objects.list_objects(repository_name)

    async def get_object(self, repository_name: str, object_path: str) -> BucketObject:
        return await self._objects.get_object(repository_name, object_path)

    async def add_object(self, repository_name: str, object_path: str, *, type=None, metadata=None) -> None:
        await self.get_repository_binding(repository_name)  # validate
        await self._objects.add_object(repository_name, object_path, type=type, metadata=metadata)

    async def remove_object(self, repository_name: str, object_path: str) -> None:
        await self._objects.remove_object(repository_name, object_path)

    async def update_object_type(self, repository_name: str, object_path: str, type: Optional[str]) -> None:
        await self._objects.update_type(repository_name, object_path, type)

    async def touch_object(self, repository_name: str, object_path: str) -> None:
        await self._objects.touch_object(repository_name, object_path)
