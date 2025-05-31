# instance.py
# License: MIT

from typing import Dict, Optional

from darca_storage.client import StorageClient
from darca_storage.factory import StorageConnectorFactory

from darca_repository.exceptions import RepositoryConnectionError
from darca_repository.models import Repository


class RepositoryInstance:
    """
    Represents an active repository instance with its storage client resolved.

    Provides access to:
        - repository metadata
        - associated StorageClient
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

    @property
    def client(self) -> Optional[StorageClient]:
        """Return the connected StorageClient if available."""
        return self._client

    async def connect(self) -> StorageClient:
        if self._client is not None:
            return self._client

        try:
            # Resolve credentials from secrets
            raw_credentials: Dict[str, str] = {
                k: self._repository.get_secret(k)
                for k in (self._repository.credentials or {})
                if self._repository.get_secret(k) is not None
            }

            # Build session metadata context
            session_metadata = {
                "repository_name": self._repository.name,
                "storage_url": self._repository.storage_url,
                "scheme": self._repository.scheme.value,
                "tags": self._repository.tags,
            }

            self._client = await StorageConnectorFactory.from_url(
                url=self._repository.storage_url,
                session_metadata=session_metadata,
                credentials=raw_credentials,
                parameters=self._repository.parameters,
            )

            return self._client

        except Exception as e:
            raise RepositoryConnectionError(
                name=self.name,
                message=(
                    f"Failed to connect to repository '{self.name}' "
                    f"at {self._repository.storage_url}"
                ),
                cause=e,
            ) from e

    async def test_connection(self) -> bool:
        """
        Probes whether the repository's root directory is reachable.

        Returns:
            bool: True if the repository is usable, False otherwise.
        """
        client = await self.connect()
        return await client.exists(".")
