"""
Chapter ingestion script – reads markdown/txt files from data/chapters/,
chunks them, embeds them, and upserts into FAISS.

Usage:
    python -m rag.ingest --source data/chapters/
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import re
from pathlib import Path

import structlog

from config.settings import get_settings
from rag.chunker import ChapterChunker
from rag.embedder import get_embedder
from rag.vectordb import VectorDB

logger = structlog.get_logger(__name__)
settings = get_settings()

_CHAPTER_RE = re.compile(r"chapter[_-]?(\d+)", re.IGNORECASE)


def _detect_chapter(filename: str) -> int:
    m = _CHAPTER_RE.search(filename)
    if m:
        return int(m.group(1))
    raise ValueError(f"Cannot detect chapter number from filename: {filename}")


def _chunk_id(chapter: int, chunk_index: int, text: str) -> str:
    h = hashlib.md5(text.encode()).hexdigest()[:8]
    return f"ch{chapter:02d}_idx{chunk_index:04d}_{h}"


async def ingest_directory(source: str) -> None:
    source_path = Path(source)
    if not source_path.exists():
        logger.error("source_not_found", path=source)
        return

    embedder = get_embedder()
    vectordb = VectorDB()
    await vectordb.init()
    chunker = ChapterChunker()

    files = sorted(source_path.glob("*.md")) + sorted(source_path.glob("*.txt"))
    if not files:
        logger.warning("no_files_found", path=source)
        return

    for filepath in files:
        chapter = _detect_chapter(filepath.name)
        content = filepath.read_text(encoding="utf-8")
        chunks = chunker.chunk_document(content, chapter=chapter, source=filepath.name)

        logger.info("ingesting_file", file=filepath.name, chapter=chapter, chunks=len(chunks))

        # Batch embed
        texts = [c.text for c in chunks]
        BATCH = 50
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), BATCH):
            batch = texts[i : i + BATCH]
            embs = await embedder.embed_batch(batch)
            all_embeddings.extend(embs)

        # Upsert into FAISS
        ids = [_chunk_id(chapter, c.chunk_index, c.text) for c in chunks]
        metadatas = [
            {"chapter": c.chapter, "source": c.source, "chunk_index": c.chunk_index}
            for c in chunks
        ]
        await vectordb.add(
            ids=ids,
            embeddings=all_embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info("file_ingested", file=filepath.name, vectors=len(chunks))

    logger.info("ingestion_complete", files=len(files))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest BTU chapters into FAISS")
    parser.add_argument("--source", default="data/chapters/", help="Directory with chapter files")
    args = parser.parse_args()
    asyncio.run(ingest_directory(args.source))


if __name__ == "__main__":
    main()
