"""
Chat routes:
  POST /chat          – standard request/response
  GET  /chat/stream   – SSE streaming response
  POST /chat/upload   – file upload (pass file text to pipeline)
"""

from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from api.middleware.auth import require_auth
from api.schemas.chat import ChatRequest, ChatResponse, UploadResponse
from agents.engine import PipelineEngine

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_engine() -> PipelineEngine:
    from api.app import get_pipeline_engine
    return get_pipeline_engine()


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
) -> ChatResponse:
    try:
        result = await engine.chat(student_id, req.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return ChatResponse(
        text=result.text,
        source_agent=result.source_agent,
        latency_ms=result.latency_ms,
        rag_chunks_used=result.rag_chunks_used,
        ceremony=result.ceremony.model_dump() if result.ceremony else None,
        sprint_status=result.sprint_status,
        wheel_prize=result.wheel_prize.model_dump() if result.wheel_prize else None,
    )


@router.get("/stream")
async def chat_stream(
    message: str,
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
) -> StreamingResponse:
    async def _sse_generator() -> AsyncIterator[str]:
        async for chunk in engine.stream_chat(student_id, message):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_sse_generator(), media_type="text/event-stream")


@router.post("/upload", response_model=UploadResponse)
async def upload_and_chat(
    file: UploadFile = File(...),
    student_id: str = Depends(require_auth),
    engine: PipelineEngine = Depends(_get_engine),
) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    content = await file.read()
    text = content.decode("utf-8", errors="replace")[:8000]  # truncate at 8k chars
    message = f"[Student uploaded file: {file.filename}]\n\n{text}"
    await engine.chat(student_id, message)
    return UploadResponse(filename=file.filename, message="File processed successfully")
