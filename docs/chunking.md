# Intelligent Document Chunking

Ocat includes a sophisticated document chunking system that intelligently splits long documents into manageable pieces for optimal vector store performance and retrieval accuracy.

## Overview

The chunking system replaces simple text truncation with multiple intelligent strategies that:

- **Preserve semantic coherence** by respecting sentence and paragraph boundaries
- **Support configurable overlap** between chunks to maintain context
- **Track document provenance** to link chunks back to their source
- **Handle multiple documents** efficiently 
- **Integrate seamlessly** with vector store operations

## Chunking Strategies

### 1. Semantic Chunking (Default)

**Strategy**: `semantic`

Splits text at natural sentence and paragraph boundaries while staying within size limits.

**Benefits**:
- Preserves complete thoughts and concepts
- Maintains readability in retrieved chunks
- Optimal for most document types

**How it works**:
- Splits text into sentences using regex patterns
- Groups sentences until approaching chunk size limit
- Respects maximum chunk size as hard limit
- Adds configurable overlap between chunks

**Best for**: Articles, documentation, books, general text content

### 2. Fixed-Size Chunking

**Strategy**: `fixed_size`

Splits text into fixed-size chunks with word boundary preservation.

**Benefits**:
- Predictable chunk sizes for consistent processing
- Efficient for uniform content
- Good token usage control

**How it works**:
- Splits at fixed character intervals
- Attempts to break at word boundaries when possible
- Adds configurable overlap between chunks
- Falls back to hard breaks if no word boundaries found

**Best for**: Code files, structured data, uniform content

### 3. Hybrid Chunking

**Strategy**: `hybrid`

Combines semantic and fixed-size approaches with automatic fallback.

**Benefits**:
- Semantic chunking for normal text
- Fixed-size fallback for oversized chunks
- Handles diverse content types automatically

**How it works**:
- Attempts semantic chunking first
- Falls back to fixed-size for chunks exceeding max_chunk_size
- Maintains provenance and overlap throughout

**Best for**: Mixed content, unknown document types, production systems

### 4. Truncate (Legacy)

**Strategy**: `truncate`

Simple truncation at character limit (original behavior).

**Benefits**:
- Fastest processing
- Backward compatibility
- Predictable behavior

**When to use**: Only for backward compatibility or when processing speed is critical

## Configuration

Add chunking configuration to your `ocat.yaml`:

```yaml
chunking:
  strategy: "semantic"              # Strategy: semantic, fixed_size, hybrid, truncate
  chunk_size: 1000                  # Target chunk size in characters
  chunk_overlap: 100                # Overlap between chunks in characters  
  max_chunk_size: 1500              # Hard limit for semantic chunks
  preserve_sentence_boundaries: true # Respect word/sentence boundaries
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `strategy` | `"semantic"` | Chunking strategy to use |
| `chunk_size` | `1000` | Target chunk size in characters |
| `chunk_overlap` | `100` | Characters of overlap between chunks |
| `max_chunk_size` | `1500` | Maximum chunk size (hard limit) |
| `preserve_sentence_boundaries` | `true` | Respect sentence/word boundaries |

## Document Provenance

Every chunk includes comprehensive metadata for traceability:

```python
@dataclass
class DocumentChunk:
    chunk_id: str           # Unique chunk identifier
    document_id: str        # Links chunks from same document  
    content: str            # The chunk content
    chunk_index: int        # Index within document (0-based)
    total_chunks: int       # Total chunks in document
    overlap_start: int      # Overlap start position
    overlap_end: int        # Overlap end position
    source_file: Optional[str]  # Source file path if applicable
    metadata: Dict[str, Any]    # Additional metadata
```

### Metadata Tracking

Chunks automatically track:
- **Source information**: File path, file name, file size
- **Session context**: Thread ID, session ID from when added
- **Chunk relationships**: Index, total count, overlap positions
- **Custom metadata**: User-provided key-value pairs

## Command Integration

### `/vadd` Command Enhancement

The `/vadd` command now automatically uses intelligent chunking for long text:

```bash
# Short text - stored as single exchange (original behavior)
/vadd This is a short note.

# Long text - automatically chunked using configured strategy  
/vadd [long document text...]
# → "Long text added to vector store as 3 chunks"
```

### `/attach` Command Enhancement

The `/attach` command now offers vector store integration:

```bash
/attach document1.txt document2.md

# After attaching to conversation, you'll be prompted:
# "Would you like to also add these files to the vector store for future reference? (y/n)"

# If you choose 'y':
# → Files are chunked and added to vector store
# → "Added 2 file(s) to vector store as 8 chunks"
```

## Vector Store Integration

### New Methods

The vector store includes new methods for document handling:

```python
# Add document with chunking
exchange_ids = vector_store.add_document(
    text="Long document content...",
    thread_id="session_123", 
    session_id="thread_456",
    metadata={"author": "user", "category": "docs"}
)

