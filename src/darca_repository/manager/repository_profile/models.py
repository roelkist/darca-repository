# repository_vault/models.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Repository(BaseModel):
    repository_name: str
    description: Optional[str] = None
    creation_time: str = datetime.utcnow().isoformat()
    modification_time: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    repository_id: Optional[int] = None
