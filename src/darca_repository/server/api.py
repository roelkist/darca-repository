# src/darca_repository/server/api.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Annotated

from darca_repository.server.dependencies import get_registry
from darca_repository.server.service import get_or_create_instance, connect_to_repository
from darca_repository.registry.interfaces import RepositoryRegistry
from darca_repository.models import Repository, RepositoryConnectionInfo
from darca_repository.exceptions import RepositoryNotFoundError

router = APIRouter()


# ------------------------------
# Repository Profile Management
# ------------------------------

class RepositoryCreateRequest(BaseModel):
    name: str
    connection: RepositoryConnectionInfo
    tags: dict[str, str] | None = None
    enabled: bool = True
    priority: int | None = None

    def to_repository(self) -> Repository:
        return Repository(
            name=self.name,
            connection=self.connection,
            tags=self.tags,
            enabled=self.enabled,
            priority=self.priority,
        )


@router.get("/", response_model=list[Repository])
def list_repositories(registry: RepositoryRegistry = Depends(get_registry)):
    return registry.list_profiles()


@router.get("/{name}", response_model=Repository)
def get_repository(name: str, registry: RepositoryRegistry = Depends(get_registry)):
    try:
        return registry.get_profile(name)
    except RepositoryNotFoundError:
        raise HTTPException(status_code=404, detail=f"Repository '{name}' not found.")


@router.get("/{name}/test")
async def test_connection(name: str, registry: RepositoryRegistry = Depends(get_registry), retry: int = 0):
    for attempt in range(retry + 1):
        try:
            return {"success": await connect_to_repository(name, registry)}
        except Exception as e:
            if attempt == retry:
                raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Repository)
def add_repository(req: RepositoryCreateRequest, registry: RepositoryRegistry = Depends(get_registry)):
    repository = req.to_repository()
    registry.add_profile(repository)
    return repository


@router.delete("/{name}")
def delete_repository(name: str, registry: RepositoryRegistry = Depends(get_registry)):
    try:
        registry.remove_profile(name)
        return {"message": f"Repository '{name}' removed."}
    except RepositoryNotFoundError:
        raise HTTPException(status_code=404, detail=f"Repository '{name}' not found.")


# ------------------------
# Repository I/O Endpoints
# ------------------------

@router.get("/{name}/list")
async def list_files(
    name: str,
    path: Annotated[str, Query(alias="path")] = ".",
    registry: RepositoryRegistry = Depends(get_registry),
):
    instance = await get_or_create_instance(name, registry)
    return {"files": await instance.list(path)}


@router.get("/{name}/exists")
async def exists_file(
    name: str,
    path: Annotated[str, Query(alias="path")],
    registry: RepositoryRegistry = Depends(get_registry),
):
    instance = await get_or_create_instance(name, registry)
    return {"exists": await instance.exists(path)}


@router.get("/{name}/read")
async def read_file(
    name: str,
    path: Annotated[str, Query(alias="path")],
    registry: RepositoryRegistry = Depends(get_registry),
):
    instance = await get_or_create_instance(name, registry)
    content = await instance.read(path)
    return StreamingResponse(iter([content]), media_type="application/octet-stream")


class WriteRequest(BaseModel):
    path: str
    data: bytes


@router.post("/{name}/write")
async def write_file(
    name: str,
    req: WriteRequest,
    registry: RepositoryRegistry = Depends(get_registry),
):
    instance = await get_or_create_instance(name, registry)
    await instance.write(req.path, req.data)
    return {"status": "written"}


@router.delete("/{name}/delete")
async def delete_file(
    name: str,
    path: Annotated[str, Query(alias="path")],
    registry: RepositoryRegistry = Depends(get_registry),
):
    instance = await get_or_create_instance(name, registry)
    await instance.delete(path)
    return {"status": "deleted"}
