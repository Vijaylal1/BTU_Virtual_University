"""
Tier-1 Agent: Dean Morgan – Master Orchestrator.
Responsibilities: intent routing, ceremony triggering, quality gating.
"""

from __future__ import annotations

from typing import Any

import structlog

from agents.base import BaseAgent
from agents.handoff import (
    AgentResponse,
    CeremonyResponse,
    HandoffPacket1,
    IntentType,
    MilestoneType,
    StudentContext,
)
from agents.prompts.dean import DEAN_SYSTEM
from agents.router import IntentRouter
from config.agent_config import CHAPTER_TO_PROFESSOR, POC_ACTIVE_PROFESSORS
from config.settings import get_settings
from memory.store import MemoryStore

logger = structlog.get_logger(__name__)
settings = get_settings()


class DeanAgent(BaseAgent):
    agent_id = "dean_morgan"
    tier = 1

    def __init__(self, memory: MemoryStore) -> None:
        super().__init__(memory)
        self.router = IntentRouter()

    # ── Primary entry point ───────────────────────────────────────────────────

    async def handle(self, student_id: str, message: str) -> HandoffPacket1 | CeremonyResponse:  # type: ignore[override]
        return await self.orchestrate(student_id, message)

    async def orchestrate(self, student_id: str, message: str) -> HandoffPacket1 | CeremonyResponse:
        context = await self.memory.get_student_context(student_id)

        # ── Ceremony: onboarding ─────────────────────────────────────────────
        if context.completion_pct == 0.0 and not await self.memory.is_onboarded(student_id):
            return await self._ceremony(context, MilestoneType.ONBOARDING)

        # ── Ceremony: graduation ─────────────────────────────────────────────
        if context.completion_pct >= 1.0 and not await self.memory.is_graduated(student_id):
            return await self._ceremony(context, MilestoneType.GRADUATION)

        # ── Classify intent ──────────────────────────────────────────────────
        intent, target_module, confidence = await self.router.classify(message, context)

        # ── Fallback: dormant professor in POC → reroute to place ────────────
        if intent == IntentType.DOMAIN and target_module and target_module not in POC_ACTIVE_PROFESSORS:
            target_module = POC_ACTIVE_PROFESSORS[0]

        # ── Build diagnostic note ────────────────────────────────────────────
        dean_note = await self._diagnostic_note(message, context, intent)

        # ── Personalised greeting (first message after onboarding) ───────────
        greeting = await self._maybe_greet(student_id, context)

        return HandoffPacket1(
            student_id=student_id,
            raw_message=message,
            intent_type=intent,
            target_module=target_module,
            confidence=confidence,
            student_context=context,
            dean_note=dean_note,
            greeting=greeting,
        )

    # ── Quality gate (called after professor responds) ────────────────────────

    async def quality_gate(self, response: AgentResponse, context: StudentContext) -> AgentResponse:
        if response.latency_ms > 15_000:
            logger.warning("slow_response", latency_ms=response.latency_ms, agent=response.source_agent)
        # Future: confidence scoring, content safety check
        return response

    # ── Ceremony ─────────────────────────────────────────────────────────────

    async def _ceremony(self, context: StudentContext, milestone: MilestoneType) -> CeremonyResponse:
        prompt_map = {
            MilestoneType.ONBOARDING: (
                f"Welcome {context.full_name} to BTU Virtual University. "
                "Write a warm 3-4 sentence onboarding speech from Dean Morgan. "
                "Mention the 30-chapter journey, 10 specialist professors, and weekly 15-hr sprint."
            ),
            MilestoneType.GRADUATION: (
                f"Write a celebratory 4-5 sentence graduation speech from Dean Morgan for {context.full_name}, "
                "who has just completed all 30 chapters of the BTU programme. "
                "Acknowledge their hard work and the skills they've gained."
            ),
        }
        result = await self._call_llm(
            system=DEAN_SYSTEM,
            messages=[{"role": "user", "content": prompt_map[milestone]}],
            max_tokens=512,
        )
        badge = "🎓 BTU Graduate" if milestone == MilestoneType.GRADUATION else "🎒 BTU Pioneer"

        # Persist ceremony record
        await self.memory.record_ceremony(context.student_id, milestone, result["text"])
        if milestone == MilestoneType.ONBOARDING:
            await self.memory.mark_onboarded(context.student_id)
        elif milestone == MilestoneType.GRADUATION:
            await self.memory.mark_graduated(context.student_id)

        return CeremonyResponse(
            milestone=milestone,
            ceremony_script=result["text"],
            badge_awarded=badge,
            confetti=milestone == MilestoneType.GRADUATION,
        )

    # ── Personalised greeting ────────────────────────────────────────────────

    async def _maybe_greet(self, student_id: str, context: StudentContext) -> str | None:
        """Generate a greeting for the student's first real message after onboarding,
        or a welcome-back note if they're returning after previous conversations."""
        msg_count = await self.memory.total_message_count(student_id)

        # First real message right after onboarding (ceremony creates ~2 messages)
        if msg_count <= 3:
            prompt = (
                f"The student {context.full_name} just completed onboarding and is sending "
                "their very first question at BTU Virtual University. "
                "Write a warm 1-2 sentence greeting from Dean Morgan. "
                "Address them by first name, welcome them, and tell them you're here to help. "
                "Keep it under 40 words."
            )
        # Returning student (has history)
        elif msg_count > 3:
            prompt = (
                f"Student {context.full_name} is back for another session. "
                f"They are on Chapter {context.current_chapter} "
                f"({context.completion_pct*100:.0f}% complete). "
                "Write a brief 1-sentence welcome-back from Dean Morgan. "
                "Address them by first name and acknowledge their progress. "
                "Keep it under 30 words."
            )
        else:
            return None

        result = await self._call_llm(
            system=DEAN_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            model=settings.HAIKU_MODEL,
        )
        return result["text"]

    # ── Diagnostic note ───────────────────────────────────────────────────────

    async def _diagnostic_note(
        self,
        message: str,
        context: StudentContext,
        intent: IntentType,
    ) -> str:
        prompt = (
            f"Student: {context.full_name} | Ch.{context.current_chapter} | "
            f"{context.completion_pct*100:.0f}% complete | "
            f"Sprint Week {context.sprint_week}: {context.sprint_hours}/{context.sprint_target}hrs\n"
            f"Intent: {intent.value}\n"
            f"Message: {message}\n"
            "Write a 1-2 sentence diagnostic note for the downstream agent. "
            "Note any gaps, urgency, or emotional cues."
        )
        result = await self._call_llm(
            system=DEAN_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=128,
            model=settings.HAIKU_MODEL,   # fast/cheap for internal note
        )
        return result["text"]
