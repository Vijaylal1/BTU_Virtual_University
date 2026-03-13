"""Wheel of Fortune routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import require_auth
from config.settings import get_settings
from gamification.sprint_engine import SprintEngine
from gamification.wheel_of_fortune import WheelOfFortune

router = APIRouter(prefix="/wheel", tags=["wheel"])


def _get_wheel() -> WheelOfFortune:
    from api.app import get_wheel
    return get_wheel()


def _get_sprint() -> SprintEngine:
    from api.app import get_sprint_engine
    return get_sprint_engine()


@router.post("/{student_id}/spin")
async def spin(
    student_id: str,
    auth_id: str = Depends(require_auth),
    wheel: WheelOfFortune = Depends(_get_wheel),
    sprint: SprintEngine = Depends(_get_sprint),
) -> dict:
    if get_settings().WHEEL_REQUIRE_SPRINT:
        eligible = await sprint.check_wheel_eligibility(student_id)
        if not eligible:
            raise HTTPException(status_code=403, detail="Complete your weekly sprint target (15 hrs) to spin!")
    prize = await wheel.spin(student_id)
    return {"prize": prize.model_dump()}


@router.get("/prizes")
async def list_prizes(wheel: WheelOfFortune = Depends(_get_wheel)) -> list:
    return [p.model_dump() for p in wheel.get_prizes()]
