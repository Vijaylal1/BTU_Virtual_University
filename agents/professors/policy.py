"""
Prof. Lucas Policy – Legal, Policy & Compliance (Chapters 25-27).
STATUS: DORMANT – stub only. Activate in a future sprint.
"""

from __future__ import annotations

from agents.handoff import HandoffPacket2
from agents.professors.base_professor import BaseProfessor, ProfessorResponse
from memory.store import MemoryStore
from rag.pipeline import RAGPipeline


class ProfPolicy(BaseProfessor):
    agent_id       = "policy"
    professor_name = "Prof. Lucas Policy"
    domain         = "Legal, Policy & Compliance"
    chapters       = [25, 26, 27]

    def __init__(self, memory: MemoryStore, rag: RAGPipeline) -> None:
        super().__init__(memory, rag)

    async def respond(self, packet: HandoffPacket2) -> ProfessorResponse:
        return ProfessorResponse(
            response_text=(
                "Prof. Lucas Policy's domain (Legal, Policy & Compliance, chapters 25-27) "
                "will be available in the next sprint. "
                "Please ask Prof. Priya Place (chapters 1-3) or Elias Vance for guidance."
            ),
            thinking=None,
            latency_ms=0,
            rag_chunks_used=0,
        )
