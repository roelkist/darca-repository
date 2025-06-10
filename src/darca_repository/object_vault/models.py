from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone


class BucketObject(BaseModel):
    object_id: Optional[int] = None
    object_path: str
    type: Optional[str] = None
    creation_time: str = datetime.now(tz=timezone.utc).isoformat()
    modification_time: Optional[str] = None


class Bucket(BaseModel):
    bucket_id: Optional[int] = None
    bucket_name: str
    creation_time: str = datetime.now(tz=timezone.utc).isoformat()
    modification_time: Optional[str] = None
    objects: List[BucketObject] = []