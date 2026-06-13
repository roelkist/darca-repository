from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone


class File(BaseModel):
    file_id: Optional[int] = None
    file_path: str
    type: Optional[str] = None
    creation_time: str = datetime.now(tz=timezone.utc).isoformat()
    modification_time: Optional[str] = None


class Dataset(BaseModel):
    dataset_id: Optional[int] = None
    dataset_name: str
    creation_time: str = datetime.now(tz=timezone.utc).isoformat()
    modification_time: Optional[str] = None
    objects: List[File] = []
    