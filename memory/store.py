"""
MemoryStore – async PostgreSQL-backed persistence layer.
All public methods are async and use SQLAlchemy 2.x async sessions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agents.handoff import MilestoneType, StudentContext
from config.settings import get_settings
from memory.models import (
    Base,
    Ceremony,
    ChapterProgress,
    CrossAgentSummary,
    DiscussionMember,
    DiscussionMessage,
    DiscussionRoom,
    DoubtSession,
    LibraryResource,
    LibrarySession,
    Message,
    Sprint,
    Student,
    WheelSpin,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class MemoryStore:
    def __init__(self) -> None:
        import re

        db_url = re.sub(r"[?&]sslmode=\w+", "", settings.DATABASE_URL)
        connect_args = {"ssl": True} if "neon.tech" in settings.DATABASE_URL else {}
        self._engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def init_db(self) -> None:
        """Create all tables if they don't exist (dev convenience; use migrations in prod)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _session(self) -> AsyncSession:
        return self._session_factory()

    # ── Student ───────────────────────────────────────────────────────────────

    async def get_student(self, student_id: str) -> Optional[Student]:
        async with self._session() as s:
            return await s.get(Student, uuid.UUID(student_id))

    async def get_student_by_email(self, email: str) -> Optional[Student]:
        async with self._session() as s:
            result = await s.execute(select(Student).where(Student.email == email))
            return result.scalar_one_or_none()

    async def create_student(
        self, email: str, full_name: str, hashed_pw: str
    ) -> Student:
        async with self._session() as s:
            student = Student(email=email, full_name=full_name, hashed_pw=hashed_pw)
            s.add(student)
            await s.commit()
            await s.refresh(student)
            return student

    async def get_student_context(self, student_id: str) -> StudentContext:
        """Build the StudentContext used by Dean for routing."""
        async with self._session() as s:
            student = await s.get(Student, uuid.UUID(student_id))
            if not student:
                raise ValueError(f"Student {student_id} not found")

            result = await s.execute(
                select(ChapterProgress)
                .where(ChapterProgress.student_id == uuid.UUID(student_id))
                .order_by(ChapterProgress.chapter_number)
            )
            chapters = result.scalars().all()
            completed = sum(1 for c in chapters if c.status == "completed")
            current_ch = max(
                (c.chapter_number for c in chapters if c.status == "in_progress"),
                default=1,
            )
            completion_pct = completed / 30.0

            sprint_result = await s.execute(
                select(Sprint)
                .where(
                    Sprint.student_id == uuid.UUID(student_id),
                    Sprint.status == "active",
                )
                .order_by(Sprint.week_number.desc())
                .limit(1)
            )
            sprint = sprint_result.scalar_one_or_none()
            sprint_week = sprint.week_number if sprint else 1
            sprint_hours = sprint.hours_logged if sprint else 0.0

            summ_result = await s.execute(
                select(CrossAgentSummary.summary_text)
                .where(CrossAgentSummary.student_id == uuid.UUID(student_id))
                .order_by(CrossAgentSummary.created_at.desc())
                .limit(5)
            )
            recent_summaries = [row[0] for row in summ_result.all()]

            badge_count_result = await s.execute(
                select(func.count()).where(
                    WheelSpin.student_id == uuid.UUID(student_id)
                )
            )
            badge_count = badge_count_result.scalar() or 0

            return StudentContext(
                student_id=student_id,
                full_name=student.full_name,
                current_chapter=current_ch,
                completion_pct=completion_pct,
                sprint_week=sprint_week,
                sprint_hours=sprint_hours,
                sprint_target=15.0,
                recent_summaries=recent_summaries,
                badge_count=badge_count,
            )

    # ── Messages ──────────────────────────────────────────────────────────────

    async def get_or_create_session(self, student_id: str) -> uuid.UUID:
        """Return the most recent active session for the student, creating one if needed."""
        async with self._session() as s:
            from memory.models import Session as SessionModel

            result = await s.execute(
                select(SessionModel)
                .where(SessionModel.student_id == uuid.UUID(student_id))
                .order_by(SessionModel.created_at.desc())
                .limit(1)
            )
            session = result.scalar_one_or_none()
            if session:
                return session.session_id
            new_session = SessionModel(student_id=uuid.UUID(student_id))
            s.add(new_session)
            await s.commit()
            await s.refresh(new_session)
            return new_session.session_id

    async def save_message(
        self,
        student_id: str,
        role: str,
        content: str,
        source_agent: Optional[str] = None,
        thinking: Optional[str] = None,
        latency_ms: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> None:
        try:
            sid = (
                uuid.UUID(session_id)
                if session_id
                else await self.get_or_create_session(student_id)
            )
            async with self._session() as s:
                msg = Message(
                    session_id=sid,
                    student_id=uuid.UUID(student_id),
                    role=role,
                    content=content,
                    source_agent=source_agent,
                    thinking=thinking,
                    latency_ms=latency_ms,
                )
                s.add(msg)
                await s.commit()
        except Exception as exc:
            logger.error(
                "save_message_failed", student_id=student_id, role=role, error=str(exc)
            )
            raise

    async def get_recent_messages(self, student_id: str, limit: int = 10) -> list[dict]:
        async with self._session() as s:
            result = await s.execute(
                select(Message)
                .where(Message.student_id == uuid.UUID(student_id))
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            msgs = result.scalars().all()
            return [
                {"role": m.role, "content": m.content, "source_agent": m.source_agent}
                for m in reversed(msgs)
            ]

    async def message_count_since_last_summary(
        self, student_id: str, professor_id: str
    ) -> int:
        """Count messages since the last cross-agent summary for this professor."""
        async with self._session() as s:
            last_summary = await s.execute(
                select(CrossAgentSummary.created_at)
                .where(
                    CrossAgentSummary.student_id == uuid.UUID(student_id),
                    CrossAgentSummary.professor_id == professor_id,
                )
                .order_by(CrossAgentSummary.created_at.desc())
                .limit(1)
            )
            row = last_summary.scalar_one_or_none()
            since = row if row else datetime(2000, 1, 1, tzinfo=timezone.utc)

            count_result = await s.execute(
                select(func.count()).where(
                    Message.student_id == uuid.UUID(student_id),
                    Message.source_agent == professor_id,
                    Message.created_at > since,
                )
            )
            return count_result.scalar() or 0

    # ── Summaries ─────────────────────────────────────────────────────────────

    async def save_summary(
        self, student_id: str, professor_id: str, summary_text: str
    ) -> None:
        async with self._session() as s:
            summary = CrossAgentSummary(
                student_id=uuid.UUID(student_id),
                professor_id=professor_id,
                summary_text=summary_text,
            )
            s.add(summary)
            await s.commit()

    # ── Ceremonies ────────────────────────────────────────────────────────────

    async def record_ceremony(
        self, student_id: str, milestone: MilestoneType, script: str
    ) -> None:
        async with self._session() as s:
            s.add(
                Ceremony(
                    student_id=uuid.UUID(student_id),
                    milestone=milestone.value,
                    script=script,
                )
            )
            await s.commit()

    async def is_onboarded(self, student_id: str) -> bool:
        async with self._session() as s:
            student = await s.get(Student, uuid.UUID(student_id))
            return bool(student and student.onboarded)

    async def mark_onboarded(self, student_id: str) -> None:
        async with self._session() as s:
            student = await s.get(Student, uuid.UUID(student_id))
            if student:
                student.onboarded = True
                await s.commit()

    async def is_graduated(self, student_id: str) -> bool:
        async with self._session() as s:
            student = await s.get(Student, uuid.UUID(student_id))
            return bool(student and student.graduated)

    async def mark_graduated(self, student_id: str) -> None:
        async with self._session() as s:
            student = await s.get(Student, uuid.UUID(student_id))
            if student:
                student.graduated = True
                await s.commit()

    async def total_message_count(self, student_id: str) -> int:
        async with self._session() as s:
            result = await s.execute(
                select(func.count(Message.message_id)).where(
                    Message.student_id == uuid.UUID(student_id)
                )
            )
            return result.scalar_one()

    # ── Sprint helpers ────────────────────────────────────────────────────────

    async def get_latest_sprint(self, student_id: str) -> Optional[Sprint]:
        async with self._session() as s:
            result = await s.execute(
                select(Sprint)
                .where(Sprint.student_id == uuid.UUID(student_id))
                .order_by(Sprint.week_number.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_active_sprint(self, student_id: str) -> Optional[Sprint]:
        async with self._session() as s:
            result = await s.execute(
                select(Sprint)
                .where(
                    Sprint.student_id == uuid.UUID(student_id),
                    Sprint.status == "active",
                )
                .order_by(Sprint.week_number.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def log_sprint_hours(self, student_id: str, hours: float) -> Sprint:
        async with self._session() as s:
            sprint = await s.execute(
                select(Sprint)
                .where(
                    Sprint.student_id == uuid.UUID(student_id),
                    Sprint.status == "active",
                )
                .order_by(Sprint.week_number.desc())
                .limit(1)
            )
            sprint = sprint.scalar_one_or_none()
            if not sprint:
                result = await s.execute(
                    select(func.max(Sprint.week_number)).where(
                        Sprint.student_id == uuid.UUID(student_id)
                    )
                )
                max_week = result.scalar() or 0
                sprint = Sprint(
                    student_id=uuid.UUID(student_id),
                    week_number=max_week + 1,
                    hours_logged=hours,
                )
                s.add(sprint)
            else:
                sprint.hours_logged = (sprint.hours_logged or 0.0) + hours
                if sprint.hours_logged >= sprint.target_hours:
                    sprint.status = "completed"
                    sprint.completed_at = datetime.now(timezone.utc)
            await s.commit()
            await s.refresh(sprint)
            return sprint

    # ── Wheel spins ───────────────────────────────────────────────────────────

    async def save_wheel_spin(
        self, student_id: str, prize: str, prize_type: str
    ) -> None:
        try:
            async with self._session() as s:
                s.add(
                    WheelSpin(
                        student_id=uuid.UUID(student_id),
                        prize=prize,
                        prize_type=prize_type,
                    )
                )
                await s.commit()
            logger.info("wheel_spin_saved", student_id=student_id, prize=prize)
        except Exception as exc:
            logger.error(
                "wheel_spin_save_failed", student_id=student_id, error=str(exc)
            )
            raise

    # ── Chapter progress ──────────────────────────────────────────────────────

    async def update_chapter_status(
        self, student_id: str, chapter: int, status: str
    ) -> None:
        async with self._session() as s:
            result = await s.execute(
                select(ChapterProgress).where(
                    ChapterProgress.student_id == uuid.UUID(student_id),
                    ChapterProgress.chapter_number == chapter,
                )
            )
            progress = result.scalar_one_or_none()
            now = datetime.now(timezone.utc)
            if progress:
                progress.status = status
                if status == "in_progress" and not progress.started_at:
                    progress.started_at = now
                if status == "completed":
                    progress.completed_at = now
            else:
                s.add(
                    ChapterProgress(
                        student_id=uuid.UUID(student_id),
                        chapter_number=chapter,
                        status=status,
                        started_at=now if status == "in_progress" else None,
                        completed_at=now if status == "completed" else None,
                    )
                )
            await s.commit()

    # ── Discussion rooms ─────────────────────────────────────────────────────

    async def create_discussion_room(
        self,
        title: str,
        room_type: str,
        created_by: str,
        chapter_hint: Optional[int] = None,
        professor_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> DiscussionRoom:
        async with self._session() as s:
            room = DiscussionRoom(
                title=title,
                room_type=room_type,
                chapter_hint=chapter_hint,
                professor_id=professor_id,
                topic=topic,
                created_by=uuid.UUID(created_by),
            )
            s.add(room)
            await s.flush()
            s.add(
                DiscussionMember(room_id=room.room_id, student_id=uuid.UUID(created_by))
            )
            await s.commit()
            await s.refresh(room)
            return room

    async def list_discussion_rooms(
        self, room_type: Optional[str] = None, chapter_hint: Optional[int] = None
    ) -> list[DiscussionRoom]:
        async with self._session() as s:
            q = select(DiscussionRoom).where(DiscussionRoom.is_active == True)
            if room_type:
                q = q.where(DiscussionRoom.room_type == room_type)
            if chapter_hint is not None:
                q = q.where(DiscussionRoom.chapter_hint == chapter_hint)
            q = q.order_by(DiscussionRoom.created_at.desc())
            result = await s.execute(q)
            return list(result.scalars().all())

    async def get_discussion_room(self, room_id: str) -> Optional[DiscussionRoom]:
        async with self._session() as s:
            return await s.get(DiscussionRoom, uuid.UUID(room_id))

    async def join_discussion_room(self, room_id: str, student_id: str) -> bool:
        """Join a room. Returns False if already a member."""
        async with self._session() as s:
            existing = await s.execute(
                select(DiscussionMember).where(
                    DiscussionMember.room_id == uuid.UUID(room_id),
                    DiscussionMember.student_id == uuid.UUID(student_id),
                )
            )
            if existing.scalar_one_or_none():
                return False
            s.add(
                DiscussionMember(
                    room_id=uuid.UUID(room_id), student_id=uuid.UUID(student_id)
                )
            )
            await s.commit()
            return True

    async def get_room_members(self, room_id: str) -> list[dict]:
        async with self._session() as s:
            result = await s.execute(
                select(DiscussionMember, Student)
                .join(Student, DiscussionMember.student_id == Student.student_id)
                .where(DiscussionMember.room_id == uuid.UUID(room_id))
                .order_by(DiscussionMember.joined_at)
            )
            return [
                {
                    "student_id": str(m.student_id),
                    "full_name": st.full_name,
                    "joined_at": str(m.joined_at),
                }
                for m, st in result.all()
            ]

    async def post_discussion_message(
        self,
        room_id: str,
        content: str,
        student_id: Optional[str] = None,
        is_ai: bool = False,
    ) -> DiscussionMessage:
        async with self._session() as s:
            msg = DiscussionMessage(
                room_id=uuid.UUID(room_id),
                student_id=uuid.UUID(student_id) if student_id else None,
                content=content,
                is_ai=is_ai,
            )
            s.add(msg)
            await s.commit()
            await s.refresh(msg)
            return msg

    async def get_discussion_messages(
        self, room_id: str, limit: int = 50
    ) -> list[dict]:
        async with self._session() as s:
            result = await s.execute(
                select(DiscussionMessage, Student)
                .outerjoin(Student, DiscussionMessage.student_id == Student.student_id)
                .where(DiscussionMessage.room_id == uuid.UUID(room_id))
                .order_by(DiscussionMessage.created_at.asc())
                .limit(limit)
            )
            return [
                {
                    "msg_id": m.msg_id,
                    "student_id": str(m.student_id) if m.student_id else None,
                    "author": st.full_name if st else "Coach Elias",
                    "content": m.content,
                    "is_ai": m.is_ai,
                    "created_at": str(m.created_at),
                }
                for m, st in result.all()
            ]

    # ── Library resources ────────────────────────────────────────────────────

    async def add_library_resource(
        self,
        title: str,
        resource_type: str,
        url: Optional[str] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        chapters: Optional[list[int]] = None,
        professor_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        added_by: Optional[str] = None,
    ) -> LibraryResource:
        async with self._session() as s:
            res = LibraryResource(
                title=title,
                resource_type=resource_type,
                url=url,
                description=description,
                author=author,
                chapters=",".join(str(c) for c in chapters) if chapters else None,
                professor_id=professor_id,
                tags=",".join(tags) if tags else None,
                added_by=uuid.UUID(added_by) if added_by else None,
            )
            s.add(res)
            await s.commit()
            await s.refresh(res)
            return res

    async def list_library_resources(
        self,
        resource_type: Optional[str] = None,
        chapter: Optional[int] = None,
        professor_id: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> list[LibraryResource]:
        async with self._session() as s:
            q = select(LibraryResource).where(LibraryResource.is_approved == True)
            if resource_type:
                q = q.where(LibraryResource.resource_type == resource_type)
            if chapter is not None:
                q = q.where(LibraryResource.chapters.contains(str(chapter)))
            if professor_id:
                q = q.where(LibraryResource.professor_id == professor_id)
            if tag:
                q = q.where(LibraryResource.tags.contains(tag))
            if search:
                pattern = f"%{search}%"
                q = q.where(
                    LibraryResource.title.ilike(pattern)
                    | LibraryResource.description.ilike(pattern)
                    | LibraryResource.tags.ilike(pattern)
                )
            q = q.order_by(LibraryResource.created_at.desc()).limit(limit)
            result = await s.execute(q)
            return list(result.scalars().all())

    async def get_library_resource(self, resource_id: str) -> Optional[LibraryResource]:
        async with self._session() as s:
            return await s.get(LibraryResource, uuid.UUID(resource_id))

    # ── Library session logs ──────────────────────────────────────────────────

    async def save_library_session(
        self,
        student_id: str,
        query: str,
        answer: str,
        chapters_hit: list[int],
        rag_rounds: int = 1,
        latency_ms: Optional[int] = None,
    ) -> None:
        async with self._session() as s:
            s.add(
                LibrarySession(
                    student_id=uuid.UUID(student_id),
                    query=query,
                    answer=answer,
                    chapters_hit=chapters_hit,
                    rag_rounds=rag_rounds,
                    latency_ms=latency_ms,
                )
            )
            await s.commit()

    # ── Doubt session logs ────────────────────────────────────────────────────

    async def save_doubt_session(
        self,
        student_id: str,
        professor_id: str,
        doubt_question: str,
        explanation: str,
        follow_up_questions: list[str],
        suggested_chapters: list[int],
        rag_chunks_used: int = 0,
        chapter_hint: Optional[int] = None,
        latency_ms: Optional[int] = None,
    ) -> None:
        async with self._session() as s:
            s.add(
                DoubtSession(
                    student_id=uuid.UUID(student_id),
                    professor_id=professor_id,
                    doubt_question=doubt_question,
                    explanation=explanation,
                    follow_up_questions=follow_up_questions,
                    suggested_chapters=suggested_chapters,
                    rag_chunks_used=rag_chunks_used,
                    chapter_hint=chapter_hint,
                    latency_ms=latency_ms,
                )
            )
            await s.commit()
