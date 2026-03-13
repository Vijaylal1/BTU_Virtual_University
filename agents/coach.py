"""
Tier-2 Agent: Elias Vance – Bridge Agent / Tactical AI Coach.
Handles navigation, motivation, sprint, wheel, library queries directly.
Routes domain and doubt queries to professors via HandoffPacket2.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog

from agents.base import BaseAgent
from agents.handoff import (
    CoachResponse,
    HandoffPacket1,
    HandoffPacket2,
    IntentType,
    LibraryResponse,
    LibrarySearchResult,
    ProfessorBriefingPacket,
)
from agents.prompts.coach import COACH_SYSTEM
from config.agent_config import CHAPTER_TO_PROFESSOR, PROFESSOR_CHAPTERS, PROFESSOR_META
from config.settings import get_settings
from memory.store import MemoryStore

if TYPE_CHECKING:
    from gamification.sprint_engine import SprintEngine
    from gamification.wheel_of_fortune import WheelOfFortune
    from rag.agentic_pipeline import AgenticRAGPipeline

logger = structlog.get_logger(__name__)
settings = get_settings()


class CoachAgent(BaseAgent):
    agent_id = "elias_vance"
    tier = 2

    def __init__(
        self,
        memory: MemoryStore,
        rag: "AgenticRAGPipeline",
        sprint: "SprintEngine",
        wheel: "WheelOfFortune",
    ) -> None:
        super().__init__(memory)
        self.rag = rag
        self.sprint = sprint
        self.wheel = wheel

    # ── Primary entry point ───────────────────────────────────────────────────

    async def handle(self, packet: HandoffPacket1) -> HandoffPacket2 | CoachResponse:  # type: ignore[override]
        return await self.bridge(packet)

    async def bridge(self, packet: HandoffPacket1) -> HandoffPacket2 | CoachResponse:
        intent = packet.intent_type
        sid = packet.student_id
        ctx = packet.student_context

        if intent == IntentType.NAVIGATION:
            return await self._handle_navigation(packet)

        if intent == IntentType.MOTIVATION:
            return await self._handle_motivation(packet)

        if intent == IntentType.SPRINT:
            return await self._handle_sprint(sid)

        if intent == IntentType.WHEEL:
            return await self._handle_wheel(sid)

        if intent == IntentType.LIBRARY:
            return await self._handle_library(packet)

        # DOMAIN / CROSS_P / DOUBT → build handoff to professor
        professor_id = packet.target_module or "place"  # fallback to POC active
        chapters = PROFESSOR_CHAPTERS.get(professor_id, [1, 2, 3])
        mode = "doubt_clearing" if intent == IntentType.DOUBT else "normal"

        # Agentic RAG retrieval across all 30 chapters at coach level
        rag_result = await self.rag.agentic_retrieve(
            packet.raw_message, chapters=list(range(1, 31))
        )
        rag_pre_query = self._refine_query(packet.raw_message, packet.dean_note)

        briefing = ProfessorBriefingPacket(
            student_name=ctx.full_name,
            current_chapter=ctx.current_chapter,
            completion_pct=ctx.completion_pct,
            sprint_context=f"Week {ctx.sprint_week}: {ctx.sprint_hours:.1f}/{ctx.sprint_target}hrs",
            recent_summaries=ctx.recent_summaries,
            coach_note=self._build_coach_note(packet, rag_result.chunks),
        )

        # Fetch recent session history for professor context
        history = await self.memory.get_recent_messages(packet.student_id, limit=10)

        return HandoffPacket2(
            professor_id=professor_id,
            briefing_packet=briefing,
            rag_chapters=chapters,
            rag_pre_query=rag_pre_query,
            session_history=history,
            thinking_budget=settings.THINKING_BUDGET,
            mode=mode,
        )

    # ── Direct handlers ───────────────────────────────────────────────────────

    async def _handle_navigation(self, packet: HandoffPacket1) -> CoachResponse:
        ctx = packet.student_context
        prompt = (
            f"The student {ctx.full_name} is on chapter {ctx.current_chapter} "
            f"({ctx.completion_pct*100:.0f}% complete). "
            f"Sprint Week {ctx.sprint_week}: {ctx.sprint_hours}/{ctx.sprint_target}hrs. "
            "Explain where they are in the BTU 30-chapter journey "
            "and what the next 2 chapters will cover. Be motivating and concise (≤120 words)."
        )
        result = await self._call_llm(
            system=COACH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return CoachResponse(response_text=result["text"])

    async def _handle_motivation(self, packet: HandoffPacket1) -> CoachResponse:
        ctx = packet.student_context
        prompt = (
            f"Student {ctx.full_name} needs motivation. They have {ctx.badge_count} badges, "
            f"are on chapter {ctx.current_chapter} ({ctx.completion_pct*100:.0f}%), "
            f"Sprint: {ctx.sprint_hours}/{ctx.sprint_target}hrs. "
            f"Their message: '{packet.raw_message}'. "
            "Respond with a short energising coaching message (≤100 words). "
            "Reference a specific achievement or progress milestone."
        )
        result = await self._call_llm(
            system=COACH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return CoachResponse(response_text=result["text"])

    async def _handle_sprint(self, student_id: str) -> CoachResponse:
        status = await self.sprint.get_status(student_id)
        remaining = max(0.0, status["target"] - status["logged"])
        pct = min(100, int(status["logged"] / status["target"] * 100))
        text = (
            f"🏃 **Sprint Week {status['week']}**\n"
            f"Hours logged: {status['logged']:.1f} / {status['target']:.0f} hrs ({pct}%)\n"
            f"Remaining: {remaining:.1f} hrs\n"
        )
        if remaining == 0:
            text += "✅ Sprint target hit! Wheel spin unlocked 🎡"
        elif remaining <= 3:
            text += "Almost there – one focused session and you're done!"
        else:
            text += f"Keep going – aim for {remaining/3:.1f} hrs per day this week."
        return CoachResponse(response_text=text, sprint_status=status)

    async def _handle_wheel(self, student_id: str) -> CoachResponse:
        prize = await self.wheel.spin(student_id)
        text = (
            f"🎡 **Wheel of Fortune!**\n\n"
            f"You won: **{prize.prize_label}** ({prize.prize_type})\n\n"
            "Keep spinning that wheel of success!"
        )
        return CoachResponse(response_text=text, wheel_prize=prize)

    async def _handle_library(self, packet: HandoffPacket1) -> CoachResponse:
        """
        Library scenario: student browses the BTU digital library.
        Uses Agentic RAG across all 30 chapters, then Coach synthesises
        a curated answer with source references.
        """
        ctx = packet.student_context
        query = packet.raw_message

        rag_result = await self.rag.agentic_retrieve(
            query,
            chapters=list(range(1, 31)),   # full library scope
            max_rounds=3,
        )

        # Build a readable resource list for the response
        resource_lines = []
        for i, chunk in enumerate(rag_result.chunks[:5], 1):
            prof_id = CHAPTER_TO_PROFESSOR.get(chunk.chapter, "")
            prof_meta = PROFESSOR_META.get(prof_id, {})
            resource_lines.append(
                f"[{i}] **Ch.{chunk.chapter}** ({prof_meta.get('name', prof_id)}) "
                f"– score {chunk.score:.2f}\n{chunk.text[:280]}"
            )
        resources_text = "\n\n".join(resource_lines) if resource_lines else "No matching resources found."

        prompt = (
            f"Student {ctx.full_name} is visiting the BTU Digital Library.\n"
            f"Their search query: '{query}'\n\n"
            f"Retrieved curriculum resources (across all 30 chapters):\n{resources_text}\n\n"
            "As Coach Elias Vance acting as the librarian:\n"
            "1. Give a concise, helpful answer synthesising the resources (max 200 words).\n"
            "2. End with: 'Relevant chapters: X, Y, Z' so the student knows where to study.\n"
            "Be warm and encouraging."
        )
        result = await self._call_llm(
            system=COACH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        return CoachResponse(response_text=result["text"], source_agent="btu_library")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refine_query(self, raw: str, dean_note: str) -> str:
        return f"{raw} [context: {dean_note[:200]}]" if dean_note else raw

    def _build_coach_note(self, packet: HandoffPacket1, rag_chunks: list) -> str:
        chunks_found = len(rag_chunks)
        return (
            f"Dean note: {packet.dean_note[:150]} | "
            f"{chunks_found} RAG chunk(s) retrieved | "
            f"Confidence: {packet.confidence:.2f}"
        )
