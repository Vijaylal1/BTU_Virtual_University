"""
SQLAlchemy ORM models mirroring schema.sql.
All models use async-compatible patterns via asyncpg.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    student_id  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email       = Column(String, unique=True, nullable=False)
    full_name   = Column(String, nullable=False)
    hashed_pw   = Column(String, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    onboarded   = Column(Boolean, default=False)
    graduated   = Column(Boolean, default=False)

    sessions = relationship("Session", back_populates="student", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="student", cascade="all, delete-orphan")
    sprints  = relationship("Sprint", back_populates="student", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    session_id  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id  = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="sessions")


class Message(Base):
    __tablename__ = "messages"

    message_id   = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id   = Column(UUID(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    role         = Column(String, nullable=False)
    content      = Column(Text, nullable=False)
    source_agent = Column(String)
    thinking     = Column(Text)
    latency_ms   = Column(Integer)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="messages")


class CrossAgentSummary(Base):
    __tablename__ = "cross_agent_summaries"

    summary_id   = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    professor_id = Column(String, nullable=False)
    summary_text = Column(Text, nullable=False)
    msg_count    = Column(Integer, default=5)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


class Sprint(Base):
    __tablename__ = "sprints"

    sprint_id    = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    week_number  = Column(Integer, nullable=False)
    hours_logged = Column(Float, default=0.0)
    target_hours = Column(Float, default=15.0)
    started_at   = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status       = Column(String, default="active")

    student = relationship("Student", back_populates="sprints")


class WheelSpin(Base):
    __tablename__ = "wheel_spins"

    spin_id    = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    prize      = Column(String, nullable=False)
    prize_type = Column(String, nullable=False)
    spun_at    = Column(DateTime(timezone=True), server_default=func.now())


class Ceremony(Base):
    __tablename__ = "ceremonies"

    ceremony_id  = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    milestone    = Column(String, nullable=False)
    script       = Column(Text, nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())


class ChapterProgress(Base):
    __tablename__ = "chapter_progress"

    progress_id    = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id     = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    status         = Column(String, default="locked")
    started_at     = Column(DateTime(timezone=True))
    completed_at   = Column(DateTime(timezone=True))


# ── Library Session logs ──────────────────────────────────────────────────────

class LibrarySession(Base):
    __tablename__ = "library_sessions"

    session_id   = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id   = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    query        = Column(Text, nullable=False)
    answer       = Column(Text, nullable=False)
    chapters_hit = Column(ARRAY(Integer), nullable=False, default=[])
    rag_rounds   = Column(Integer, nullable=False, default=1)
    latency_ms   = Column(Integer)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())


# ── Doubt Clearing Session logs ──────────────────────────────────────────────

class DoubtSession(Base):
    __tablename__ = "doubt_sessions"

    doubt_id            = Column(BigInteger, primary_key=True, autoincrement=True)
    student_id          = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    professor_id        = Column(String, nullable=False)
    doubt_question      = Column(Text, nullable=False)
    explanation         = Column(Text, nullable=False)
    follow_up_questions = Column(JSONB, nullable=False, default=[])
    suggested_chapters  = Column(ARRAY(Integer), nullable=False, default=[])
    rag_chunks_used     = Column(Integer, nullable=False, default=0)
    chapter_hint        = Column(Integer)
    latency_ms          = Column(Integer)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())


# ── Group Discussion models ──────────────────────────────────────────────────

class DiscussionRoom(Base):
    __tablename__ = "discussion_rooms"

    room_id      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title        = Column(String, nullable=False)
    room_type    = Column(String, nullable=False)        # "campus" | "library"
    chapter_hint = Column(Integer)                       # chapter number (campus rooms)
    professor_id = Column(String)                        # owning professor's module
    topic        = Column(Text)                          # free-text topic description
    created_by   = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    members  = relationship("DiscussionMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("DiscussionMessage", back_populates="room", cascade="all, delete-orphan")


class DiscussionMember(Base):
    __tablename__ = "discussion_members"

    member_id  = Column(BigInteger, primary_key=True, autoincrement=True)
    room_id    = Column(UUID(as_uuid=True), ForeignKey("discussion_rooms.room_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    joined_at  = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("DiscussionRoom", back_populates="members")


class DiscussionMessage(Base):
    __tablename__ = "discussion_messages"

    msg_id     = Column(BigInteger, primary_key=True, autoincrement=True)
    room_id    = Column(UUID(as_uuid=True), ForeignKey("discussion_rooms.room_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"))  # NULL for AI messages
    content    = Column(Text, nullable=False)
    is_ai      = Column(Boolean, default=False)          # True = Coach Elias message
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("DiscussionRoom", back_populates="messages")


# ── Library Resource catalog ─────────────────────────────────────────────────

class LibraryResource(Base):
    __tablename__ = "library_resources"

    resource_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title         = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)      # "paper" | "video" | "article" | "case_study" | "book"
    url           = Column(Text)                         # external link (YouTube, DOI, blog, etc.)
    description   = Column(Text)
    author        = Column(String)                       # author / creator / publisher
    chapters      = Column(String)                       # comma-separated chapter numbers (e.g., "1,2,5")
    professor_id  = Column(String)                       # related professor module
    tags          = Column(String)                       # comma-separated tags (e.g., "marketing,strategy")
    added_by      = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="SET NULL"))
    is_approved   = Column(Boolean, default=True)        # admin approval flag
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
