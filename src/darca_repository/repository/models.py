# models.py
# License: MIT

import os
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator

class Repository(BaseModel):
    """Defines a named repository and associated metadata."""
    name: str
    tags: Optional[Dict[str, str]] = None
    enabled: bool = True
    priority: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError("Repository name must be a valid identifier (no spaces or special chars).")
        return v
