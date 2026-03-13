"""
Pipeline Engine – orchestrates the full 3-tier agentic call chain.

Flow:
    User message
        → Tier 1: DeanAgent.orchestrate()  → HandoffPacket1 | CeremonyResponse
        → Tier 2: CoachAgent.bridge()       → HandoffPacket2 | CoachResponse
        → Tier 3: Professor.respond()       → ProfessorResponse
        → Tier 1: DeanAgent.quality_gate()
        → AgentResponse (returned to API)

Additional flows:
    library_search() – student visits BTU Library; agentic cross-chapter RAG
    doubt_chat()     – student clears a doubt directly with a professor
"""

from __future__ import annotations

import time
from typing import AsyncIterator, Optional

import structlog

from agents.dean import DeanAgent
from agents.coach import CoachAgent
from agents.handoff import (
    AgentResponse,
    CeremonyResponse,
    CoachResponse,
    DoubtPacket,
    DoubtResponse,
    HandoffPacket1,
    HandoffPacket2,
    LibraryResponse,
    LibrarySearchResult,
)
from agents.registry import AgentRegistry
from config.agent_config import CHAPTER_TO_PROFESSOR, PROFESSOR_META
from config.settings import get_settings
from memory.store import MemoryStore
from memory.summariser import Summariser
from rag.agentic_pipeline import AgenticRAGPipeline

logger = structlog.get_logger(__name__)
settings = get_settings()


