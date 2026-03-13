"""Doubt Clearing Session endpoint request/response schemas."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class DoubtRequest(BaseModel):
    doubt_question: str = Field(..., min_length=1, max_length=2000)
    chapter_hint: Optional[int] = Field(
        None,
        ge=1,
        le=30,
        description="Chapter number the doubt is about. Used to auto-select the professor.",
    )


class ProfessorDoubtRequest(BaseModel):
    doubt_question: str = Field(..., min_length=1, max_length=2000)
    professor_id: str = Field(..., description="e.g. 'place', 'pricing', 'people'")
    chapter_hint: Optional[int] = Field(None, ge=1, le=30)


class DoubtResponse(BaseModel):
    explanation: str
    follow_up_questions: list[str]
    suggested_chapters: list[int]
    professor_id: str
    rag_chunks_used: int
    latency_ms: int
