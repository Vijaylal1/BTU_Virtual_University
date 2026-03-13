"""
Intent router – classifies incoming student messages into IntentType.
Uses a fast Haiku call with a structured JSON prompt.
"""

from __future__ import annotations

import json
import re

import anthropic
import structlog

from agents.handoff import IntentType, StudentContext
from config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

_SYSTEM = """
You are an intent classifier for the BTU Virtual University chat system.
Given a student message and context, classify the intent into EXACTLY one of:
  domain      – question about BTU course content (route to a professor)
  cross_p     – spans multiple professor domains
  nav         – navigation / what chapter / what's next
  motivation  – emotional support / motivation
  ceremony    – onboarding or graduation milestone
  sprint      – sprint hours / weekly target check
  wheel       – wheel of fortune request
  library     – student wants to browse/search the BTU Library (e.g. "take me to the library",
                "search library for X", "I want to explore resources on Y")
  doubt       – student wants to clear a specific doubt with a professor (e.g. "I have a doubt
                about pricing", "can I ask Prof. Priya about chapter 2", "doubt session")

Also identify the target_module (professor_id like "place", "people", etc.) when intent=domain or intent=doubt.
Respond ONLY with valid JSON:
{"intent": "<intent>", "target_module": "<professor_id or null>", "confidence": <0.0-1.0>}
""".strip()


class IntentRouter:
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def classify(self, message: str, context: StudentContext) -> tuple[IntentType, str | None, float]:
        """Returns (intent_type, target_module, confidence)."""
        user_msg = (
            f"Student: {context.full_name}\n"
            f"Current chapter: {context.current_chapter}\n"
            f"Message: {message}"
        )
        try:
            response = await self._client.messages.create(
                model=settings.HAIKU_MODEL,
                max_tokens=256,
                system=_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = response.content[0].text.strip()
            # Strip markdown fences if present
            raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("```").strip()
            data = json.loads(raw)
            intent = IntentType(data.get("intent", "domain"))
            target = data.get("target_module") or None
            confidence = float(data.get("confidence", 0.75))
            logger.debug("intent_classified", intent=intent, target=target, conf=confidence)
            return intent, target, confidence
        except Exception as exc:
            logger.warning("intent_classification_failed", error=str(exc))
            return IntentType.DOMAIN, None, 0.5
