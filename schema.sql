-- ══════════════════════════════════════════════════════════════════════════════
-- BTU Virtual University – PostgreSQL Schema  (Database: BTU_VU)
-- ══════════════════════════════════════════════════════════════════════════════
--
-- SETUP (run once):
--
--   1. Open pgAdmin → create a database named  BTU_VU
--   2. Open Query Tool, paste this file and click Run (▶)
--
-- Or via psql terminal:
--   psql -U postgres -d BTU_VU -f schema.sql
-- ══════════════════════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── 1. Students ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    student_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email        TEXT UNIQUE NOT NULL,
    full_name    TEXT NOT NULL,
    hashed_pw    TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    onboarded    BOOLEAN DEFAULT FALSE,
    graduated    BOOLEAN DEFAULT FALSE
);

-- ── 2. Sessions (one per student-device) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    last_active  TIMESTAMPTZ DEFAULT NOW()
);

-- ── 3. Chat Messages ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    message_id   BIGSERIAL PRIMARY KEY,
    session_id   UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    student_id   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    role         TEXT NOT NULL CHECK (role IN ('user','assistant')),
    content      TEXT NOT NULL,
    source_agent TEXT,
    thinking     TEXT,
    latency_ms   INT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── 4. Cross-Agent Summaries (upward summarisation every 5 msgs) ────────────
CREATE TABLE IF NOT EXISTS cross_agent_summaries (
    summary_id   BIGSERIAL PRIMARY KEY,
    student_id   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    professor_id TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    msg_count    INT NOT NULL DEFAULT 5,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── 5. Sprint Tracking (15 hr / week target) ───────────────────────────────
CREATE TABLE IF NOT EXISTS sprints (
    sprint_id    BIGSERIAL PRIMARY KEY,
    student_id   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    week_number  INT NOT NULL,
    hours_logged FLOAT NOT NULL DEFAULT 0.0,
    target_hours FLOAT NOT NULL DEFAULT 15.0,
    started_at   TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','completed','missed')),
    UNIQUE(student_id, week_number)
);

-- ── 6. Wheel of Fortune Spins ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wheel_spins (
    spin_id      BIGSERIAL PRIMARY KEY,
    student_id   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    prize        TEXT NOT NULL,
    prize_type   TEXT NOT NULL,
    spun_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 7. Ceremonies / Milestones ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ceremonies (
    ceremony_id  BIGSERIAL PRIMARY KEY,
    student_id   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    milestone    TEXT NOT NULL,
    script       TEXT NOT NULL,
    triggered_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── 8. Chapter Progress ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chapter_progress (
    progress_id     BIGSERIAL PRIMARY KEY,
    student_id      UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    chapter_number  INT NOT NULL CHECK (chapter_number BETWEEN 1 AND 30),
    status          TEXT NOT NULL DEFAULT 'locked' CHECK (status IN ('locked','in_progress','completed')),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    UNIQUE(student_id, chapter_number)
);

-- ── 9. Library Sessions (search log with retrieval metadata) ────────────────
CREATE TABLE IF NOT EXISTS library_sessions (
    session_id      BIGSERIAL PRIMARY KEY,
    student_id      UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    query           TEXT NOT NULL,
    answer          TEXT NOT NULL,
    chapters_hit    INT[] NOT NULL DEFAULT '{}',
    rag_rounds      INT NOT NULL DEFAULT 1,
    latency_ms      INT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── 10. Doubt Clearing Sessions ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doubt_sessions (
    doubt_id             BIGSERIAL PRIMARY KEY,
    student_id           UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    professor_id         TEXT NOT NULL,
    doubt_question       TEXT NOT NULL,
    explanation          TEXT NOT NULL,
    follow_up_questions  JSONB NOT NULL DEFAULT '[]',
    suggested_chapters   INT[] NOT NULL DEFAULT '{}',
    rag_chunks_used      INT NOT NULL DEFAULT 0,
    chapter_hint         INT,
    latency_ms           INT,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ── 11. Discussion Rooms ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS discussion_rooms (
    room_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT NOT NULL,
    room_type    TEXT NOT NULL CHECK (room_type IN ('campus','library')),
    chapter_hint INT,
    professor_id TEXT,
    topic        TEXT,
    created_by   UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    is_active    BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── 12. Discussion Members ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS discussion_members (
    member_id   BIGSERIAL PRIMARY KEY,
    room_id     UUID NOT NULL REFERENCES discussion_rooms(room_id) ON DELETE CASCADE,
    student_id  UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    joined_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(room_id, student_id)
);

-- ── 13. Discussion Messages ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS discussion_messages (
    msg_id      BIGSERIAL PRIMARY KEY,
    room_id     UUID NOT NULL REFERENCES discussion_rooms(room_id) ON DELETE CASCADE,
    student_id  UUID REFERENCES students(student_id) ON DELETE SET NULL,
    content     TEXT NOT NULL,
    is_ai       BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── 14. Library Resources (external papers, videos, articles) ───────────────
CREATE TABLE IF NOT EXISTS library_resources (
    resource_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title         TEXT NOT NULL,
    resource_type TEXT NOT NULL CHECK (resource_type IN ('paper','video','article','case_study','book')),
    url           TEXT,
    description   TEXT,
    author        TEXT,
    chapters      TEXT,              -- comma-separated chapter numbers e.g. "1,2,5"
    professor_id  TEXT,
    tags          TEXT,              -- comma-separated tags e.g. "marketing,strategy"
    added_by      UUID REFERENCES students(student_id) ON DELETE SET NULL,
    is_approved   BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ══════════════════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_messages_student
    ON messages(student_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_summaries_student_prof
    ON cross_agent_summaries(student_id, professor_id);

CREATE INDEX IF NOT EXISTS idx_sprints_student
    ON sprints(student_id, week_number);

CREATE INDEX IF NOT EXISTS idx_chapter_progress_student
    ON chapter_progress(student_id, chapter_number);

CREATE INDEX IF NOT EXISTS idx_library_sessions_student
    ON library_sessions(student_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_doubt_sessions_student
    ON doubt_sessions(student_id, professor_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_discussion_rooms_type
    ON discussion_rooms(room_type, is_active);

CREATE INDEX IF NOT EXISTS idx_discussion_messages_room
    ON discussion_messages(room_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_library_resources_type
    ON library_resources(resource_type, is_approved);