class PipelineEngine:
    def __init__(
        self,
        memory: MemoryStore,
        dean: DeanAgent,
        coach: CoachAgent,
        registry: AgentRegistry,
        summariser: Summariser,
        rag: AgenticRAGPipeline,
    ) -> None:
        self.memory     = memory
        self.dean       = dean
        self.coach      = coach
        self.registry   = registry
        self.summariser = summariser
        self.rag        = rag

    # ── Main pipeline ─────────────────────────────────────────────────────────

    async def chat(self, student_id: str, message: str) -> AgentResponse:
        start = time.monotonic()

        # Persist user message
        await self.memory.save_message(student_id, role="user", content=message)

        # ── Tier 1: Dean ─────────────────────────────────────────────────────
        tier1 = await self.dean.orchestrate(student_id, message)

        if isinstance(tier1, CeremonyResponse):
            response = AgentResponse(
                text=tier1.ceremony_script,
                source_agent="dean_morgan",
                latency_ms=int((time.monotonic() - start) * 1000),
                ceremony=tier1,
            )
            await self._persist_and_maybe_summarise(student_id, response, "dean_morgan")
            return response

        # ── Tier 2: Coach ─────────────────────────────────────────────────────
        tier2 = await self.coach.bridge(tier1)

        if isinstance(tier2, CoachResponse):
            response = AgentResponse(
                text=self._prepend_greeting(tier1.greeting, tier2.response_text),
                source_agent=tier2.source_agent,
                latency_ms=int((time.monotonic() - start) * 1000),
                sprint_status=tier2.sprint_status,
                wheel_prize=tier2.wheel_prize,
            )
            await self._persist_and_maybe_summarise(student_id, response, tier2.source_agent)
            return response

        # ── Tier 3: Professor ─────────────────────────────────────────────────
        professor = self.registry.get_professor(tier2.professor_id)
        prof_resp = await professor.respond(tier2)

        # Quality gate (Tier 1 post-check)
        context = tier1.student_context
        response = AgentResponse(
            text=self._prepend_greeting(tier1.greeting, prof_resp.response_text),
            source_agent=tier2.professor_id,
            thinking=prof_resp.thinking,
            latency_ms=int((time.monotonic() - start) * 1000),
            rag_chunks_used=prof_resp.rag_chunks_used,
        )
        response = await self.dean.quality_gate(response, context)

        await self._persist_and_maybe_summarise(student_id, response, tier2.professor_id)
        return response

    # ── Streaming pipeline (SSE) ──────────────────────────────────────────────

    async def stream_chat(self, student_id: str, message: str) -> AsyncIterator[str]:
        await self.memory.save_message(student_id, role="user", content=message)

        tier1 = await self.dean.orchestrate(student_id, message)

        if isinstance(tier1, CeremonyResponse):
            yield tier1.ceremony_script
            return

        # Emit greeting as the first chunk if present
        greeting = tier1.greeting
        if greeting:
            yield greeting + "\n\n"

        tier2 = await self.coach.bridge(tier1)

        if isinstance(tier2, CoachResponse):
            yield tier2.response_text
            return

        professor = self.registry.get_professor(tier2.professor_id)
        full_text = (greeting + "\n\n") if greeting else ""
        async for chunk in professor.stream_respond(tier2):
            full_text += chunk
            yield chunk

        # Persist after streaming complete
        await self.memory.save_message(
            student_id, role="assistant", content=full_text,
            source_agent=tier2.professor_id,
        )
        await self._maybe_summarise(student_id, tier2.professor_id)

    # ── Library pipeline ──────────────────────────────────────────────────────

    async def library_search(self, student_id: str, query: str) -> LibraryResponse:
        """
        Student visits the BTU Digital Library.
        Runs Agentic RAG across all 30 chapters, then generates a synthesised
        answer with chapter-source references.
        """
        start = time.monotonic()

        await self.memory.save_message(student_id, role="user", content=f"[LIBRARY] {query}")

        rag_result = await self.rag.agentic_retrieve(
            query=query,
            chapters=list(range(1, 31)),
            max_rounds=3,
        )

        resources: list[LibrarySearchResult] = []
        chapters_seen: set[int] = set()
        for chunk in rag_result.chunks:
            prof_id = CHAPTER_TO_PROFESSOR.get(chunk.chapter, "")
            resources.append(LibrarySearchResult(
                chapter=chunk.chapter,
                excerpt=chunk.text[:400],
                score=round(chunk.score, 4),
                source=chunk.source,
                professor=prof_id,
            ))
            chapters_seen.add(chunk.chapter)

        # Use coach to synthesise the library answer
        context_lines = "\n".join(
            f"Ch.{r.chapter} ({PROFESSOR_META.get(r.professor, {}).get('name', r.professor)}): {r.excerpt}"
            for r in resources[:6]
        )
        from agents.prompts.coach import COACH_SYSTEM
        synth_prompt = (
            f"A student searched the BTU Digital Library for: '{query}'\n\n"
            f"Retrieved resources:\n{context_lines or 'No resources found.'}\n\n"
            "Synthesise a clear, informative answer (max 250 words). "
            "At the end, list the relevant chapter numbers."
        )
        synth = await self.dean._call_llm(
            system=COACH_SYSTEM,
            messages=[{"role": "user", "content": synth_prompt}],
            max_tokens=512,
        )
        answer = synth["text"]

        await self.memory.save_message(
            student_id, role="assistant", content=answer, source_agent="btu_library"
        )

        latency = int((time.monotonic() - start) * 1000)

        # Persist structured library session log
        await self.memory.save_library_session(
            student_id=student_id,
            query=query,
            answer=answer,
            chapters_hit=sorted(chapters_seen),
            rag_rounds=rag_result.rounds_used,
            latency_ms=latency,
        )

        return LibraryResponse(
            answer=answer,
            resources=resources,
            chapters_searched=sorted(chapters_seen),
            rag_rounds_used=rag_result.rounds_used,
            retrieval_trace=rag_result.trace,
            latency_ms=latency,
        )

    # ── Doubt Clearing pipeline ────────────────────────────────────────────────

    async def doubt_chat(
        self,
        student_id: str,
        doubt_question: str,
        professor_id: Optional[str] = None,
        chapter_hint: Optional[int] = None,
    ) -> DoubtResponse:
        """
        Student clears a specific doubt with the concerned professor.
        Routes directly to the professor (skipping Tiers 1-2) with a
        Socratic doubt-clearing prompt and targeted Agentic RAG.
        """
        await self.memory.save_message(student_id, role="user", content=f"[DOUBT] {doubt_question}")

        context = await self.memory.get_student_context(student_id)

        # Resolve which professor to use
        resolved_professor_id = professor_id or "place"
        if chapter_hint:
            resolved_professor_id = CHAPTER_TO_PROFESSOR.get(chapter_hint, resolved_professor_id)

        professor = self.registry.get_professor(resolved_professor_id)

        packet = DoubtPacket(
            student_id=student_id,
            student_context=context,
            professor_id=resolved_professor_id,
            doubt_question=doubt_question,
            chapter_hint=chapter_hint,
        )
        doubt_response = await professor.clear_doubt(packet)

        # Persist for memory continuity
        await self.memory.save_message(
            student_id,
            role="assistant",
            content=doubt_response.explanation,
            source_agent=resolved_professor_id,
            latency_ms=doubt_response.latency_ms,
        )

        # Persist structured doubt session log
        await self.memory.save_doubt_session(
            student_id=student_id,
            professor_id=resolved_professor_id,
            doubt_question=doubt_question,
            explanation=doubt_response.explanation,
            follow_up_questions=doubt_response.follow_up_questions,
            suggested_chapters=doubt_response.suggested_chapters,
            rag_chunks_used=doubt_response.rag_chunks_used,
            chapter_hint=chapter_hint,
            latency_ms=doubt_response.latency_ms,
        )

        await self._maybe_summarise(student_id, resolved_professor_id)

        return doubt_response

    # ── Discussion AI moderator ──────────────────────────────────────────────

    async def discuss_ai(self, room_id: str, nudge: str | None = None) -> str:
        """
        Coach Elias reviews recent discussion messages and provides moderation.
        If the room is tied to a chapter, RAG context from that chapter is included.
        """
        from agents.prompts.coach import COACH_SYSTEM
        from config.agent_config import PROFESSOR_META

        room = await self.memory.get_discussion_room(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")

        # Gather recent messages for context
        messages = await self.memory.get_discussion_messages(room_id, limit=30)
        if not messages:
            return "No messages yet — I'll be here to help once the discussion gets started!"

        conversation = "\n".join(
            f"{'[AI] Coach Elias' if m['is_ai'] else m['author']}: {m['content']}"
            for m in messages
        )

        # Build room context description
        room_desc = f"Room: '{room.title}' ({room.room_type})"
        if room.chapter_hint:
            room_desc += f" | Chapter {room.chapter_hint}"
        if room.professor_id:
            prof_name = PROFESSOR_META.get(room.professor_id, {}).get("name", room.professor_id)
            room_desc += f" | Module: {prof_name}"
        if room.topic:
            room_desc += f" | Topic: {room.topic}"

        # Optional RAG context for library rooms or chapter-linked campus rooms
        rag_context = ""
        if room.chapter_hint and self.rag:
            topic_query = room.topic or room.title
            try:
                chunks = await self.rag.retrieve(
                    query=topic_query,
                    chapters=[room.chapter_hint],
                    top_k=3,
                )
                if chunks:
                    rag_context = "\n\nRelevant curriculum material:\n" + "\n".join(
                        f"- {c.text[:200]}" for c in chunks
                    )
            except Exception:
                pass  # RAG is optional for moderation

        action = nudge or "Synthesise the key points, correct any misconceptions, and ask a thought-provoking follow-up question"

        prompt = (
            f"{room_desc}\n\n"
            f"Discussion so far:\n{conversation}\n"
            f"{rag_context}\n\n"
            f"As Coach Elias, the AI moderator of this student discussion: {action}.\n"
            "Keep your response under 150 words. Be encouraging and educational."
        )

        result = await self.coach._call_llm(
            system=COACH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return result["text"]

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _prepend_greeting(greeting: str | None, text: str) -> str:
        if greeting:
            return f"{greeting}\n\n{text}"
        return text

    async def _persist_and_maybe_summarise(
        self, student_id: str, response: AgentResponse, agent: str
    ) -> None:
        await self.memory.save_message(
            student_id,
            role="assistant",
            content=response.text,
            source_agent=agent,
            thinking=response.thinking,
            latency_ms=response.latency_ms,
        )
        await self._maybe_summarise(student_id, agent)

    async def _maybe_summarise(self, student_id: str, professor_id: str) -> None:
        count = await self.memory.message_count_since_last_summary(student_id, professor_id)
        if count >= settings.SUMMARISE_EVERY_N:
            recent = await self.memory.get_recent_messages(student_id, limit=settings.SUMMARISE_EVERY_N)
            await self.summariser.summarise_and_store(student_id, professor_id, recent)
            logger.info("upward_summarisation_triggered", student_id=student_id, professor_id=professor_id)
