"""
Upward Summariser – runs every SUMMARISE_EVERY_N messages per professor.
Uses claude-haiku-4-5 (fast, cheap) to produce 2-3 sentence cross-agent summaries.
"""

from __future__ import annotations

import anthropic
import structlog

from config.settings import get_settings
from memory.store import MemoryStore

logger = structlog.get_logger(__name__)
settings = get_settings()

_SYSTEM = """
You are a concise academic note-taker for BTU Virtual University.
Given a short conversation excerpt between a student and a professor,
write a 2-3 sentence factual summary that captures:
  1. The key topic(s) discussed
  2. Any knowledge gaps or breakthroughs
  3. Student's current understanding level

Respond ONLY with the summary paragraph. No bullet points. No headers.
""".strip()


class Summariser:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def summarise_and_store(
        self,
        student_id: str,
        professor_id: str,
        messages: list[dict],
    ) -> str:
        """Generate and persist a cross-agent summary."""
        conversation = "\n".join(
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in messages
        )
        try:
            response = await self._client.messages.create(
                model=settings.HAIKU_MODEL,
                max_tokens=256,
                system=_SYSTEM,
                messages=[{"role": "user", "content": conversation}],
            )
            summary = response.content[0].text.strip()
            await self.memory.save_summary(student_id, professor_id, summary)
            logger.info("summary_saved", student_id=student_id, professor_id=professor_id, length=len(summary))
            return summary
        except Exception as exc:
            logger.error("summarisation_failed", error=str(exc))
            return ""
