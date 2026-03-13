"""
Discussion routes – Campus & Library group discussions.

Students can create or join discussion rooms tied to specific chapters or
modules, post messages, and ask Coach Elias (AI moderator) to weigh in.

Endpoints:
  POST /discuss/create              – create a new discussion room
  GET  /discuss/rooms               – list open rooms (filter by type/chapter)
  POST /discuss/{room_id}/join      – join a room
  POST /discuss/{room_id}/msg       – post a message
  GET  /discuss/{room_id}/msgs      – get room messages
  GET  /discuss/{room_id}/members   – get room members
  POST /discuss/{room_id}/ai        – ask Coach Elias to moderate / summarise
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.middleware.auth import require_auth
from api.schemas.discuss import (
    AIAssistRequest,
    AIAssistResponse,
    CreateRoomRequest,
    DiscussionMessageResponse,
    JoinRoomResponse,
    MemberResponse,
    PostMessageRequest,
    RoomResponse,
)
from agents.engine import PipelineEngine
from config.agent_config import CHAPTER_TO_PROFESSOR
from memory.store import MemoryStore

router = APIRouter(prefix="/discuss", tags=["discussion"])


def _get_store() -> MemoryStore:
    from api.app import get_memory_store
    return get_memory_store()


def _get_engine() -> PipelineEngine:
    from api.app import get_pipeline_engine
    return get_pipeline_engine()


# ── Create room ──────────────────────────────────────────────────────────────

@router.post("/create", response_model=RoomResponse, status_code=201)
async def create_room(
    req: CreateRoomRequest,
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> RoomResponse:
    """Create a new discussion room. The creator is auto-joined."""
    professor_id = req.professor_id
    if not professor_id and req.chapter_hint:
        professor_id = CHAPTER_TO_PROFESSOR.get(req.chapter_hint)

    room = await store.create_discussion_room(
        title=req.title,
        room_type=req.room_type,
        created_by=student_id,
        chapter_hint=req.chapter_hint,
        professor_id=professor_id,
        topic=req.topic,
    )
    return RoomResponse(
        room_id=str(room.room_id),
        title=room.title,
        room_type=room.room_type,
        chapter_hint=room.chapter_hint,
        professor_id=room.professor_id,
        topic=room.topic,
        created_by=str(room.created_by),
        is_active=room.is_active,
        member_count=1,
        created_at=str(room.created_at),
    )


# ── List rooms ───────────────────────────────────────────────────────────────

@router.get("/rooms", response_model=list[RoomResponse])
async def list_rooms(
    room_type: Optional[str] = Query(None, pattern="^(campus|library)$"),
    chapter: Optional[int] = Query(None, ge=1, le=30),
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> list[RoomResponse]:
    """List active discussion rooms, optionally filtered by type or chapter."""
    rooms = await store.list_discussion_rooms(room_type=room_type, chapter_hint=chapter)
    results = []
    for room in rooms:
        members = await store.get_room_members(str(room.room_id))
        results.append(RoomResponse(
            room_id=str(room.room_id),
            title=room.title,
            room_type=room.room_type,
            chapter_hint=room.chapter_hint,
            professor_id=room.professor_id,
            topic=room.topic,
            created_by=str(room.created_by),
            is_active=room.is_active,
            member_count=len(members),
            created_at=str(room.created_at),
        ))
    return results


# ── Join room ────────────────────────────────────────────────────────────────

@router.post("/{room_id}/join", response_model=JoinRoomResponse)
async def join_room(
    room_id: str,
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> JoinRoomResponse:
    """Join an existing discussion room."""
    room = await store.get_discussion_room(room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Room not found or closed")

    joined = await store.join_discussion_room(room_id, student_id)
    msg = "Joined successfully" if joined else "Already a member"
    return JoinRoomResponse(joined=joined, room_id=room_id, message=msg)


# ── Post message ─────────────────────────────────────────────────────────────

@router.post("/{room_id}/msg", response_model=DiscussionMessageResponse)
async def post_message(
    room_id: str,
    req: PostMessageRequest,
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> DiscussionMessageResponse:
    """Post a message to a discussion room."""
    room = await store.get_discussion_room(room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Room not found or closed")

    student = await store.get_student(student_id)
    msg = await store.post_discussion_message(room_id, req.content, student_id=student_id)
    return DiscussionMessageResponse(
        msg_id=msg.msg_id,
        student_id=student_id,
        author=student.full_name if student else "Unknown",
        content=msg.content,
        is_ai=False,
        created_at=str(msg.created_at),
    )


# ── Get messages ─────────────────────────────────────────────────────────────

@router.get("/{room_id}/msgs", response_model=list[DiscussionMessageResponse])
async def get_messages(
    room_id: str,
    limit: int = Query(50, ge=1, le=200),
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> list[DiscussionMessageResponse]:
    """Get messages from a discussion room."""
    room = await store.get_discussion_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    msgs = await store.get_discussion_messages(room_id, limit=limit)
    return [DiscussionMessageResponse(**m) for m in msgs]


# ── Get members ──────────────────────────────────────────────────────────────

@router.get("/{room_id}/members", response_model=list[MemberResponse])
async def get_members(
    room_id: str,
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> list[MemberResponse]:
    """List members of a discussion room."""
    room = await store.get_discussion_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    members = await store.get_room_members(room_id)
    return [MemberResponse(**m) for m in members]


# ── AI moderator ─────────────────────────────────────────────────────────────

@router.post("/{room_id}/ai", response_model=AIAssistResponse)
async def ai_assist(
    room_id: str,
    req: AIAssistRequest = AIAssistRequest(),
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
    store: MemoryStore = Depends(_get_store),
) -> AIAssistResponse:
    """
    Ask Coach Elias to moderate the discussion.

    Without a prompt, Elias reads the recent messages and provides a helpful
    synthesis or nudge. With a prompt (e.g., 'summarise', 'correct mistakes',
    'ask a follow-up question'), Elias responds accordingly.
    """
    room = await store.get_discussion_room(room_id)
    if not room or not room.is_active:
        raise HTTPException(status_code=404, detail="Room not found or closed")

    try:
        ai_text = await engine.discuss_ai(room_id, nudge=req.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Persist AI message in the room
    await store.post_discussion_message(room_id, ai_text, is_ai=True)

    return AIAssistResponse(content=ai_text, room_id=room_id)
