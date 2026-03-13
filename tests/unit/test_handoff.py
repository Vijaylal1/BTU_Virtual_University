"""Unit tests for handoff data models."""

import pytest
from pydantic import ValidationError

from agents.handoff import (
    HandoffPacket1,
    HandoffPacket2,
    IntentType,
    ProfessorBriefingPacket,
    StudentContext,
)


def _context() -> StudentContext:
    return StudentContext(
        student_id="abc-123",
        full_name="Alice",
        current_chapter=2,
        completion_pct=0.06,
        sprint_week=1,
        sprint_hours=5.0,
        sprint_target=15.0,
    )


def test_handoff_packet1_valid():
    p = HandoffPacket1(
        student_id="abc-123",
        raw_message="Tell me about location strategy",
        intent_type=IntentType.DOMAIN,
        target_module="place",
        confidence=0.85,
        student_context=_context(),
        dean_note="Student is early in programme",
    )
    assert p.confidence == 0.85
    assert p.intent_type == IntentType.DOMAIN


def test_handoff_packet1_invalid_confidence():
    with pytest.raises(ValidationError):
        HandoffPacket1(
            student_id="abc",
            raw_message="hello",
            intent_type=IntentType.DOMAIN,
            confidence=1.5,  # > 1.0 → invalid
            student_context=_context(),
        )


def test_handoff_packet2_valid():
    briefing = ProfessorBriefingPacket(
        student_name="Alice",
        current_chapter=2,
        completion_pct=0.06,
        sprint_context="Week 1: 5/15hrs",
    )
    p = HandoffPacket2(
        professor_id="place",
        briefing_packet=briefing,
        rag_chapters=[1, 2, 3],
        rag_pre_query="location strategy site selection",
    )
    assert p.professor_id == "place"
    assert p.rag_chapters == [1, 2, 3]
