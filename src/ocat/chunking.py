"""
Document Chunking System for Ocat.

Provides intelligent document chunking with multiple strategies for optimal
vector store storage and retrieval. Supports semantic chunking, fixed-size
chunking with overlap, and hybrid approaches.
"""

import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path


class ChunkingStrategy(Enum):
    """Enumeration of available chunking strategies."""

    TRUNCATE = "truncate"  # Simple truncation (original behavior)
    FIXED_SIZE = "fixed_size"  # Fixed size with word boundaries and overlap
    SEMANTIC = "semantic"  # Sentence/paragraph boundaries within size limits
    HYBRID = "hybrid"  # Semantic with fallback to fixed-size


@dataclass
class DocumentChunk:
    """
    Represents a single chunk from a document.

    Attributes
    ----------
    chunk_id : str
        Unique identifier for this chunk
    document_id : str
        Identifier linking chunks from the same document
    content : str
        The chunk content
    chunk_index : int
        Index of this chunk within the document (0-based)
    total_chunks : int
        Total number of chunks in the document
    overlap_start : int
        Character index where overlap with previous chunk starts (0 if no overlap)
    overlap_end : int
        Character index where overlap with next chunk ends (len(content) if no overlap)
    source_file : Optional[str]
        Path to source file if chunk came from a file
    metadata : Dict[str, Any]
        Additional metadata about the chunk
    """

    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    total_chunks: int
    overlap_start: int = 0
    overlap_end: int = 0
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.overlap_end == 0:
            self.overlap_end = len(self.content)
        if self.metadata is None:
            self.metadata = {}


