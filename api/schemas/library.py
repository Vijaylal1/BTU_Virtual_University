"""Library endpoint request/response schemas."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class LibrarySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="What the student is searching for")
    chapters: Optional[list[int]] = Field(
        None,
        description="Optional: restrict search to specific chapters (1-30). Default: all chapters.",
    )


class LibrarySearchResponse(BaseModel):
    answer: str
    resources: list[dict]         # list of LibrarySearchResult dicts
    chapters_searched: list[int]
    rag_rounds_used: int
    retrieval_trace: list[dict]   # shows how the agent navigated retrieval
    external_resources: list[dict] = Field(default_factory=list)  # matching papers/videos/articles
    latency_ms: int


class LibraryTopicsResponse(BaseModel):
    topics: list[dict]            # professor domains the library covers


# ── Library Resource schemas ─────────────────────────────────────────────────

class AddResourceRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=300)
    resource_type: str = Field(..., pattern="^(paper|video|article|case_study|book)$")
    url: Optional[str] = Field(None, max_length=2000)
    description: Optional[str] = Field(None, max_length=2000)
    author: Optional[str] = Field(None, max_length=200)
    chapters: Optional[list[int]] = Field(None, description="Related chapter numbers (1-30)")
    professor_id: Optional[str] = None
    tags: Optional[list[str]] = Field(None, description="Tags for categorisation")


class ResourceResponse(BaseModel):
    resource_id: str
    title: str
    resource_type: str
    url: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    chapters: Optional[list[int]] = None
    professor_id: Optional[str] = None
    tags: Optional[list[str]] = None
    added_by: Optional[str] = None
    created_at: str
