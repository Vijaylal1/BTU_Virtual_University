"""
Abstract base for all 10 BTU specialist professors (Tier-3).
Provides the standard respond() pipeline:
  1. Agentic RAG retrieval (multi-round, chapter-scoped)
  2. Build messages from briefing + session history + RAG context
  3. Call LLM with adaptive thinking
  4. Return structured ProfessorResponse

For doubt_clearing mode the professor adopts a Socratic teaching style
and appends follow-up questions to guide the student deeper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from agents.base import BaseAgent
from agents.handoff import DoubtPacket, DoubtResponse, HandoffPacket2
from agents.prompts.professors import professor_system
from config.settings import get_settings

if TYPE_CHECKING:
    from memory.store import MemoryStore
    from rag.agentic_pipeline import AgenticRAGPipeline

logger = structlog.get_logger(__name__)
settings = get_settings()


class ProfessorResponse:
    def __init__(self, response_text: str, thinking: str | None, latency_ms: int, rag_chunks_used: int) -> None:
        self.response_text = response_text
        self.thinking = thinking
        self.latency_ms = latency_ms
        self.rag_chunks_used = rag_chunks_used


class BaseProfessor(BaseAgent):
    tier = 3
    professor_name: str = "Professor"
    domain: str = "General"
    chapters: list[int] = []

    def __init__(self, memory: "MemoryStore", rag: "AgenticRAGPipeline") -> None:
        super().__init__(memory)
        self.rag = rag
        self._system = professor_system(self.professor_name, self.domain, self.chapters)

    # ── Primary handler ───────────────────────────────────────────────────────

    async def handle(self, packet: HandoffPacket2) -> ProfessorResponse:  # type: ignore[override]
        return await self.respond(packet)

    async def respond(self, packet: HandoffPacket2) -> ProfessorResponse:
        # Step 1: Agentic RAG – chapter-scoped multi-round retrieval
        rag_result = await self.rag.agentic_retrieve(
            query=packet.rag_pre_query,
            chapters=packet.rag_chapters,
            top_k=settings.RAG_TOP_K,
        )
        rag_context = self._format_rag(rag_result.chunks)

        # Step 2: build conversation messages (with doubt-clearing mode if requested)
        messages = self._build_messages(packet, rag_context)

        # Step 3: LLM call with thinking
        result = await self._call_llm(
            system=self._system,
            messages=messages,
            max_tokens=2048,
            use_thinking=True,
        )
        return ProfessorResponse(
            response_text=result["text"],
            thinking=result["thinking"],
            latency_ms=result["latency_ms"],
            rag_chunks_used=len(rag_result.chunks),
        )

    # ── Doubt Clearing Session ────────────────────────────────────────────────

    async def clear_doubt(self, packet: DoubtPacket) -> DoubtResponse:
        """
        Focused, Socratic doubt-clearing session with the student.
        Uses Agentic RAG on the professor's own chapters, then responds
        with a structured explanation + follow-up questions.
        """
        import json
        import re
        import time as _time

        start = _time.monotonic()

        chapters = self.chapters or packet.chapter_hint and [packet.chapter_hint] or list(range(1, 31))
        rag_result = await self.rag.agentic_retrieve(
            query=packet.doubt_question,
            chapters=chapters,
            max_rounds=3,
        )
        rag_context = self._format_rag(rag_result.chunks)

        doubt_system = (
            f"{self._system}\n\n"
            "DOUBT CLEARING MODE: The student has a specific doubt. "
            "Your response MUST be structured as valid JSON:\n"
            "{\n"
            '  "explanation": "<thorough, step-by-step explanation>",\n'
            '  "follow_up_questions": ["<question to check understanding>", "<deeper probe>"],\n'
            '  "suggested_chapters": [<chapter numbers most relevant>]\n'
            "}\n"
            "Adopt a Socratic style: explain clearly, then ask questions to guide the student "
            "to discover deeper understanding themselves."
        )

        ctx = packet.student_context
        user_msg = (
            f"Student: {ctx.full_name} | Chapter: {ctx.current_chapter} | "
            f"Progress: {ctx.completion_pct*100:.0f}%\n\n"
            f"DOUBT: {packet.doubt_question}\n\n"
            f"[Relevant curriculum context]\n{rag_context or 'No specific context found.'}"
        )

        result = await self._call_llm(
            system=doubt_system,
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=1024,
            use_thinking=True,
        )

        latency_ms = int((_time.monotonic() - start) * 1000)

        # Parse structured JSON response
        try:
            raw = re.sub(r"^```[a-z]*\n?", "", result["text"].strip()).rstrip("```").strip()
            data = json.loads(raw)
            return DoubtResponse(
                explanation=data.get("explanation", result["text"]),
                follow_up_questions=data.get("follow_up_questions", []),
                suggested_chapters=data.get("suggested_chapters", []),
                professor_id=self.agent_id,
                rag_chunks_used=len(rag_result.chunks),
                latency_ms=latency_ms,
            )
        except Exception:
            return DoubtResponse(
                explanation=result["text"],
                follow_up_questions=[],
                suggested_chapters=self.chapters[:2] if self.chapters else [],
                professor_id=self.agent_id,
                rag_chunks_used=len(rag_result.chunks),
                latency_ms=latency_ms,
            )

    # ── Streaming variant for SSE ─────────────────────────────────────────────

    async def stream_respond(self, packet: HandoffPacket2):
        """Async generator yielding text chunks."""
        rag_result = await self.rag.agentic_retrieve(
            query=packet.rag_pre_query,
            chapters=packet.rag_chapters,
        )
        rag_context = self._format_rag(rag_result.chunks)
        messages = self._build_messages(packet, rag_context)
        async for chunk in self._stream_llm(system=self._system, messages=messages, max_tokens=2048):
            yield chunk

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_messages(self, packet: HandoffPacket2, rag_context: str) -> list[dict]:
        b = packet.briefing_packet
        mode_note = (
            "\n[MODE: DOUBT CLEARING – adopt a Socratic teaching style; "
            "explain step-by-step, then ask 1-2 probing follow-up questions.]"
            if packet.mode == "doubt_clearing" else ""
        )
        system_note = (
            f"[STUDENT BRIEFING]\n"
            f"Name: {b.student_name} | Chapter: {b.current_chapter} | "
            f"Progress: {b.completion_pct*100:.0f}% | {b.sprint_context}\n"
            f"Coach note: {b.coach_note}\n"
            f"Recent summaries: {'; '.join(b.recent_summaries[-2:]) if b.recent_summaries else 'None'}"
            f"{mode_note}\n\n"
            f"[CURRICULUM CONTEXT (agentic RAG – chapter-scoped)]\n"
            f"{rag_context or 'No specific curriculum context found.'}"
        )
        messages: list[dict] = [{"role": "user", "content": system_note}]

        # Inject session history (alternating user/assistant)
        for msg in packet.session_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # The actual student question (latest turn must be user)
        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": b.coach_note})
        return messages

    @staticmethod
    def _format_rag(chunks: list) -> str:
        if not chunks:
            return ""
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(f"[{i}] Ch.{c.chapter} – {c.text[:400]}")
        return "\n\n".join(parts)

