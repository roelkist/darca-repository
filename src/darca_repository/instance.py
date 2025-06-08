# src/darca_repository/instance.py
# License: MIT

from typing import Dict, Optional, List

from darca_storage.client import StorageClient
from darca_storage.factory import StorageConnectorFactory

from darca_repository.exceptions import (
    RepositoryConnectionError,
    RepositoryNotConnectedError,
    RepositoryIOError,
)
from darca_repository.models import Repository


class RepositoryInstance:
    """
    Represents an active repository instance with its resolved storage client.
    Provides direct access to storage operations like read, write, list, etc.
    """

    def __init__(self, repository: Repository):
        self._repository = repository
        self._client: Optional[StorageClient] = None

    @property
    def name(self) -> str:
        return self._repository.name

    @property
    def metadata(self) -> Repository:
        return self._repository

    def is_connected(self) -> bool:
        return self._client is not None

    async def connect(self) -> StorageClient:
        if self._client is not None:
            return self._client

        try:
            raw_credentials: Dict[str, str] = {
                k: self._repository.get_secret(k)
                for k in (self._repository.connection.credentials or {})
                if self._repository.get_secret(k) is not None
            }

            session_metadata = {
                "repository_name": self._repository.name,
                "storage_url": self._repository.connection.storage_url,
                "scheme": self._repository.connection.scheme.value,
                "tags": self._repository.tags or {},
            }

            self._client = await StorageConnectorFactory.from_url(
                url=self._repository.connection.storage_url,
                session_metadata=session_metadata,
                credentials=raw_credentials,
                parameters=self._repository.connection.parameters,
            )

            return self._client

        except Exception as e:
            raise RepositoryConnectionError(
                name=self.name,
                message=(
                    f"Failed to connect to repository '{self.name}' "
                    f"at {self._repository.connection.storage_url}"
                ),
                cause=e,
            ) from e

    async def disconnect(self) -> None:
        if self._client and hasattr(self._client, "close"):
            await self._client.close()
        self._client = None

    async def test_connection(self) -> bool:
        client = await self.connect()
        return await client.exists(".")

    # ----------------------------
    # Storage I/O operation layer
    # ----------------------------

    async def read(self, path: str) -> bytes:
        client = await self._require_client()
        try:
            return await client.read(path)
        except Exception as e:
            raise RepositoryIOError(f"Failed to read '{path}' in '{self.name}'", cause=e)

    async def write(self, path: str, data: bytes) -> None:
        client = await self._require_client()
        try:
            await client.write(path, data)
        except Exception as e:
            raise RepositoryIOError(f"Failed to write to '{path}' in '{self.name}'", cause=e)

    async def delete(self, path: str) -> None:
        client = await self._require_client()
        try:
            await client.delete(path)
        except Exception as e:
            raise RepositoryIOError(f"Failed to delete '{path}' in '{self.name}'", cause=e)

    async def list(self, path: str = ".") -> List[str]:
        client = await self._require_client()
        try:
            return await client.list(path)
        except Exception as e:
            raise RepositoryIOError(f"Failed to list '{path}' in '{self.name}'", cause=e)

    async def exists(self, path: str) -> bool:
        client = await self._require_client()
        try:
            return await client.exists(path)
        except Exception as e:
            raise RepositoryIOError(f"Failed to check existence of '{path}' in '{self.name}'", cause=e)

    async def _require_client(self) -> StorageClient:
        if self._client is None:
            await self.connect()
        if self._client is None:
            raise RepositoryNotConnectedError(self.name)
        return self._client
