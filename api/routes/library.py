"""
Library routes – BTU Digital Library.

The library is a full knowledge hub that combines:
  1. Agentic RAG across all 30 curriculum chapters
  2. External resources: research papers, videos, articles, case studies, books

Endpoints:
  POST /library/search       – search the library (RAG + external resources)
  GET  /library/topics       – browsable topic areas (professor domains)
  GET  /library/resources    – browse/filter external resources
  POST /library/resources    – add a new external resource
  GET  /library/resources/{id} – get a single resource by ID
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.middleware.auth import require_auth
from api.schemas.library import (
    AddResourceRequest,
    LibrarySearchRequest,
    LibrarySearchResponse,
    LibraryTopicsResponse,
    ResourceResponse,
)
from agents.engine import PipelineEngine
from memory.store import MemoryStore

router = APIRouter(prefix="/library", tags=["library"])


def _get_engine() -> PipelineEngine:
    from api.app import get_pipeline_engine
    return get_pipeline_engine()


def _get_store() -> MemoryStore:
    from api.app import get_memory_store
    return get_memory_store()


def _resource_to_response(r) -> ResourceResponse:
    return ResourceResponse(
        resource_id=str(r.resource_id),
        title=r.title,
        resource_type=r.resource_type,
        url=r.url,
        description=r.description,
        author=r.author,
        chapters=[int(c) for c in r.chapters.split(",") if c.strip()] if r.chapters else None,
        professor_id=r.professor_id,
        tags=r.tags.split(",") if r.tags else None,
        added_by=str(r.added_by) if r.added_by else None,
        created_at=str(r.created_at),
    )


# ── Search (RAG + external resources) ────────────────────────────────────────

@router.post("/search", response_model=LibrarySearchResponse)
async def library_search(
    req: LibrarySearchRequest,
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
    store: MemoryStore = Depends(_get_store),
) -> LibrarySearchResponse:
    """
    Search the BTU Digital Library.

    Combines Agentic RAG (multi-round, LLM-guided) across all 30 chapters
    with matching external resources (papers, videos, articles, case studies).
    """
    try:
        result = await engine.library_search(student_id, req.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Also search external resources by keyword
    ext_resources = await store.list_library_resources(search=req.query, limit=5)
    ext_dicts = [_resource_to_response(r).model_dump() for r in ext_resources]

    return LibrarySearchResponse(
        answer=result.answer,
        resources=[r.model_dump() for r in result.resources],
        chapters_searched=result.chapters_searched,
        rag_rounds_used=result.rag_rounds_used,
        retrieval_trace=result.retrieval_trace,
        external_resources=ext_dicts,
        latency_ms=result.latency_ms,
    )


# ── Browse topics ────────────────────────────────────────────────────────────

@router.get("/topics", response_model=LibraryTopicsResponse)
async def library_topics(
    student_id: str = Depends(require_auth),
) -> LibraryTopicsResponse:
    """
    List all topic areas in the BTU Library (one per professor / P-domain).
    Students can use these as search entry points.
    """
    from config.agent_config import PROFESSOR_META, PROFESSOR_CHAPTERS
    topics = [
        {
            "professor_id": pid,
            "professor_name": meta["name"],
            "domain": meta["domain"],
            "chapters": PROFESSOR_CHAPTERS.get(pid, []),
            "active": meta.get("active", False),
        }
        for pid, meta in PROFESSOR_META.items()
    ]
    return LibraryTopicsResponse(topics=topics)


# ── Browse external resources ────────────────────────────────────────────────

@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(
    resource_type: Optional[str] = Query(None, pattern="^(paper|video|article|case_study|book)$"),
    chapter: Optional[int] = Query(None, ge=1, le=30),
    professor_id: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None, max_length=200),
    limit: int = Query(50, ge=1, le=200),
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> list[ResourceResponse]:
    """
    Browse external library resources with optional filters.

    Filter by type (paper/video/article/case_study/book), chapter, professor module,
    tag, or free-text search across title/description/tags.
    """
    resources = await store.list_library_resources(
        resource_type=resource_type,
        chapter=chapter,
        professor_id=professor_id,
        tag=tag,
        search=search,
        limit=limit,
    )
    return [_resource_to_response(r) for r in resources]


# ── Add a resource ───────────────────────────────────────────────────────────

@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def add_resource(
    req: AddResourceRequest,
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> ResourceResponse:
    """
    Add an external resource to the BTU Library.

    Students can contribute papers, videos, articles, case studies, or books.
    Resources are linked to chapters and professor modules for discoverability.
    """
    from config.agent_config import CHAPTER_TO_PROFESSOR
    professor_id = req.professor_id
    if not professor_id and req.chapters:
        professor_id = CHAPTER_TO_PROFESSOR.get(req.chapters[0])

    resource = await store.add_library_resource(
        title=req.title,
        resource_type=req.resource_type,
        url=req.url,
        description=req.description,
        author=req.author,
        chapters=req.chapters,
        professor_id=professor_id,
        tags=req.tags,
        added_by=student_id,
    )
    return _resource_to_response(resource)


# ── Get single resource ──────────────────────────────────────────────────────

@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    student_id: str = Depends(require_auth),
    store: MemoryStore = Depends(_get_store),
) -> ResourceResponse:
    """Get a single library resource by ID."""
    resource = await store.get_library_resource(resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _resource_to_response(resource)
