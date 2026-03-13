"""Unit tests for intent router."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.handoff import IntentType, StudentContext
from agents.router import IntentRouter


def _make_context(**kwargs) -> StudentContext:
    defaults = dict(
        student_id="test-student-uuid",
        full_name="Test Student",
        current_chapter=1,
        completion_pct=0.0,
        sprint_week=1,
        sprint_hours=0.0,
        sprint_target=15.0,
    )
    return StudentContext(**(defaults | kwargs))


@pytest.mark.asyncio
async def test_classify_domain_intent():
    """Router correctly classifies a domain question."""
    router = IntentRouter()
    fake_content = MagicMock()
    fake_content.text = '{"intent": "domain", "target_module": "place", "confidence": 0.9}'

    fake_response = MagicMock()
    fake_response.content = [fake_content]

    with patch.object(router._client.messages, "create", new=AsyncMock(return_value=fake_response)):
        intent, target, confidence = await router.classify(
            "What is the best strategy for choosing a location?",
            _make_context(),
        )

    assert intent == IntentType.DOMAIN
    assert target == "place"
    assert confidence == 0.9


@pytest.mark.asyncio
async def test_classify_fallback_on_error():
    """Router falls back gracefully on API errors."""
    router = IntentRouter()

    with patch.object(router._client.messages, "create", new=AsyncMock(side_effect=Exception("API down"))):
        intent, target, confidence = await router.classify("any message", _make_context())

    assert intent == IntentType.DOMAIN
    assert confidence == 0.5


def test_intent_type_values():
    """All IntentType values are valid strings."""
    for member in IntentType:
        assert isinstance(member.value, str)
