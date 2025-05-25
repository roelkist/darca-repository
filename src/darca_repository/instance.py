# instance.py
# License: MIT

from typing import Optional
from darca_storage.factory import StorageConnectorFactory
from darca_storage.interfaces.file_backend import FileBackend

from darca_repository.models import Repository
from darca_repository.exceptions import RepositoryNotFoundError, RepositoryConnectionError


class RepositoryInstance:
    """
    Represents an active repository instance with its storage backend resolved.
    Provides access to repository metadata and its corresponding FileBackend.
    """

    def __init__(self, repository: Repository):
        self._repository = repository
        self._connector = None
        self._backend: Optional[FileBackend] = None

    @property
    def name(self) -> str:
        return self._repository.name

    @property
    def metadata(self) -> Repository:
        return self._repository

    async def connect(self) -> FileBackend:
        """
        Lazily resolves and caches the FileBackend associated with the repository.
        """
        if self._backend is not None:
            return self._backend

        try:
            self._connector = await StorageConnectorFactory.from_url(
                self._repository.storage_url,
                credentials={k: v.get_secret_value() for k, v in (self._repository.credentials or {}).items()},
                parameters=self._repository.parameters
            )
            self._backend = await self._connector.connect()
            return self._backend

        except Exception as e:
            raise RepositoryConnectionError(
                message=f"Failed to connect to repository '{self.name}' at {self._repository.storage_url}",
                repository=self.name,
                cause=e
            ) from e
