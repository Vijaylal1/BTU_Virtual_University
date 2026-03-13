"""
Async text embedder using sentence-transformers (free, local model).
Falls back to a simple hash-based placeholder if the model fails to load.
"""

from __future__ import annotations

import asyncio

import structlog

from config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class SentenceTransformerEmbedder:
    """Production embedder using sentence-transformers (runs locally, free)."""

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._dim = self._model.get_sentence_embedding_dimension()
        logger.info("sentence_transformer_loaded", model=settings.EMBEDDING_MODEL, dim=self._dim)

    async def embed(self, text: str) -> list[float]:
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(None, self._model.encode, text)
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, self._model.encode, texts)
        return [e.tolist() for e in embeddings]


class FallbackEmbedder:
    """Deterministic fallback embedder (for testing without model)."""

    DIM = 384  # match all-MiniLM-L6-v2 default dim

    async def embed(self, text: str) -> list[float]:
        import hashlib
        digest = hashlib.sha256(text.encode()).digest()
        floats = [(b / 255.0) - 0.5 for b in digest]
        while len(floats) < self.DIM:
            floats.extend(floats)
        return floats[: self.DIM]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


def get_embedder() -> SentenceTransformerEmbedder | FallbackEmbedder:
    try:
        return SentenceTransformerEmbedder()
    except Exception as exc:
        logger.warning("sentence_transformer_init_failed", error=str(exc))
    logger.warning("using_fallback_embedder")
    return FallbackEmbedder()
