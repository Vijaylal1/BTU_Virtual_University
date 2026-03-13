"""Agent info routes – list professors, their status, and chapter mapping."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.middleware.auth import require_auth
from agents.registry import AgentRegistry
from config.agent_config import CHAPTER_TO_PROFESSOR, PROFESSOR_META

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_registry() -> AgentRegistry:
    from api.app import get_registry
    return get_registry()


@router.get("")
async def list_agents(
    auth_id: str = Depends(require_auth),
    registry: AgentRegistry = Depends(_get_registry),
) -> dict:
    professors = registry.list_professors()
    return {
        "dean":       {"id": "dean_morgan",  "name": "Dean Morgan",  "tier": 1},
        "coach":      {"id": "elias_vance",  "name": "Elias Vance",  "tier": 2},
        "professors": professors,
    }


@router.get("/chapter-map")
async def chapter_map(_: str = Depends(require_auth)) -> dict:
    return {
        "chapters": {str(ch): prof for ch, prof in CHAPTER_TO_PROFESSOR.items()},
        "professors": PROFESSOR_META,
    }
