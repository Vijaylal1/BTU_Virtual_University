"""
FAISS vector store adapter.
Uses faiss-cpu for local similarity search with JSON metadata sidecar.
No external server needed – suitable for Vercel / serverless.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
import structlog

from config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class QueryResult:
    text: str
    chapter: int
    score: float
    source: str = ""
    chunk_index: int = 0


class VectorDB:
    """FAISS-backed vector store with cosine similarity."""

    def __init__(self) -> None:
        self._index: Optional[faiss.IndexFlatIP] = None
        self._docs: list[dict] = []  # parallel list: {id, text, chapter, source, chunk_index}
        self._persist_dir: str = ""

    @property
    def _index_path(self) -> str:
        return os.path.join(self._persist_dir, "faiss.index")

    @property
    def _meta_path(self) -> str:
        return os.path.join(self._persist_dir, "faiss_meta.json")

    async def init(self) -> None:
        self._persist_dir = settings.FAISS_PERSIST_DIR
        os.makedirs(self._persist_dir, exist_ok=True)

        if os.path.exists(self._index_path) and os.path.exists(self._meta_path):
            loop = asyncio.get_event_loop()
            self._index = await loop.run_in_executor(None, faiss.read_index, self._index_path)
            with open(self._meta_path, "r", encoding="utf-8") as f:
                self._docs = json.load(f)
            logger.info("faiss_loaded", vectors=self._index.ntotal, persist=self._persist_dir)
        else:
            # Will be created on first add() with correct dimension
            self._index = None
            self._docs = []
            logger.info("faiss_initialized_empty", persist=self._persist_dir)

    def _save(self) -> None:
        if self._index is not None:
            faiss.write_index(self._index, self._index_path)
            with open(self._meta_path, "w", encoding="utf-8") as f:
                json.dump(self._docs, f, ensure_ascii=False)

    async def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        arr = np.array(embeddings, dtype=np.float32)
        # Normalize for cosine similarity (inner product on unit vectors = cosine)
        faiss.normalize_L2(arr)

        if self._index is None:
            dim = arr.shape[1]
            self._index = faiss.IndexFlatIP(dim)

        self._index.add(arr)
        for doc_id, text, meta in zip(ids, documents, metadatas):
            self._docs.append({
                "id": doc_id,
                "text": text,
                "chapter": meta.get("chapter", 0),
                "source": meta.get("source", ""),
                "chunk_index": meta.get("chunk_index", 0),
            })
        self._save()

    async def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[QueryResult]:
        if self._index is None or self._index.ntotal == 0:
            return []

        q = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(q)

        # Over-fetch if filtering by chapter
        fetch_k = min(n_results * 4, self._index.ntotal) if where else min(n_results, self._index.ntotal)
        scores, indices = self._index.search(q, fetch_k)

        # Extract chapter filter
        chapter_filter: set[int] | None = None
        if where and "chapter" in where:
            ch_val = where["chapter"]
            if isinstance(ch_val, dict) and "$in" in ch_val:
                chapter_filter = set(ch_val["$in"])
            elif isinstance(ch_val, int):
                chapter_filter = {ch_val}

        output: list[QueryResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._docs):
                continue
            doc = self._docs[idx]
            if chapter_filter and doc["chapter"] not in chapter_filter:
                continue
            output.append(QueryResult(
                text=doc["text"],
                chapter=doc["chapter"],
                score=float(score),
                source=doc["source"],
                chunk_index=doc["chunk_index"],
            ))
            if len(output) >= n_results:
                break

        return output

    async def delete_collection(self) -> None:
        for path in [self._index_path, self._meta_path]:
            if os.path.exists(path):
                os.remove(path)
        self._index = None
        self._docs = []
