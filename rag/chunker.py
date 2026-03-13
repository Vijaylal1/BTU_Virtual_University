"""
Text chunker – splits curriculum text into 512-token overlapping chunks.
Preserves chapter metadata for scoped retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from config.settings import get_settings

settings = get_settings()


@dataclass
class TextChunk:
    text: str
    chapter: int
    chunk_index: int
    source: str = ""   # filename or doc title


class ChapterChunker:
    def __init__(
        self,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> None:
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.overlap = overlap or settings.RAG_CHUNK_OVERLAP

    def chunk_text(self, text: str, chapter: int, source: str = "") -> list[TextChunk]:
        """Split text into overlapping word-based chunks."""
        words = text.split()
        chunks: list[TextChunk] = []
        start = 0
        idx = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append(TextChunk(
                text=chunk_text,
                chapter=chapter,
                chunk_index=idx,
                source=source,
            ))
            if end == len(words):
                break
            start = end - self.overlap
            idx += 1
        return chunks

    def chunk_document(self, content: str, chapter: int, source: str = "") -> list[TextChunk]:
        """Chunk a full chapter document, splitting on paragraph boundaries first."""
        paragraphs = re.split(r"\n{2,}", content.strip())
        all_chunks: list[TextChunk] = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            all_chunks.extend(self.chunk_text(para, chapter, source))
        return all_chunks
