"""
Prof. Priya Place – Location & Footprint Strategy (Chapters 1-3).
STATUS: POC ACTIVE – full implementation.
"""

from __future__ import annotations

from agents.handoff import HandoffPacket2
from agents.professors.base_professor import BaseProfessor, ProfessorResponse
from memory.store import MemoryStore
from rag.pipeline import RAGPipeline


class ProfPlace(BaseProfessor):
    agent_id      = "place"
    professor_name = "Prof. Priya Place"
    domain         = "Location & Footprint Strategy"
    chapters       = [1, 2, 3]

    def __init__(self, memory: MemoryStore, rag: RAGPipeline) -> None:
        super().__init__(memory, rag)

    async def respond(self, packet: HandoffPacket2) -> ProfessorResponse:
        """Full Opus call with RAG + adaptive thinking."""
        return await super().respond(packet)
