"""
Prof. Marcus Pricing – Financial Planning & Pricing (Chapters 19-21).
STATUS: DORMANT – stub only. Activate in a future sprint.
"""

from __future__ import annotations

from agents.handoff import HandoffPacket2
from agents.professors.base_professor import BaseProfessor, ProfessorResponse
from memory.store import MemoryStore
from rag.pipeline import RAGPipeline


class ProfPricing(BaseProfessor):
    agent_id       = "pricing"
    professor_name = "Prof. Marcus Pricing"
    domain         = "Financial Planning & Pricing"
    chapters       = [19, 20, 21]

    def __init__(self, memory: MemoryStore, rag: RAGPipeline) -> None:
        super().__init__(memory, rag)

    async def respond(self, packet: HandoffPacket2) -> ProfessorResponse:
        return ProfessorResponse(
            response_text=(
                "Prof. Marcus Pricing's domain (Financial Planning & Pricing, chapters 19-21) "
                "will be available in the next sprint. "
                "Please ask Prof. Priya Place (chapters 1-3) or Elias Vance for guidance."
            ),
            thinking=None,
            latency_ms=0,
            rag_chunks_used=0,
        )
