"""
Doubt Clearing Session routes.

Students can request a focused doubt-clearing session with the professor
responsible for a given chapter or topic. The professor responds in a
Socratic teaching style: thorough explanation + follow-up questions to
guide the student to deeper understanding.

Endpoints:
  POST /doubt           – start a doubt-clearing session (auto-detects professor)
  POST /doubt/professor – target a specific professor directly
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.middleware.auth import require_auth
from api.schemas.doubt import DoubtRequest, DoubtResponse, ProfessorDoubtRequest
from agents.engine import PipelineEngine

router = APIRouter(prefix="/doubt", tags=["doubt"])


def _get_engine() -> PipelineEngine:
    from api.app import get_pipeline_engine
    return get_pipeline_engine()


@router.post("", response_model=DoubtResponse)
async def clear_doubt(
    req: DoubtRequest,
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
) -> DoubtResponse:
    """
    Submit a doubt for clearing.

    The system auto-detects the responsible professor based on `chapter_hint`
    or the doubt question itself (falls back to Prof. Priya Place).
    The professor responds with:
      - A step-by-step explanation
      - 1-2 follow-up questions (Socratic style)
      - Suggested chapters for further study
    """
    try:
        result = await engine.doubt_chat(
            student_id=student_id,
            doubt_question=req.doubt_question,
            chapter_hint=req.chapter_hint,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return DoubtResponse(
        explanation=result.explanation,
        follow_up_questions=result.follow_up_questions,
        suggested_chapters=result.suggested_chapters,
        professor_id=result.professor_id,
        rag_chunks_used=result.rag_chunks_used,
        latency_ms=result.latency_ms,
    )


@router.post("/professor", response_model=DoubtResponse)
async def clear_doubt_with_professor(
    req: ProfessorDoubtRequest,
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
) -> DoubtResponse:
    """
    Submit a doubt to a specific professor by ID.

    Use this when the student knows which professor they want to consult
    (e.g. "I want to ask Prof. Marcus Pricing about contribution margins").
    """
    from config.agent_config import PROFESSOR_META
    if req.professor_id not in PROFESSOR_META:
        raise HTTPException(status_code=400, detail=f"Unknown professor_id: {req.professor_id}")

    try:
        result = await engine.doubt_chat(
            student_id=student_id,
            doubt_question=req.doubt_question,
            professor_id=req.professor_id,
            chapter_hint=req.chapter_hint,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return DoubtResponse(
        explanation=result.explanation,
        follow_up_questions=result.follow_up_questions,
        suggested_chapters=result.suggested_chapters,
        professor_id=result.professor_id,
        rag_chunks_used=result.rag_chunks_used,
        latency_ms=result.latency_ms,
    )
