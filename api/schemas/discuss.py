"""Discussion endpoint schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateRoomRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    room_type: str = Field(..., pattern="^(campus|library)$")
    chapter_hint: Optional[int] = Field(None, ge=1, le=30)
    professor_id: Optional[str] = None
    topic: Optional[str] = Field(None, max_length=500)


class RoomResponse(BaseModel):
    room_id: str
    title: str
    room_type: str
    chapter_hint: Optional[int] = None
    professor_id: Optional[str] = None
    topic: Optional[str] = None
    created_by: str
    is_active: bool
    member_count: int = 0
    created_at: str


class JoinRoomResponse(BaseModel):
    joined: bool
    room_id: str
    message: str


class PostMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class DiscussionMessageResponse(BaseModel):
    msg_id: int
    student_id: Optional[str] = None
    author: str
    content: str
    is_ai: bool
    created_at: str


class AIAssistRequest(BaseModel):
    prompt: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional nudge for the AI moderator (e.g., 'summarise', 'correct misconceptions')",
    )


class AIAssistResponse(BaseModel):
    content: str
    source_agent: str = "elias_vance"
    room_id: str


class MemberResponse(BaseModel):
    student_id: str
    full_name: str
    joined_at: str
