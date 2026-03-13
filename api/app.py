"""
FastAPI application factory.
All dependencies (MemoryStore, AgenticRAGPipeline, PipelineEngine) are created at startup
and exposed via module-level getters for use in route dependencies.
"""

from __future__ import annotations

import os
import structlog
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Resolve static directory from project root (not CWD)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_STATIC_DIR = _PROJECT_ROOT / "static"

from agents.dean import DeanAgent
from agents.coach import CoachAgent
from agents.engine import PipelineEngine
from agents.registry import AgentRegistry
from config.settings import get_settings
from gamification.sprint_engine import SprintEngine
from gamification.wheel_of_fortune import WheelOfFortune
from memory.store import MemoryStore
from memory.summariser import Summariser
from rag.agentic_pipeline import AgenticRAGPipeline

logger = structlog.get_logger(__name__)
settings = get_settings()

# ── Module-level singletons ───────────────────────────────────────────────────
_memory:   MemoryStore        | None = None
_rag:      AgenticRAGPipeline | None = None
_engine:   PipelineEngine     | None = None
_registry: AgentRegistry      | None = None
_sprint:   SprintEngine       | None = None
_wheel:    WheelOfFortune     | None = None


def get_memory_store()   -> MemoryStore:    assert _memory;   return _memory
def get_pipeline_engine()-> PipelineEngine: assert _engine;   return _engine
def get_registry()       -> AgentRegistry:  assert _registry; return _registry
def get_sprint_engine()  -> SprintEngine:   assert _sprint;   return _sprint
def get_wheel()          -> WheelOfFortune: assert _wheel;    return _wheel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global _memory, _rag, _engine, _registry, _sprint, _wheel

    logger.info("btu_api_starting")

    # Initialise memory (PostgreSQL)
    _memory = MemoryStore()
    try:
        await _memory.init_db()
        logger.info("database_connected")
    except Exception as exc:
        logger.warning("database_init_failed", reason=str(exc),
                       hint="Start PostgreSQL or check DATABASE_URL in .env")

    # Initialise Agentic RAG (FAISS + sentence-transformers)
    _rag = AgenticRAGPipeline()
    try:
        await _rag.init()
        logger.info("rag_connected")
    except Exception as exc:
        logger.warning("rag_init_skipped", reason=str(exc))

    # Gamification
    _sprint = SprintEngine(_memory)
    _wheel  = WheelOfFortune(_memory)

    # Agent registry
    _registry = AgentRegistry(_memory, _rag)

    # Pipeline engine
    summariser = Summariser(_memory)
    dean  = DeanAgent(_memory)
    coach = CoachAgent(_memory, _rag, _sprint, _wheel)
    _engine = PipelineEngine(_memory, dean, coach, _registry, summariser, _rag)

    logger.info("btu_api_ready")
    yield

    # Shutdown
    logger.info("btu_api_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="BTU Virtual University API",
        description="Multi-Agentic AI Framework – 3-Tier Architecture",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    from api.routes.health   import router as health_router
    from api.routes.auth     import router as auth_router
    from api.routes.chat     import router as chat_router
    from api.routes.sprint   import router as sprint_router
    from api.routes.wheel    import router as wheel_router
    from api.routes.agents   import router as agents_router
    from api.routes.ingest   import router as ingest_router
    from api.routes.library  import router as library_router
    from api.routes.doubt    import router as doubt_router
    from api.routes.discuss  import router as discuss_router

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(sprint_router)
    app.include_router(wheel_router)
    app.include_router(agents_router)
    app.include_router(ingest_router)
    app.include_router(library_router)
    app.include_router(doubt_router)
    app.include_router(discuss_router)

    # Serve the frontend dashboard — route BEFORE static mount
    @app.get("/", include_in_schema=False)
    async def frontend():
        html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(
            content=html,
            headers={"Cache-Control": "public, max-age=3600"},
        )

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    return app


# Single app instance used by uvicorn
app = create_app()
