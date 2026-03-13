"""Chapter ingestion admin routes."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from api.middleware.auth import require_auth

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    source_dir: str = "data/chapters/"


@router.post("/chapters")
async def ingest_chapters(
    req: IngestRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(require_auth),
) -> dict:
    from rag.ingest import ingest_directory
    background_tasks.add_task(ingest_directory, req.source_dir)
    return {"message": f"Ingestion started from {req.source_dir}", "status": "queued"}