class DocumentChunker:
    """
    Document chunking engine with multiple strategies.

    Provides intelligent document splitting with configurable strategies,
    chunk sizes, overlap, and provenance tracking.
    """

    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        max_chunk_size: int = 1500,
        preserve_sentence_boundaries: bool = True,
    ):
        """
        Initialize the document chunker.

        Parameters
        ----------
        strategy : ChunkingStrategy
            Chunking strategy to use
        chunk_size : int
            Target chunk size in characters
        chunk_overlap : int
            Overlap between chunks in characters
        max_chunk_size : int
            Maximum chunk size (hard limit for semantic chunking)
        preserve_sentence_boundaries : bool
            Whether to preserve sentence boundaries when possible
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size
        self.preserve_sentence_boundaries = preserve_sentence_boundaries

    def chunk_text(
        self,
        text: str,
        source_file: Optional[str] = None,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk text using the configured strategy.

        Parameters
        ----------
        text : str
            Text to chunk
        source_file : Optional[str]
            Path to source file if applicable
        document_id : Optional[str]
            Document ID for linking chunks (auto-generated if not provided)
        metadata : Optional[Dict[str, Any]]
            Additional metadata to include with all chunks

        Returns
        -------
        List[DocumentChunk]
            List of document chunks with provenance tracking
        """
        if not text.strip():
            return []

        # Generate document ID if not provided
        if document_id is None:
            document_id = str(uuid.uuid4())

        # Initialize metadata
        if metadata is None:
            metadata = {}

        # Apply chunking strategy
        if self.strategy == ChunkingStrategy.TRUNCATE:
            chunks = self._chunk_truncate(text)
        elif self.strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(text)
        elif self.strategy == ChunkingStrategy.SEMANTIC:
            chunks = self._chunk_semantic(text)
        elif self.strategy == ChunkingStrategy.HYBRID:
            chunks = self._chunk_hybrid(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")

        # Create DocumentChunk objects with provenance
        document_chunks = []
        total_chunks = len(chunks)

        for i, (content, overlap_start, overlap_end) in enumerate(chunks):
            chunk = DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                content=content,
                chunk_index=i,
                total_chunks=total_chunks,
                overlap_start=overlap_start,
                overlap_end=overlap_end,
                source_file=source_file,
                metadata=metadata.copy(),
            )
            document_chunks.append(chunk)

        return document_chunks

    def _chunk_truncate(self, text: str) -> List[tuple]:
        """Simple truncation chunking (original behavior)."""
        if len(text) <= self.chunk_size:
            return [(text, 0, len(text))]
        return [(text[: self.chunk_size], 0, self.chunk_size)]

    def _chunk_fixed_size(self, text: str) -> List[tuple]:
        """Fixed-size chunking with word boundaries and overlap."""
        if len(text) <= self.chunk_size:
            return [(text, 0, len(text))]

        chunks = []
        start = 0

        while start < len(text):
            # Calculate end position
            end = min(start + self.chunk_size, len(text))

            # If not at the end of text and preserve_sentence_boundaries is True,
            # try to break at word boundary
            if end < len(text) and self.preserve_sentence_boundaries:
                # Look for word boundary within last 100 characters
                search_start = max(end - 100, start)
                space_match = None

                for i in range(end - 1, search_start - 1, -1):
                    if text[i].isspace():
                        space_match = i + 1
                        break

                if space_match and space_match > start:
                    end = space_match

            chunk_content = text[start:end]
            overlap_start = 0 if start == 0 else self.chunk_overlap
            overlap_end = len(chunk_content)

            chunks.append((chunk_content, overlap_start, overlap_end))

            # Move start position with overlap
            if end >= len(text):
                break
            start = max(start + self.chunk_size - self.chunk_overlap, start + 1)

        return chunks

    def _chunk_semantic(self, text: str) -> List[tuple]:
        """Semantic chunking based on sentence and paragraph boundaries."""
        if len(text) <= self.chunk_size:
            return [(text, 0, len(text))]

        # Split into sentences using regex
        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = ""
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # If adding this sentence would exceed max_chunk_size, start new chunk
            if current_length + sentence_length > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
                current_length = sentence_length
            # If adding this sentence would exceed chunk_size, start new chunk
            elif current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
                current_length = sentence_length
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                    current_length += sentence_length + 1
                else:
                    current_chunk = sentence
                    current_length = sentence_length

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)

        # Convert to tuple format with overlap info
        chunk_tuples = []
        for i, chunk in enumerate(chunks):
            overlap_start = 0
            overlap_end = len(chunk)

            # Add overlap for non-first chunks
            if i > 0 and self.chunk_overlap > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-self.chunk_overlap :]
                chunk = overlap_text + " " + chunk
                overlap_start = len(overlap_text) + 1
                overlap_end = len(chunk)

            chunk_tuples.append((chunk, overlap_start, overlap_end))

        return chunk_tuples

    def _chunk_hybrid(self, text: str) -> List[tuple]:
        """Hybrid chunking: semantic with fallback to fixed-size."""
        try:
            # Try semantic chunking first
            semantic_chunks = self._chunk_semantic(text)

            # Check if any chunk is too large
            oversized_chunks = []
            for chunk_content, overlap_start, overlap_end in semantic_chunks:
                if len(chunk_content) > self.max_chunk_size:
                    # Fall back to fixed-size for this chunk
                    sub_chunker = DocumentChunker(
                        strategy=ChunkingStrategy.FIXED_SIZE,
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap,
                        preserve_sentence_boundaries=self.preserve_sentence_boundaries,
                    )
                    sub_chunks = sub_chunker._chunk_fixed_size(chunk_content)
                    oversized_chunks.extend(sub_chunks)
                else:
                    oversized_chunks.append((chunk_content, overlap_start, overlap_end))

            return oversized_chunks

        except Exception:
            # If semantic chunking fails, fall back to fixed-size
            return self._chunk_fixed_size(text)

    def chunk_file(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk a text file.

        Parameters
        ----------
        file_path : str
            Path to the text file to chunk
        document_id : Optional[str]
            Document ID for linking chunks (auto-generated if not provided)
        metadata : Optional[Dict[str, Any]]
            Additional metadata to include with all chunks

        Returns
        -------
        List[DocumentChunk]
            List of document chunks with provenance tracking

        Raises
        ------
        FileNotFoundError
            If the file doesn't exist
        UnicodeDecodeError
            If the file cannot be read as text
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path_obj, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(f"Cannot read file as text: {file_path}") from e

        # Add file-specific metadata
        file_metadata = metadata.copy() if metadata else {}
        file_metadata.update(
            {
                "file_name": file_path_obj.name,
                "file_path": str(file_path_obj),
                "file_size": len(content),
            }
        )

        return self.chunk_text(
            text=content,
            source_file=str(file_path_obj),
            document_id=document_id,
            metadata=file_metadata,
        )
