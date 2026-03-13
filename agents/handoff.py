"""
Pydantic v2 data contracts for the two-handoff context pipeline.

    User → Dean → HandoffPacket1 → Coach → HandoffPacket2 → Professor
                                         └→ CoachResponse (direct reply)

Also contains models for the Library and Doubt Clearing Session features.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    DOMAIN      = "domain"       # route to a professor
    CROSS_P     = "cross_p"      # cross-professor concept
    NAVIGATION  = "nav"          # course map / what's next
    MOTIVATION  = "motivation"   # coach handles directly
    CEREMONY    = "ceremony"     # onboarding / graduation
    SPRINT      = "sprint"       # sprint status check
    WHEEL       = "wheel"        # wheel of fortune
    LIBRARY     = "library"      # student visits the library (free exploration)
    DOUBT       = "doubt"        # student requests a doubt-clearing session with a professor


class MilestoneType(str, Enum):
    ONBOARDING  = "onboarding"
    CHAPTER_UP  = "chapter_completion"
    SPRINT_DONE = "sprint_completion"
    GRADUATION  = "graduation"


# ── Sub-models ────────────────────────────────────────────────────────────────

class StudentContext(BaseModel):
    student_id:       str
    full_name:        str
    current_chapter:  int = 1
    completion_pct:   float = Field(ge=0.0, le=1.0, default=0.0)
    sprint_week:      int = 1
    sprint_hours:     float = 0.0
    sprint_target:    float = 15.0
    recent_summaries: list[str] = Field(default_factory=list)
    badge_count:      int = 0
    last_agent:       Optional[str] = None


class ProfessorBriefingPacket(BaseModel):
    """Compact context passed from coach to professor."""
    student_name:     str
    current_chapter:  int
    completion_pct:   float
    sprint_context:   str              # e.g. "Week 3, 9/15 hrs"
    recent_summaries: list[str] = Field(default_factory=list)
    coach_note:       str = ""         # Elias's framing note


class CeremonyResponse(BaseModel):
    milestone:       MilestoneType
    ceremony_script: str
    badge_awarded:   Optional[str] = None
    confetti:        bool = False


class WheelPrize(BaseModel):
    prize_label: str
    prize_type:  str   # "bonus_hours" | "double_xp" | "hint" | "skip" | "mystery"
    value:       Any = None


# ── Handoff Packets ───────────────────────────────────────────────────────────

class HandoffPacket1(BaseModel):
    """Tier-1 → Tier-2: Dean to Coach."""
    student_id:      str
    raw_message:     str
    intent_type:     IntentType
    target_module:   Optional[str] = None   # professor_id if intent==DOMAIN
    confidence:      float = Field(ge=0.0, le=1.0, default=0.8)
    student_context: StudentContext
    dean_note:       str = ""               # diagnostic framing from Dean
    handle_directly: bool = False           # Dean handles without escalation
    greeting:        Optional[str] = None   # personalised greeting (first msg / welcome back)


class HandoffPacket2(BaseModel):
    """Tier-2 → Tier-3: Coach to Professor."""
    professor_id:     str
    briefing_packet:  ProfessorBriefingPacket
    rag_chapters:     list[int]
    rag_pre_query:    str                   # refined query for RAG
    session_history:  list[dict] = Field(default_factory=list)
    thinking_budget:  int = 8000
    mode:             str = "normal"        # "normal" | "doubt_clearing"


# ── Library models ────────────────────────────────────────────────────────────

class LibrarySearchResult(BaseModel):
    """A single retrieved resource from the BTU Library."""
    chapter:   int
    excerpt:   str
    score:     float
    source:    str = ""
    professor: str = ""   # professor_id responsible for this chapter


class LibraryResponse(BaseModel):
    """Response from the library search pipeline."""
    answer:             str
    resources:          list[LibrarySearchResult] = Field(default_factory=list)
    chapters_searched:  list[int] = Field(default_factory=list)
    rag_rounds_used:    int = 1
    retrieval_trace:    list[dict] = Field(default_factory=list)
    latency_ms:         int = 0


# ── Doubt Clearing models ─────────────────────────────────────────────────────

class DoubtPacket(BaseModel):
    """Carries a doubt-clearing request directly to a professor."""
    student_id:      str
    student_context: StudentContext
    professor_id:    str
    doubt_question:  str
    chapter_hint:    Optional[int] = None   # chapter the doubt is about


class DoubtResponse(BaseModel):
    """Structured response from a professor during a doubt session."""
    explanation:          str
    follow_up_questions:  list[str] = Field(default_factory=list)
    suggested_chapters:   list[int] = Field(default_factory=list)
    professor_id:         str
    rag_chunks_used:      int = 0
    latency_ms:           int = 0


# ── Response Models ───────────────────────────────────────────────────────────

class AgentResponse(BaseModel):
    """Unified response returned from the pipeline to the API."""
    text:           str
    source_agent:   str
    thinking:       Optional[str] = None
    latency_ms:     int = 0
    ceremony:       Optional[CeremonyResponse] = None
    sprint_status:  Optional[dict] = None
    wheel_prize:    Optional[WheelPrize] = None
    rag_chunks_used: int = 0


class CoachResponse(BaseModel):
    """Used when Coach handles the query directly (nav / motivation / sprint / wheel / library)."""
    response_text: str
    source_agent:  str = "elias_vance"
    sprint_status: Optional[dict] = None
    wheel_prize:   Optional[WheelPrize] = None
