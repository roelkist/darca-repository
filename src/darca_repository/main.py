# src/darca_repository/main.py

from fastapi import FastAPI
from darca_repository.server.api import router as repository_router

app = FastAPI(
    title="DARCA Repository Server",
    version="0.0.1",
    description="Repository orchestration and connection service."
)

app.include_router(repository_router, prefix="/repositories")
