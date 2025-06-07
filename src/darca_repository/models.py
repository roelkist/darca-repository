# models.py
# License: MIT

import os
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator


class StorageScheme(str, Enum):
    FILE = "file"
    S3 = "s3"
    MEMORY = "mem"
    NFS = "nfs"
    # Extend as needed


class RepositoryConnectionInfo(BaseModel):
    """Describes how to connect to a storage backend."""
    storage_url: str
    scheme: StorageScheme
    credentials: Optional[Dict[str, SecretStr]] = None
    parameters: Dict[str, str] = Field(default_factory=dict)

    def get_secret(self, key: str) -> Optional[str]:
        val = self.credentials.get(key) if self.credentials else None
        if isinstance(val, SecretStr):
            raw = val.get_secret_value()
            if raw.startswith("${") and raw.endswith("}"):
                return os.getenv(raw[2:-1])
            return raw
        return None


class Repository(BaseModel):
    """Defines a named repository and associated metadata."""
    name: str
    connection: RepositoryConnectionInfo
    tags: Optional[Dict[str, str]] = None
    enabled: bool = True
    priority: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError("Repository name must be a valid identifier (no spaces or special chars).")
        return v

    def get_secret(self, key: str) -> Optional[str]:
        """Shorthand passthrough for connection secrets."""
        return self.connection.get_secret(key)
