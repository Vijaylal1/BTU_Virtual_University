"""Sprint routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.middleware.auth import require_auth
from gamification.sprint_engine import SprintEngine

router = APIRouter(prefix="/sprint", tags=["sprint"])


class LogHoursRequest(BaseModel):
    hours: float = Field(..., gt=0.0, le=24.0)


def _get_sprint() -> SprintEngine:
    from api.app import get_sprint_engine
    return get_sprint_engine()


@router.get("/{student_id}")
async def sprint_status(
    student_id: str,
    auth_id: str = Depends(require_auth),
    engine: SprintEngine = Depends(_get_sprint),
) -> dict:
    return await engine.get_status(student_id)


@router.post("/{student_id}/log")
async def log_hours(
    student_id: str,
    req: LogHoursRequest,
    auth_id: str = Depends(require_auth),
    engine: SprintEngine = Depends(_get_sprint),
) -> dict:
    return await engine.log_hours(student_id, req.hours)
