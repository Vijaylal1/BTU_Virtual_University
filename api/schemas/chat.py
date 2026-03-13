"""Chat endpoint request/response schemas."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    source_agent: str
    latency_ms: int
    rag_chunks_used: int = 0
    ceremony: Optional[dict] = None
    sprint_status: Optional[dict] = None
    wheel_prize: Optional[dict] = None


class UploadResponse(BaseModel):
    filename: str
    message: str
