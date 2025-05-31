# models.py
# License: MIT

import os
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, SecretStr


class StorageScheme(str, Enum):
    FILE = "file"
    S3 = "s3"
    MEMORY = "mem"
    NFS = "nfs"
    # Add more schemes as needed


class Repository(BaseModel):
    """
    Represents a configured repository for storing logical spaces.
    """

    name: str
    storage_url: str
    scheme: StorageScheme
    credentials: Optional[Dict[str, SecretStr]] = Field(default=None)
    parameters: Dict[str, str] = Field(default_factory=dict)
    tags: Optional[Dict[str, str]] = None
    enabled: bool = True
    priority: Optional[int] = None

    def get_secret(self, key: str) -> Optional[str]:
        val = self.credentials.get(key) if self.credentials else None
        if isinstance(val, SecretStr):
            raw = val.get_secret_value()
            if raw.startswith("${") and raw.endswith("}"):
                return os.getenv(raw[2:-1])
            return raw
        return None
