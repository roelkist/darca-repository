# src/darca_repository/interfaces.py
# License: MIT

from typing import Protocol, runtime_checkable, List


@runtime_checkable
class RepositoryIOInterface(Protocol):
    """
    Protocol for repository I/O capabilities.
    Used to enforce and type-check the storage operation surface.
    """

    async def read(self, path: str) -> bytes:
        """Read binary data from the specified path."""
        ...

    async def write(self, path: str, data: bytes) -> None:
        """Write binary data to the specified path."""
        ...

    async def delete(self, path: str) -> None:
        """Delete the specified file."""
        ...

    async def list(self, path: str = ".") -> List[str]:
        """List all items under the specified directory path."""
        ...

    async def exists(self, path: str) -> bool:
        """Check whether a path exists."""
        ...
