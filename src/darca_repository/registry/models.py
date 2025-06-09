from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from enum import Enum
from typing import Dict, Optional, List
import os


class StorageScheme(str, Enum):
    FILE = "file"
    S3 = "s3"
    MEMORY = "mem"
    NFS = "nfs"
    # Extend as needed


class RegistryProfile(BaseModel):
    """Describes how to connect to a storage backend."""
    name: str
    profile_id: Optional[int] = None
    storage_url: str
    scheme: Optional[StorageScheme] = None 
    credentials: Optional[Dict[str, SecretStr]] = None
    parameters: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    tags: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError("Repository name must be a valid identifier (no spaces or special chars).")
        return v

    @model_validator(mode="after")
    def infer_scheme_from_url(self) -> "RegistryProfile":
        if not self.scheme:
            if self.storage_url.startswith("file://"):
                self.scheme = StorageScheme.FILE
            elif self.storage_url.startswith("s3://"):
                self.scheme = StorageScheme.S3
            elif self.storage_url.startswith("mem://"):
                self.scheme = StorageScheme.MEMORY
            elif self.storage_url.startswith("nfs://"):
                self.scheme = StorageScheme.NFS
            else:
                raise ValueError(f"Unable to infer storage scheme from URL: {self.storage_url}")
        return self

    def get_secret(self, key: str) -> Optional[str]:
        val = self.credentials.get(key) if self.credentials else None
        if isinstance(val, SecretStr):
            raw = val.get_secret_value()
            if raw.startswith("${") and raw.endswith("}"):
                return os.getenv(raw[2:-1])
            return raw
        return None
