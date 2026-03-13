"""
Prof. Sam Process – Operations & Workflow Design (Chapters 7-9).
STATUS: DORMANT – stub only. Activate in a future sprint.
"""

from __future__ import annotations

from agents.handoff import HandoffPacket2
from agents.professors.base_professor import BaseProfessor, ProfessorResponse
from memory.store import MemoryStore
from rag.pipeline import RAGPipeline


class ProfProcess(BaseProfessor):
    agent_id       = "process"
    professor_name = "Prof. Sam Process"
    domain         = "Operations & Workflow Design"
    chapters       = [7, 8, 9]

    def __init__(self, memory: MemoryStore, rag: RAGPipeline) -> None:
        super().__init__(memory, rag)

    async def respond(self, packet: HandoffPacket2) -> ProfessorResponse:
        return ProfessorResponse(
            response_text=(
                "Prof. Sam Process's domain (Operations & Workflow Design, chapters 7-9) "
                "will be available in the next sprint. "
                "Please ask Prof. Priya Place (chapters 1-3) or Elias Vance for guidance."
            ),
            thinking=None,
            latency_ms=0,
            rag_chunks_used=0,
        )
