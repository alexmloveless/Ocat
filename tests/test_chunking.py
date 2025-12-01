"""
Tests for the document chunking system.

Tests all chunking strategies, provenance tracking, and integration
with the vector store system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from src.ocat.chunking import (
    DocumentChunker,
    ChunkingStrategy,
    DocumentChunk,
)


class TestDocumentChunk:
    """Test DocumentChunk data class."""

    def test_document_chunk_creation(self):
        """Test creating a DocumentChunk with all fields."""
        chunk = DocumentChunk(
            chunk_id="test-id",
            document_id="doc-id",
            content="Test content",
            chunk_index=0,
            total_chunks=3,
            overlap_start=10,
            overlap_end=50,
            source_file="/test/file.txt",
            metadata={"key": "value"},
        )

        assert chunk.chunk_id == "test-id"
        assert chunk.document_id == "doc-id"
        assert chunk.content == "Test content"
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 3
        assert chunk.overlap_start == 10
        assert chunk.overlap_end == 50
        assert chunk.source_file == "/test/file.txt"
        assert chunk.metadata == {"key": "value"}

    def test_document_chunk_defaults(self):
        """Test DocumentChunk with default values."""
        chunk = DocumentChunk(
            chunk_id="test-id",
            document_id="doc-id",
            content="Test content",
            chunk_index=0,
            total_chunks=1,
        )

        assert chunk.overlap_start == 0
        assert chunk.overlap_end == len("Test content")
        assert chunk.source_file is None
        assert chunk.metadata == {}


class TestDocumentChunker:
    """Test DocumentChunker class and strategies."""

    def test_chunker_initialization(self):
        """Test chunker initialization with default values."""
        chunker = DocumentChunker()

        assert chunker.strategy == ChunkingStrategy.SEMANTIC
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 100
        assert chunker.max_chunk_size == 1500
        assert chunker.preserve_sentence_boundaries is True

    def test_chunker_custom_initialization(self):
        """Test chunker initialization with custom values."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=500,
            chunk_overlap=50,
            max_chunk_size=800,
            preserve_sentence_boundaries=False,
        )

        assert chunker.strategy == ChunkingStrategy.FIXED_SIZE
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 50
        assert chunker.max_chunk_size == 800
        assert chunker.preserve_sentence_boundaries is False


class TestTruncateChunking:
    """Test truncate chunking strategy."""

    def test_truncate_short_text(self):
        """Test truncate chunking with short text."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.TRUNCATE,
            chunk_size=100,
        )

        text = "This is a short text."
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1

    def test_truncate_long_text(self):
        """Test truncate chunking with long text."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.TRUNCATE,
            chunk_size=20,
        )

        text = "This is a very long text that should be truncated."
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text[:20]
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1


class TestFixedSizeChunking:
    """Test fixed-size chunking strategy."""

    def test_fixed_size_short_text(self):
        """Test fixed-size chunking with short text."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=100,
        )

        text = "This is a short text."
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_fixed_size_long_text(self):
        """Test fixed-size chunking with long text."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=30,
            chunk_overlap=10,
        )

        text = "This is a longer text that should be split into multiple chunks for testing."
        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1

        # Check that chunks have proper indices and totals
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == len(chunks)

        # Check overlap (non-first chunks should have overlap)
        for i, chunk in enumerate(chunks[1:], 1):
            assert chunk.overlap_start > 0

    def test_fixed_size_word_boundaries(self):
        """Test that fixed-size chunking respects word boundaries."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=20,
            preserve_sentence_boundaries=True,
        )

        text = "Word boundaries should be preserved when splitting text."
        chunks = chunker.chunk_text(text)

        # Check that chunks don't break words
        for chunk in chunks:
            if len(chunk.content) == 20:  # If chunk is exactly chunk_size
                # It should end at a word boundary
                assert chunk.content[-1].isspace() or chunk.content == text[-20:]


class TestSemanticChunking:
    """Test semantic chunking strategy."""

    def test_semantic_short_text(self):
        """Test semantic chunking with short text."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=200,
        )

        text = "This is a short sentence. This is another one."
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_semantic_long_text(self):
        """Test semantic chunking with multiple sentences."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=50,
            chunk_overlap=10,
        )

        text = (
            "This is the first sentence. "
            "This is the second sentence. "
            "This is the third sentence. "
            "This is the fourth sentence."
        )

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1

        # Check that sentence boundaries are preserved
        for chunk in chunks:
            # Chunks should generally end with sentence endings or be overlaps
            content = chunk.content.strip()
            if not content.endswith(".") and chunk.chunk_index < chunk.total_chunks - 1:
                # If not ending with period, should be due to overlap
                assert chunk.overlap_start > 0

    def test_semantic_max_chunk_size(self):
        """Test that semantic chunking respects max chunk size."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.SEMANTIC,
            chunk_size=30,
            max_chunk_size=50,
        )

        # Create a very long sentence that would exceed max_chunk_size
        long_sentence = (
            "This is an extremely long sentence that goes on and on and should be split "
            * 3
        )
        text = f"{long_sentence}. Short sentence."

        chunks = chunker.chunk_text(text)

        # No chunk should exceed max_chunk_size
        for chunk in chunks:
            assert len(chunk.content) <= chunker.max_chunk_size


