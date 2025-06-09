# object_vault/models.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RepositoryObject(BaseModel):
    object_path: str
    object_id: Optional[int] = None
    type: Optional[str] = None
    metadata: Optional[dict] = None
    creation_time: str = datetime.utcnow().isoformat()
    modification_time: Optional[str] = None
