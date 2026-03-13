"""
Agent Registry – instantiates and holds all agents as singletons.
Provides a typed lookup by professor_id.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from agents.professors.base_professor import BaseProfessor
from agents.professors.place       import ProfPlace
from agents.professors.people      import ProfPeople
from agents.professors.process     import ProfProcess
from agents.professors.positioning import ProfPositioning
from agents.professors.performance import ProfPerformance
from agents.professors.platform    import ProfPlatform
from agents.professors.pricing     import ProfPricing
from agents.professors.purpose     import ProfPurpose
from agents.professors.policy      import ProfPolicy
from agents.professors.profit      import ProfProfit

if TYPE_CHECKING:
    from memory.store import MemoryStore
    from rag.pipeline import RAGPipeline

logger = structlog.get_logger(__name__)

_PROFESSOR_CLASSES: dict[str, type[BaseProfessor]] = {
    "place":       ProfPlace,
    "people":      ProfPeople,
    "process":     ProfProcess,
    "positioning": ProfPositioning,
    "performance": ProfPerformance,
    "platform":    ProfPlatform,
    "pricing":     ProfPricing,
    "purpose":     ProfPurpose,
    "policy":      ProfPolicy,
    "profit":      ProfProfit,
}


class AgentRegistry:
    """Holds all instantiated agents and provides typed lookups."""

    def __init__(self, memory: "MemoryStore", rag: "RAGPipeline") -> None:
        self._memory = memory
        self._rag = rag
        self._professors: dict[str, BaseProfessor] = {}
        logger.info("agent_registry_initialised", professors=list(_PROFESSOR_CLASSES.keys()))

    def get_professor(self, professor_id: str) -> BaseProfessor:
        pid = professor_id if professor_id in _PROFESSOR_CLASSES else "place"
        if pid != professor_id:
            logger.warning("unknown_professor", professor_id=professor_id, fallback="place")
        if pid not in self._professors:
            self._professors[pid] = _PROFESSOR_CLASSES[pid](self._memory, self._rag)
            logger.info("professor_lazy_loaded", professor_id=pid)
        return self._professors[pid]

    def list_professors(self) -> list[dict]:
        from config.agent_config import PROFESSOR_META
        return [
            {
                "id": pid,
                **PROFESSOR_META.get(pid, {}),
            }
            for pid in _PROFESSOR_CLASSES
        ]
