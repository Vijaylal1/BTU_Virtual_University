"""
Abstract base class shared by all BTU agents (Dean, Coach, Professors).
Provides the Anthropic client, structured logging, and a common call helper.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import anthropic
import structlog

from config.settings import get_settings

if TYPE_CHECKING:
    from memory.store import MemoryStore

logger = structlog.get_logger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    agent_id: str = "base"
    tier: int = 0

    def __init__(self, memory: "MemoryStore") -> None:
        self.memory = memory
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._log = logger.bind(agent=self.agent_id)

    # ── Core LLM call ─────────────────────────────────────────────────────────

    async def _call_llm(
        self,
        system: str,
        messages: list[dict],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        use_thinking: bool = False,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Unified Anthropic call.  Returns:
            {"text": str, "thinking": str | None, "latency_ms": int}
        Uses adaptive thinking for Opus; streaming for large outputs.
        """
        model = model or settings.CLAUDE_MODEL
        start = time.monotonic()

        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )

        if use_thinking and model == settings.CLAUDE_MODEL:
            kwargs["thinking"] = {"type": "adaptive"}

        try:
            if stream or max_tokens >= 8000:
                async with self._client.messages.stream(**kwargs) as s:
                    final = await s.get_final_message()
            else:
                final = await self._client.messages.create(**kwargs)

            text = ""
            thinking = None
            for block in final.content:
                if block.type == "thinking":
                    thinking = block.thinking
                elif block.type == "text":
                    text = block.text

            latency_ms = int((time.monotonic() - start) * 1000)
            self._log.debug("llm_call_ok", model=model, latency_ms=latency_ms)
            return {"text": text, "thinking": thinking, "latency_ms": latency_ms}

        except anthropic.RateLimitError:
            self._log.warning("rate_limit_hit")
            raise
        except anthropic.APIError as exc:
            self._log.error("api_error", status=exc.status_code, msg=str(exc))
            raise

    # ── Streaming generator (SSE) ─────────────────────────────────────────────

    async def _stream_llm(
        self,
        system: str,
        messages: list[dict],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
    ):
        """Async generator that yields text chunks for SSE endpoints."""
        model = model or settings.CLAUDE_MODEL
        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            thinking={"type": "adaptive"},
        )
        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    @abstractmethod
    async def handle(self, *args: Any, **kwargs: Any) -> Any:
        """Each agent implements its own primary handler."""
        ...
