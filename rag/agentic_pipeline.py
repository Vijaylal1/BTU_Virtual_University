"""
Agentic RAG Pipeline – LLM-guided, multi-round iterative retrieval.

Unlike the passive RAGPipeline (single embed → retrieve), this pipeline
uses a Haiku agent to actively drive retrieval:

  Round 1: Haiku decomposes the query into 2-3 focused sub-queries
  Round N: Retrieve chunks for each sub-query, then Haiku evaluates
           whether the context is sufficient to answer the original question.
           If not, Haiku generates follow-up queries and repeats.
  Final:   Deduplicated, re-ranked chunks + retrieval trace are returned.

The class exposes a drop-in `retrieve()` method (same signature as
RAGPipeline.retrieve) so it can replace it anywhere transparently.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import anthropic
import structlog

from config.settings import get_settings
from rag.embedder import FallbackEmbedder, SentenceTransformerEmbedder, get_embedder
from rag.pipeline import RagChunk
from rag.vectordb import QueryResult, VectorDB

logger = structlog.get_logger(__name__)
settings = get_settings()


# ── Haiku prompts ─────────────────────────────────────────────────────────────

_PLANNER_SYSTEM = """
You are a retrieval planning assistant for BTU Virtual University.
Given a student's question, decompose it into 2-3 concise sub-queries that together
cover all aspects needed to answer the question.
Respond ONLY with valid JSON:
{"sub_queries": ["query1", "query2", "query3"]}
""".strip()

_EVALUATOR_SYSTEM = """
You are a retrieval quality evaluator for BTU Virtual University.
Given a student question and a list of retrieved curriculum snippets, decide
whether the retrieved context is sufficient to answer the question well.
If not, provide 1-2 targeted follow-up search queries for what is still missing.
Respond ONLY with valid JSON:
{"is_sufficient": true, "reason": "brief explanation", "follow_up_queries": []}
""".strip()


# ── Result container ──────────────────────────────────────────────────────────

@dataclass
class AgenticRagResult:
    chunks: list[RagChunk]
    sub_queries: list[str]
    rounds_used: int
    sufficient: bool
    trace: list[dict] = field(default_factory=list)


# ── Pipeline ──────────────────────────────────────────────────────────────────

class AgenticRAGPipeline:
    """
    Drop-in replacement for RAGPipeline with Agentic multi-round retrieval.

    Usage (same as RAGPipeline):
        chunks = await agentic_rag.retrieve(query, chapters=[1, 2, 3])

    Full agentic mode:
        result = await agentic_rag.agentic_retrieve(query, chapters=[1, 2, 3])
        # result.trace shows query decomposition + evaluation rounds
    """

    def __init__(self) -> None:
        self._embedder: SentenceTransformerEmbedder | FallbackEmbedder | None = None
        self.vectordb = VectorDB()
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    @property
    def embedder(self) -> SentenceTransformerEmbedder | FallbackEmbedder:
        """Lazy-load the embedding model on first use, not at startup."""
        if self._embedder is None:
            self._embedder = get_embedder()
        return self._embedder

    async def init(self) -> None:
        await self.vectordb.init()
        logger.info("agentic_rag_pipeline_ready")

    # ── Backward-compatible interface ─────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        chapters: list[int],
        top_k: int | None = None,
        threshold: float | None = None,
    ) -> list[RagChunk]:
        """Same signature as RAGPipeline.retrieve; used by professors."""
        result = await self.agentic_retrieve(
            query, chapters, top_k=top_k, threshold=threshold
        )
        return result.chunks

    # ── Agentic multi-round retrieval ─────────────────────────────────────────

    async def agentic_retrieve(
        self,
        query: str,
        chapters: list[int],
        *,
        top_k: int | None = None,
        threshold: float | None = None,
        max_rounds: int = 3,
    ) -> AgenticRagResult:
        top_k = top_k or settings.RAG_TOP_K
        threshold = threshold or settings.RAG_THRESHOLD

        # Step 1: decompose query into sub-queries
        sub_queries = await self._plan_queries(query)
        trace: list[dict] = []

        # Deduplication: text prefix → best-scoring chunk
        seen: dict[str, RagChunk] = {}
        active_queries = sub_queries

        for round_num in range(1, max_rounds + 1):
            round_new: list[RagChunk] = []
            for sq in active_queries:
                chunks = await self._raw_retrieve(
                    sq, chapters, top_k=top_k * 2, threshold=threshold
                )
                for c in chunks:
                    key = c.text[:120]
                    if key not in seen or c.score > seen[key].score:
                        seen[key] = c
                        round_new.append(c)

            collected = sorted(seen.values(), key=lambda c: c.score, reverse=True)

            # Step 2: evaluate sufficiency
            eval_result = await self._evaluate_context(query, collected[:top_k])
            trace.append({
                "round": round_num,
                "queries": active_queries,
                "chunks_collected": len(collected),
                "sufficient": eval_result["is_sufficient"],
                "reason": eval_result.get("reason", ""),
                "new_chunks_this_round": len(round_new),
            })

            if eval_result["is_sufficient"] or round_num == max_rounds:
                final = collected[:top_k]
                logger.info(
                    "agentic_rag_complete",
                    query=query[:60],
                    rounds=round_num,
                    chunks=len(final),
                    sufficient=eval_result["is_sufficient"],
                )
                return AgenticRagResult(
                    chunks=final,
                    sub_queries=sub_queries,
                    rounds_used=round_num,
                    sufficient=eval_result["is_sufficient"],
                    trace=trace,
                )

            # Plan follow-up queries for next round
            follow_ups = eval_result.get("follow_up_queries", [])
            if not follow_ups:
                break
            active_queries = follow_ups
            trace[-1]["follow_up_queries"] = follow_ups

        final = sorted(seen.values(), key=lambda c: c.score, reverse=True)[:top_k]
        return AgenticRagResult(
            chunks=final,
            sub_queries=sub_queries,
            rounds_used=max_rounds,
            sufficient=False,
            trace=trace,
        )

    # ── Haiku helpers ─────────────────────────────────────────────────────────

    async def _plan_queries(self, query: str) -> list[str]:
        try:
            resp = await self._client.messages.create(
                model=settings.HAIKU_MODEL,
                max_tokens=256,
                system=_PLANNER_SYSTEM,
                messages=[{"role": "user", "content": f"Question: {query}"}],
            )
            raw = re.sub(r"^```[a-z]*\n?", "", resp.content[0].text.strip()).rstrip("```").strip()
            data = json.loads(raw)
            queries = [q for q in data.get("sub_queries", []) if isinstance(q, str) and q.strip()]
            return queries[:3] if queries else [query]
        except Exception as exc:
            logger.warning("query_planning_failed", error=str(exc))
            return [query]

    async def _evaluate_context(self, query: str, chunks: list[RagChunk]) -> dict:
        if not chunks:
            return {
                "is_sufficient": False,
                "reason": "No chunks retrieved yet",
                "follow_up_queries": [query],
            }
        context_text = "\n".join(f"[{i+1}] Ch.{c.chapter}: {c.text[:220]}" for i, c in enumerate(chunks[:6]))
        try:
            resp = await self._client.messages.create(
                model=settings.HAIKU_MODEL,
                max_tokens=256,
                system=_EVALUATOR_SYSTEM,
                messages=[{"role": "user", "content": f"Question: {query}\n\nContext:\n{context_text}"}],
            )
            raw = re.sub(r"^```[a-z]*\n?", "", resp.content[0].text.strip()).rstrip("```").strip()
            return json.loads(raw)
        except Exception as exc:
            logger.warning("context_evaluation_failed", error=str(exc))
            return {"is_sufficient": True, "reason": "eval_error_assume_sufficient", "follow_up_queries": []}

    async def _raw_retrieve(
        self,
        query: str,
        chapters: list[int],
        top_k: int,
        threshold: float,
    ) -> list[RagChunk]:
        try:
            embedding = await self.embedder.embed(query)
        except Exception as exc:
            logger.error("embedding_failed", error=str(exc))
            return []

        where = {"chapter": {"$in": chapters}} if chapters else None
        try:
            results: list[QueryResult] = await self.vectordb.query(
                query_embedding=embedding,
                n_results=top_k,
                where=where,
            )
        except Exception as exc:
            logger.error("vectordb_query_failed", error=str(exc))
            return []

        return [
            RagChunk(text=r.text, chapter=r.chapter, score=r.score, source=r.source)
            for r in results
            if r.score >= threshold
        ]
