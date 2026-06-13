from abc import ABC, abstractmethod
from typing import List, Optional
from darca_repository.dataset_profile.models import File


class ObjectVault(ABC):
    """Async interface for managing bucket-scoped objects."""

    @abstractmethod
    async def get_object(self, bucket: str, object_path: str) -> File:
        """Return a single object by its path within the bucket."""
        ...

    @abstractmethod
    async def list_objects(self, bucket: str) -> List[File]:
        """Return all objects in a given bucket."""
        ...

    @abstractmethod
    async def add_object(
        self,
        bucket: str,
        object_path: str,
        *,
        type: Optional[str] = None,
        metadata: Optional[dict] = None,  # still optional for backward compatibility
    ) -> None:
        ...

    @abstractmethod
    async def remove_object(self, bucket: str, object_path: str) -> None:
        ...

    @abstractmethod
    async def update_type(self, bucket: str, object_path: str, type: Optional[str]) -> None:
        ...

    @abstractmethod
    async def touch_object(self, bucket: str, object_path: str) -> None:
        ...