class TestHybridChunking:
    """Test hybrid chunking strategy."""

    def test_hybrid_normal_text(self):
        """Test hybrid chunking with normal text (should use semantic)."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.HYBRID,
            chunk_size=50,
            max_chunk_size=100,
        )

        text = "First sentence. Second sentence. Third sentence."
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 1
        # Should behave like semantic chunking for normal text

    def test_hybrid_oversized_chunks(self):
        """Test hybrid chunking falls back to fixed-size for oversized chunks."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.HYBRID,
            chunk_size=30,
            max_chunk_size=50,
        )

        # Create text that would create an oversized chunk with semantic splitting
        very_long_sentence = (
            "This is a very very very very long sentence that exceeds max chunk size."
        )
        text = f"{very_long_sentence} Short sentence."

        chunks = chunker.chunk_text(text)

        # Should use fixed-size fallback
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.content) <= chunker.max_chunk_size


class TestProvenanceTracking:
    """Test document provenance and metadata tracking."""

    def test_document_id_generation(self):
        """Test that document IDs are generated when not provided."""
        chunker = DocumentChunker(chunk_size=50)

        text = "Test text for chunking."
        chunks = chunker.chunk_text(text)

        # Should have generated a document ID
        assert chunks[0].document_id is not None
        assert len(chunks[0].document_id) > 0

        # All chunks should have same document ID
        document_id = chunks[0].document_id
        for chunk in chunks:
            assert chunk.document_id == document_id

    def test_custom_document_id(self):
        """Test using custom document ID."""
        chunker = DocumentChunker(chunk_size=50)

        text = "Test text for chunking."
        custom_id = "my-custom-document-id"
        chunks = chunker.chunk_text(text, document_id=custom_id)

        for chunk in chunks:
            assert chunk.document_id == custom_id

    def test_metadata_propagation(self):
        """Test that metadata is propagated to all chunks."""
        chunker = DocumentChunker(chunk_size=20)

        text = "This is a longer text that will be split into chunks."
        metadata = {"author": "test", "category": "documentation"}

        chunks = chunker.chunk_text(text, metadata=metadata)

        for chunk in chunks:
            assert "author" in chunk.metadata
            assert "category" in chunk.metadata
            assert chunk.metadata["author"] == "test"
            assert chunk.metadata["category"] == "documentation"

    def test_source_file_tracking(self):
        """Test that source file is tracked."""
        chunker = DocumentChunker(chunk_size=50)

        text = "Test content from a file."
        source_file = "/path/to/test.txt"

        chunks = chunker.chunk_text(text, source_file=source_file)

        for chunk in chunks:
            assert chunk.source_file == source_file

    def test_chunk_relationship_tracking(self):
        """Test that chunk relationships are properly tracked."""
        chunker = DocumentChunker(chunk_size=30)

        text = "This is a longer text that will definitely be split into multiple chunks for testing."
        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Check chunk indices and totals
            for i, chunk in enumerate(chunks):
                assert chunk.chunk_index == i
                assert chunk.total_chunks == len(chunks)

                # Each chunk should have unique ID but same document ID
                assert chunk.chunk_id is not None
                assert len(chunk.chunk_id) > 0

                # All chunks should share document ID
                if i > 0:
                    assert chunk.document_id == chunks[0].document_id


class TestFileChunking:
    """Test file-based chunking operations."""

    def test_chunk_file_success(self):
        """Test successful file chunking."""
        chunker = DocumentChunker(chunk_size=50)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("This is test content in a file. It should be chunked properly.")
            temp_file = f.name

        try:
            chunks = chunker.chunk_file(temp_file)

            assert len(chunks) >= 1
            assert all(chunk.source_file == temp_file for chunk in chunks)

            # Check file metadata
            for chunk in chunks:
                assert "file_name" in chunk.metadata
                assert "file_path" in chunk.metadata
                assert "file_size" in chunk.metadata
                assert chunk.metadata["file_path"] == temp_file

        finally:
            os.unlink(temp_file)

    def test_chunk_file_not_found(self):
        """Test chunking non-existent file."""
        chunker = DocumentChunker()

        with pytest.raises(FileNotFoundError):
            chunker.chunk_file("/path/to/nonexistent/file.txt")

    def test_chunk_binary_file(self):
        """Test chunking binary file (should raise UnicodeDecodeError)."""
        chunker = DocumentChunker()

        # Create temporary binary file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")
            temp_file = f.name

        try:
            with pytest.raises(UnicodeDecodeError):
                chunker.chunk_file(temp_file)
        finally:
            os.unlink(temp_file)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_text(self):
        """Test chunking empty text."""
        chunker = DocumentChunker()

        chunks = chunker.chunk_text("")
        assert len(chunks) == 0

        chunks = chunker.chunk_text("   ")  # Whitespace only
        assert len(chunks) == 0

    def test_single_character(self):
        """Test chunking single character."""
        chunker = DocumentChunker(chunk_size=10)

        chunks = chunker.chunk_text("A")
        assert len(chunks) == 1
        assert chunks[0].content == "A"

    def test_exact_chunk_size(self):
        """Test text that's exactly chunk size."""
        chunker = DocumentChunker(chunk_size=20, chunk_overlap=0)

        text = "12345678901234567890"  # Exactly 20 characters
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_invalid_strategy(self):
        """Test invalid chunking strategy."""
        with pytest.raises(ValueError):
            chunker = DocumentChunker()
            chunker.strategy = "invalid_strategy"
            chunker.chunk_text("test")

    def test_very_large_overlap(self):
        """Test overlap larger than chunk size."""
        chunker = DocumentChunker(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=20,
            chunk_overlap=50,  # Larger than chunk size
        )

        text = "This is a test of chunking with very large overlap settings."
        chunks = chunker.chunk_text(text)

        # Should still work, but might create some interesting overlap behavior
        assert len(chunks) >= 1


if __name__ == "__main__":
    pytest.main([__file__])
