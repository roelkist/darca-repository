# registry/mysql_registry.py

from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    Boolean,
    JSON,
    select,
    delete,
)
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.exc import NoResultFound

from darca_repository.registry.models import RegistryProfile, StorageScheme
from darca_repository.registry.interfaces import Registry
from darca_repository.exceptions import RepositoryNotFoundError

Base = declarative_base()


class RepositoryProfileTable(Base):
    __tablename__ = "repository_profiles"

    name = Column(String(255), primary_key=True)
    storage_url = Column(Text, nullable=False)
    scheme = Column(String(20), nullable=False)
    credentials = Column(JSON, nullable=True)
    parameters = Column(JSON, nullable=True)
    enabled = Column(Boolean, default=True)
    tags = Column(JSON, nullable=True)


class MySQLRegistry(Registry):
    """
    MySQL-backed implementation of the Registry interface.
    """

    def __init__(self, connection_url: str, user: str, password: str):
        self._engine = create_engine(
            f"mysql+pymysql://{user}:{password}@{connection_url}",
            future=True,
        )
        Base.metadata.create_all(self._engine)

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

    def _from_model(self, repository: RegistryProfile) -> RepositoryProfileTable:
        return RepositoryProfileTable(
            name=repository.name,
            storage_url=repository.storage_url,
            scheme=repository.scheme.value,
            credentials=repository.credentials,
            parameters=repository.parameters,
            enabled=repository.enabled,
            tags=repository.tags,
        )

    def get_profile(self, name: str) -> RegistryProfile:
        with Session(self._engine) as session:
            stmt = select(RepositoryProfileTable).where(RepositoryProfileTable.name == name)
            try:
                row = session.execute(stmt).scalar_one()
                return self._to_model(row)
            except NoResultFound:
                raise RepositoryNotFoundError(name)

    def list_profiles(
        self, *, enabled_only: bool = False, tag: Optional[str] = None
    ) -> List[RegistryProfile]:
        with Session(self._engine) as session:
            stmt = select(RepositoryProfileTable)
            if enabled_only:
                stmt = stmt.where(RepositoryProfileTable.enabled == True)
            rows = session.execute(stmt).scalars().all()

            if tag:
                rows = [r for r in rows if r.tags and tag in r.tags]

            return [self._to_model(r) for r in rows]

    def add_profile(self, repository: RegistryProfile) -> None:
        with Session(self._engine) as session:
            obj = self._from_model(repository)
            session.merge(obj)
            session.commit()

    def remove_profile(self, name: str) -> None:
        with Session(self._engine) as session:
            stmt = delete(RepositoryProfileTable).where(RepositoryProfileTable.name == name)
            result = session.execute(stmt)
            if result.rowcount == 0:
                raise RepositoryNotFoundError(name)
            session.commit()
