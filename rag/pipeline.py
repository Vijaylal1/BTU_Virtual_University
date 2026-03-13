"""
RAG Pipeline – the main retrieval interface used by all agents.
Embeds a query, filters by chapter scope, and returns ranked RagChunk results.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from config.settings import get_settings
from rag.embedder import FallbackEmbedder, SentenceTransformerEmbedder, get_embedder
from rag.vectordb import QueryResult, VectorDB

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class RagChunk:
    text: str
    chapter: int
    score: float
    source: str = ""


class RAGPipeline:
    def __init__(self) -> None:
        self.embedder: SentenceTransformerEmbedder | FallbackEmbedder = get_embedder()
        self.vectordb = VectorDB()

    async def init(self) -> None:
        await self.vectordb.init()
        logger.info("rag_pipeline_ready")

    async def retrieve(
        self,
        query: str,
        chapters: list[int],
        top_k: int | None = None,
        threshold: float | None = None,
    ) -> list[RagChunk]:
        """
        Embed query, filter by chapter scope, return ranked chunks above threshold.
        """
        top_k = top_k or settings.RAG_TOP_K
        threshold = threshold or settings.RAG_THRESHOLD

        try:
            embedding = await self.embedder.embed(query)
        except Exception as exc:
            logger.error("embedding_failed", error=str(exc))
            return []

        where = {"chapter": {"$in": chapters}} if chapters else None

        try:
            results: list[QueryResult] = await self.vectordb.query(
                query_embedding=embedding,
                n_results=top_k * 2,   # over-fetch then filter by threshold
                where=where,
            )
        except Exception as exc:
            logger.error("vectordb_query_failed", error=str(exc))
            return []

        chunks = [
            RagChunk(text=r.text, chapter=r.chapter, score=r.score, source=r.source)
            for r in results
            if r.score >= threshold
        ]
        # Sort by score descending, return top_k
        chunks.sort(key=lambda c: c.score, reverse=True)
        logger.debug("rag_retrieved", query=query[:60], chapters=chapters, found=len(chunks))
        return chunks[:top_k]