# Add file with chunking
exchange_ids = vector_store.add_file(
    file_path="/path/to/document.txt",
    thread_id="session_123",
    session_id="thread_456", 
    metadata={"department": "engineering"}
)
```

### Chunk Storage

Chunks are stored as special exchanges in the vector store:

- **User prompt**: `[Document Chunk 1/3]` (indicates chunk position)
- **Assistant response**: The actual chunk content
- **Metadata**: Complete chunk provenance and relationships
- **Session/Thread IDs**: Preserved from the original context

### Retrieval and Search

Chunked documents integrate seamlessly with existing search:

```bash
# Find similar content across all documents and chunks
/vquery "machine learning concepts"

# Retrieve specific chunks by document
/vget document_id_12345  

# View chunk relationships and provenance
/vstats  # Shows chunk statistics
```

## Best Practices

### Choosing a Strategy

- **Semantic** (default): Best for most use cases, especially human-readable content
- **Fixed-size**: Use for code, structured data, or when you need predictable chunk sizes  
- **Hybrid**: Safe choice for mixed content or production systems
- **Truncate**: Only for backward compatibility

### Configuration Tuning

**For better retrieval accuracy**:
```yaml
chunking:
  strategy: "semantic"
  chunk_size: 800          # Smaller chunks for more precise matching
  chunk_overlap: 150       # More overlap for better context
```

**For token efficiency**:
```yaml
chunking:
  strategy: "fixed_size" 
  chunk_size: 1200         # Larger chunks for fewer API calls
  chunk_overlap: 50        # Less overlap to reduce redundancy
```

**For mixed content**:
```yaml
chunking:
  strategy: "hybrid"
  chunk_size: 1000
  max_chunk_size: 1500     # Prevent oversized semantic chunks
  chunk_overlap: 100
```

### File Organization

When adding multiple related files:

```bash
# Add files with related metadata
/attach project_docs/*.md
# Choose 'y' when prompted for vector store
# All files will share session/thread context for related retrieval
```

### Memory Management

The system includes automatic memory management:
- Chunk metadata is efficiently stored
- Overlap content is tracked to avoid duplication
- Large documents are processed incrementally
- Vector embeddings are generated per-chunk for optimal search

## Advanced Usage

### Custom Metadata

Enhance chunks with custom metadata for better organization:

```python
# Via Python API
vector_store.add_document(
    text=content,
    thread_id=thread_id,
    session_id=session_id,
    metadata={
        "author": "Dr. Smith",
        "department": "Research", 
        "confidentiality": "internal",
        "tags": ["AI", "machine-learning", "research"]
    }
)
```

### Document Relationships

Link related documents by using consistent metadata:

```python
# Research paper series
for i, paper in enumerate(research_papers):
    vector_store.add_file(
        file_path=paper.path,
        thread_id="research_project",
        session_id="paper_series",
        metadata={
            "series": "AI Research 2024",
            "paper_number": i + 1,
            "total_papers": len(research_papers)
        }
    )
```

### Bulk Processing

For processing many documents efficiently:

```python
# Process multiple files with shared context
thread_id = "document_import_batch_001" 
session_id = "bulk_import_2024"

for file_path in document_paths:
    try:
        vector_store.add_file(
            file_path=file_path,
            thread_id=thread_id,
            session_id=session_id,
            metadata={"batch_id": "import_001", "source": "archive"}
        )
    except Exception as e:
        logger.warning(f"Failed to process {file_path}: {e}")
```

## Troubleshooting

### Common Issues

**Chunks too small/large**:
- Adjust `chunk_size` and `max_chunk_size` in configuration
- Consider switching chunking strategy

**Poor retrieval results**:
- Increase `chunk_overlap` for better context preservation
- Use semantic chunking for better conceptual coherence
- Check that related content is in the same session/thread

**Memory usage concerns**:
- Reduce `chunk_overlap` to minimize redundancy
- Use fixed-size chunking for predictable memory usage
- Process large document sets in batches

**Encoding errors**:
- Ensure files are UTF-8 encoded
- Check file permissions and accessibility
- Verify files contain text content (not binary)

### Performance Optimization

For large document processing:

```yaml
chunking:
  strategy: "fixed_size"    # Fastest processing
  chunk_size: 1500          # Larger chunks = fewer API calls
  chunk_overlap: 50         # Minimal overlap for speed
  preserve_sentence_boundaries: false  # Skip boundary detection
```

For maximum retrieval quality:

```yaml
chunking:
  strategy: "semantic"      # Best content preservation
  chunk_size: 600           # Smaller, focused chunks  
  chunk_overlap: 200        # Substantial overlap for context
  max_chunk_size: 1000      # Prevent overly large chunks
```

## Migration from Simple Truncation

Existing vector stores will continue to work with the new chunking system. The simple truncation behavior is preserved for backward compatibility.

To migrate existing content:
1. Update configuration to preferred chunking strategy
2. Re-add important documents using `/attach` or `/vadd`
3. Use `/vdelete` to remove old truncated entries if desired
4. Existing searches will work across both old and new content

## API Reference

See the complete API documentation in the source code:
- `src/ocat/chunking.py` - Core chunking classes and strategies
- `src/ocat/vector_store.py` - Vector store integration
- `tests/test_chunking.py` - Usage examples and test cases