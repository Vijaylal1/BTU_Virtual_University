# 🎓 BTU Virtual University – Multi-Agentic AI Framework

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_Opus_4.6-Anthropic-6B4FBB?style=for-the-badge&logo=anthropic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Local-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Store-FF6B35?style=for-the-badge&logo=meta&logoColor=white)

**A 3-tier agentic AI backend** for a virtual business university — 10 specialist AI professors,
Agentic RAG, Digital Library, Socratic doubt-clearing, group discussions, and gamification —
all orchestrated by Dean Morgan.

[Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Architecture](#-architecture-overview) · [Troubleshooting](#-troubleshooting)

</div>

---

## 📐 Architecture Overview

```
Student logs in → JWT token → sends message
      │
      ▼
┌───────────────────────────────────────────────────┐
│  TIER 1 – Dean Morgan (Orchestrator)              │
│  • Intent classification via Haiku                │
│  • Personalised greeting (first msg / welcome back)│
│  • Ceremony triggers (onboarding / graduation)    │
│  • Diagnostic note for downstream agents          │
│  • Quality gate on outgoing responses             │
└───────────────────┬───────────────────────────────┘
                    │ HandoffPacket1 (+ greeting)
                    ▼
┌───────────────────────────────────────────────────┐
│  TIER 2 – Elias Vance (Coach / Bridge)            │
│  • Handles: nav, sprint, wheel, motivation        │
│  • Library scenario (cross-chapter RAG)           │
│  • AI Moderator for group discussions             │
│  • Routes domain/doubt queries to professors      │
│  • Agentic RAG pre-retrieval (30 chapters)        │
└───────────────────┬───────────────────────────────┘
                    │ HandoffPacket2
                    ▼
┌───────────────────────────────────────────────────┐
│  TIER 3 – 10 Specialist Professors                │
│  The 10 P's of Business (3 chapters each)         │
│                                                   │
│  P1  Prof. Priya Place        Ch. 1-3   ✅        │
│  P2  Prof. Maya People        Ch. 4-6   🔒        │
│  P3  Prof. Sam Process        Ch. 7-9   🔒        │
│  P4  Prof. Pablo Positioning  Ch. 10-12 🔒        │
│  P5  Prof. Leila Performance  Ch. 13-15 🔒        │
│  P6  Prof. Dana Platform      Ch. 16-18 🔒        │
│  P7  Prof. Marcus Pricing     Ch. 19-21 🔒        │
│  P8  Prof. Iris Purpose       Ch. 22-24 🔒        │
│  P9  Prof. Lucas Policy       Ch. 25-27 🔒        │
│  P10 Prof. Petra Profit       Ch. 28-30 🔒        │
│                                                   │
│  ✅ POC Active   🔒 Dormant (future sprint)        │
└───────────────────────────────────────────────────┘
                    │
                    ▼
             AgentResponse
   (greeting + text + thinking + latency + rag_chunks)
```

### Alternative Flows (Bypass Tiers)

| Flow | Path | Description |
|:-----|:-----|:------------|
| **Library Search** | Student → Engine → Agentic RAG (all 30 ch.) → Coach synthesis | Cross-chapter exploration |
| **Doubt Clearing** | Student → Engine → Professor (direct) | Socratic 1-on-1, bypasses Dean & Coach |
| **Group Discussion** | Student → Room → Coach Elias (AI moderator) | Campus or Library discussions with peers |

---

## 🛠 Tech Stack

| Component | Technology | Notes |
|:----------|:-----------|:------|
| **LLM** | `claude-opus-4-6` | Professors + extended thinking |
| **Fast LLM** | `claude-haiku-4-5` | Routing, RAG planning, summaries, greetings |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Free, local, 384-dim vectors |
| **Vector Store** | `FAISS` (faiss-cpu) | Local file-based, no server needed |
| **Database** | Local PostgreSQL + SQLAlchemy async | Managed via pgAdmin |
| **Framework** | FastAPI | Async API with JWT auth |
| **Dashboard** | Vanilla HTML/CSS/JS | Served from `/static/index.html` |

---

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 14+ | Local database (install via pgAdmin or postgres installer) |
| Anthropic API key | — | Claude Opus + Haiku |

> **Note:** FAISS and sentence-transformers run locally — no external vector DB or embedding API needed.

### 1. Clone & install dependencies

```bash
cd btu-virtual-university
python -m venv vijaylal
vijaylal\Scripts\activate          # Windows
# source vijaylal/bin/activate     # macOS / Linux
pip install -r requirements.txt

# Fix bcrypt compatibility with passlib
pip install "bcrypt==4.0.1"
```

### 2. Configure environment

```env
# .env  (fill in your real values)

# Required
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_REAL_KEY

# Local PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/BTU_VU

# JWT secret (change in production)
JWT_SECRET=a-long-random-string-at-least-32-characters
```

### 3. Set up local PostgreSQL

1. Install PostgreSQL + pgAdmin from [postgresql.org](https://www.postgresql.org/download/)
2. Open **pgAdmin** → create a new database named `BTU_VU`
3. Open **Query Tool** on `BTU_VU` → paste contents of `schema.sql` → click **Run**
4. Update `DATABASE_URL` in `.env` with your postgres password

> Tables are also auto-created on startup via `init_db()` — running `schema.sql` adds extra constraints and indexes.

### 4. Ingest chapter content

```bash
python -m rag.ingest --source data/chapters/
```

Place chapter `.md` or `.txt` files in `data/chapters/` before running. Vectors are saved to `.faiss_store/`.

### 5. Run the server

```bash
python main.py
```

- **Dashboard** → http://localhost:8080
- **API Docs** → http://localhost:8080/docs
- **Health** → http://localhost:8080/health

---

## 🖥 Dashboard

Built-in web dashboard at **http://localhost:8080**:

| Panel | Description |
|:------|:------------|
| **Dashboard** | Welcome banner with your name, system stats, all 10 professors with live/dormant status |
| **Chat** | 3-tier pipeline chat with clickable starter prompt cards |
| **Library** | Agentic RAG search across 30 chapters with suggestion chips |
| **Doubt Clearing** | Direct Socratic session with a professor; example doubt chips pre-fill the form |

**First-time setup:**
1. Go to http://localhost:8080
2. Click **"Create one"** → fill in Name, Email, Password → **Create Account →**
3. You are logged in. Click a starter card in Chat to begin.

---

## 🔄 How the Code Works — End-to-End

### Step 1 — FastAPI Receives the Request

```python
# api/routes/chat.py
@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
):
    response = await engine.chat(student_id, body.message)
    return ChatResponse(text=response.text, source_agent=response.source_agent, ...)
```

### Step 2 — PipelineEngine Orchestrates the 3-Tier Chain

```python
# agents/engine.py
async def chat(self, student_id: str, message: str) -> AgentResponse:
    await self.memory.save_message(student_id, role="user", content=message)
    tier1 = await self.dean.orchestrate(student_id, message)
    tier2 = await self.coach.bridge(tier1)
    professor = self.registry.get_professor(tier2.professor_id)
    prof_resp = await professor.respond(tier2)
    response = AgentResponse(
        text=self._prepend_greeting(tier1.greeting, prof_resp.response_text), ...
    )
    return await self.dean.quality_gate(response, tier1.student_context)
```

### Step 3 — Session Auto-Creation (Sprint 2 Fix)

```python
# memory/store.py
async def get_or_create_session(self, student_id: str) -> uuid.UUID:
    """Return the most recent session, creating one if needed (satisfies FK constraint)."""
    ...

async def save_message(self, student_id, role, content, ...):
    sid = uuid.UUID(session_id) if session_id else await self.get_or_create_session(student_id)
    ...
```

### Step 4 — Upward Summarisation

Every 5 messages, Haiku condenses the conversation into 2-3 sentences stored in `cross_agent_summaries` and injected into future professor briefings as long-term memory.

---

## 🧠 Agentic RAG Pipeline

```
Student Query
      │
      ▼  PLAN: Haiku decomposes into 2-3 sub-queries
      │
      ▼  RETRIEVE: Embed + search FAISS (chapter-scoped or full library)
      │
      ▼  EVALUATE: Haiku checks sufficiency
         YES → done  |  NO → generate follow-ups (up to 3 rounds)
      │
      ▼  Deduplicated, re-ranked chunks + full retrieval trace
```

```python
# Drop-in compatible
chunks = await rag.retrieve(query, chapters=[1, 2, 3])

# Full agentic mode
result = await rag.agentic_retrieve(query="How does footfall analysis work?", chapters=[1, 2, 3])
result.chunks         # list[RagChunk] ranked by score
result.rounds_used    # 1, 2, or 3
result.trace          # per-round query + evaluation details
```

---

## 📋 API Reference

All endpoints except `/health` require `Authorization: Bearer <token>`.

### Auth
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/auth/register` | Register → access_token |
| `POST` | `/auth/login` | Login → access_token |
| `GET` | `/auth/me` | Current student profile |

### Chat
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/chat` | Standard 3-tier chat |
| `GET` | `/chat/stream` | SSE streaming chat |
| `POST` | `/chat/upload` | Upload file for analysis |

### Library
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/library/search` | Agentic RAG search across 30 chapters |
| `GET` | `/library/topics` | Browse professor domain topics |
| `GET` | `/library/resources` | Browse external resources |
| `POST` | `/library/resources` | Add an external resource |
| `GET` | `/library/resources/{id}` | Get a single resource |

### Doubt
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/doubt` | Auto-detect professor via chapter_hint |
| `POST` | `/doubt/professor` | Target a specific professor by ID |

### Discussion
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `POST` | `/discuss/create` | Create a campus or library room |
| `GET` | `/discuss/rooms` | List rooms |
| `POST` | `/discuss/{id}/join` | Join a room |
| `POST` | `/discuss/{id}/msg` | Post a message |
| `GET` | `/discuss/{id}/msgs` | Get messages |
| `POST` | `/discuss/{id}/ai` | Ask Coach Elias to moderate |

### Gamification
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/sprint/{id}` | Sprint status |
| `POST` | `/sprint/{id}/log` | Log study hours |
| `POST` | `/wheel/{id}/spin` | Spin wheel (requires 100% sprint) |
| `GET` | `/wheel/prizes` | List all prizes |

### Admin
| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/agents` | List all professors |
| `GET` | `/agents/chapter-map` | Chapter → professor mapping |
| `POST` | `/ingest/chapters` | Trigger chapter ingestion |
| `GET` | `/health` | Health check (no auth) |

---

## 📁 Project Structure

```
btu-virtual-university/
├── main.py                    # Entry point: uvicorn + auto-open browser
├── requirements.txt
├── schema.sql                 # Full DDL (14 tables + indexes)
├── .env                       # API keys, DB URL, JWT secret
├── config/
│   ├── settings.py            # Pydantic Settings
│   └── agent_config.py        # Professor metadata + chapter map
├── agents/
│   ├── dean.py                # Tier-1 orchestrator
│   ├── coach.py               # Tier-2 bridge
│   ├── engine.py              # Pipeline entry point
│   ├── registry.py            # Professor lookup
│   ├── handoff.py             # Pydantic contracts
│   ├── router.py              # Intent classifier (Haiku)
│   ├── prompts/               # System prompts
│   └── professors/
│       ├── base_professor.py  # respond() + stream_respond() + clear_doubt()
│       ├── place.py           # ✅ Prof. Priya Place (Ch. 1-3)
│       └── ... (9 dormant stubs)
├── rag/
│   ├── agentic_pipeline.py    # Multi-round Agentic RAG
│   ├── embedder.py            # sentence-transformers
│   ├── vectordb.py            # FAISS adapter
│   └── ingest.py              # Chapter ingestion CLI
├── memory/
│   ├── models.py              # SQLAlchemy ORM (14 tables)
│   ├── store.py               # PostgreSQL async CRUD
│   └── summariser.py          # Haiku upward summarisation
├── api/
│   ├── app.py                 # FastAPI factory
│   ├── middleware/auth.py     # JWT middleware
│   ├── routes/                # Route modules
│   └── schemas/               # Pydantic schemas
├── static/
│   └── index.html             # Built-in web dashboard
├── data/chapters/             # Chapter files for RAG ingestion
├── .faiss_store/              # FAISS index (auto-created)
└── docs/
    └── generate_guide.py      # PDF guide generator (reportlab)
```

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|:---------|:--------|:------------|
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key |
| `CLAUDE_MODEL` | `claude-opus-4-6` | Main model (professors + thinking) |
| `HAIKU_MODEL` | `claude-haiku-4-5` | Fast ops (routing, RAG, summaries) |
| `THINKING_BUDGET` | `8000` | Extended thinking token budget |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Free local embeddings |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:pw@localhost:5432/BTU_VU` | Local PostgreSQL URL |
| `FAISS_PERSIST_DIR` | `.faiss_store` | FAISS index directory |
| `JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `JWT_EXPIRE_MINUTES` | `1440` | Token expiry (24 hours) |
| `RAG_CHUNK_SIZE` | `512` | Words per RAG chunk |
| `RAG_CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `RAG_TOP_K` | `5` | Max RAG results per query |
| `RAG_THRESHOLD` | `0.30` | Min cosine similarity |
| `SPRINT_TARGET_HOURS` | `15.0` | Weekly sprint target |
| `SUMMARISE_EVERY_N` | `5` | Messages between summaries |

---

## 🔓 Activating a Dormant Professor

1. Open `config/agent_config.py` → set `"active": True` for the target professor
2. Add chapter `.md` files to `data/chapters/` (e.g. `chapter_04.md` to `chapter_06.md`)
3. Run: `python -m rag.ingest --source data/chapters/`
4. Restart: `python main.py`

No code changes needed — the registry routes automatically.

---

## 🗄 Database Schema (14 Tables)

| Table | Purpose |
|:------|:--------|
| `students` | Accounts (email, name, onboarded, graduated) |
| `sessions` | Chat sessions (auto-created per student on first message) |
| `messages` | Full chat history with source_agent + thinking |
| `cross_agent_summaries` | Upward summaries every 5 messages |
| `sprints` | 15-hr/week sprint tracking |
| `wheel_spins` | Wheel of Fortune prize history |
| `ceremonies` | Onboarding / graduation scripts |
| `chapter_progress` | Per-chapter status |
| `library_sessions` | Library search logs |
| `doubt_sessions` | Doubt clearing logs |
| `discussion_rooms` | Group discussion rooms |
| `discussion_members` | Room membership |
| `discussion_messages` | Room messages (student + AI) |
| `library_resources` | External resource catalog |

---

## 🐛 Troubleshooting

| Symptom | Fix |
|:--------|:----|
| `ModuleNotFoundError` | Activate venv: `vijaylal\Scripts\activate` |
| `database_init_failed getaddrinfo failed` | Check `DATABASE_URL` in `.env` — use `localhost` for local PostgreSQL |
| `ForeignKeyViolationError` on messages | Fixed in `memory/store.py` via `get_or_create_session()` |
| `error reading bcrypt version` | Run `pip install "bcrypt==4.0.1"` |
| `401 Unauthorized` on `/chat` | Use dashboard (token handled automatically) or click Authorize in `/docs` |
| `500 Internal Server Error` | Check terminal traceback — most common: DB not connected or RAG index empty |
| No RAG results | Run `python -m rag.ingest --source data/chapters/` |
| `faiss_initialized_empty` | Normal until ingestion is run |
| Slow first startup | sentence-transformers downloads ~80MB model on first run; cached after |
| `UnicodeEncodeError` on Windows | Fixed in `main.py` — UTF-8 stdout auto-configured |
| `Directory 'static' does not exist` | Ensure `static/index.html` exists |

---

<div align="center">

**Built with** ❤️ **by the BTU Engineering Team**

FastAPI · Anthropic Claude · sentence-transformers · FAISS · PostgreSQL

</div>
