"""Unit tests for the text chunker."""

from rag.chunker import ChapterChunker


def test_chunk_text_basic():
    chunker = ChapterChunker(chunk_size=10, overlap=2)
    text = " ".join(f"word{i}" for i in range(30))
    chunks = chunker.chunk_text(text, chapter=1, source="test.txt")
    assert len(chunks) > 1
    for c in chunks:
        assert c.chapter == 1
        assert c.source == "test.txt"


def test_chunk_short_text():
    chunker = ChapterChunker(chunk_size=512)
    text = "Short paragraph."
    chunks = chunker.chunk_text(text, chapter=3)
    assert len(chunks) == 1
    assert chunks[0].chapter == 3


def test_chunk_document():
    chunker = ChapterChunker(chunk_size=50, overlap=5)
    content = "\n\n".join(f"Paragraph {i}: " + "word " * 60 for i in range(3))
    chunks = chunker.chunk_document(content, chapter=2)
    assert all(c.chapter == 2 for c in chunks)
    assert len(chunks) > 3
