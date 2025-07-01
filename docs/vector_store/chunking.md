# Document Chunking in Ocat Vector Store

When you add documents to the vector store using Ocat, the chunking behavior is quite **simple and straightforward**:

## Basic Chunking Configuration

The chunking is controlled by the `chunk_size` parameter in the embedding configuration, which defaults to **1000 characters**:

```yaml
embedding:
  chunk_size: 1000  # Text chunk size for embeddings
```

## How Documents Are Processed

### 1. Regular Chat Exchanges (via `/vadd` command)

- The entire text you provide is combined as: `"User: {text}\nAssistant: [Manual addition to vector store]"`
- This combined text is stored as a single document in ChromaDB
- **No automatic splitting occurs** - it's stored as one document

### 2. Text Embedding Generation

- If the text is longer than the `chunk_size` (1000 characters by default), it gets **truncated** rather than split into multiple chunks
- From the code: `if len(text) > self.config.embedding.chunk_size: text = text[:self.config.embedding.chunk_size]`

### 3. File Attachments (via `/attach` command)

- Files are read entirely and combined with headers
- No chunking occurs - the entire file content is added to the conversation as context

## Key Points

- **No sophisticated text splitting**: Ocat currently uses a simple truncation approach rather than intelligent chunking strategies like overlapping windows or semantic boundaries
- **Single document per exchange**: Each conversation exchange or manual addition becomes one document in the vector store
- **Configurable chunk size**: You can adjust the `chunk_size` in your config file, but it only affects the maximum text length sent for embedding generation

## Configuration

You can modify the chunking behavior in your `ocat.yaml` config file:

```yaml
embedding:
  model: "text-embedding-3-small"
  dimensions: 1536
  chunk_size: 1500  # Increase from default 1000 if needed
```

## Design Philosophy

This is a **minimal approach** as mentioned in the project documentation - the system is designed to be evolved over time rather than implementing sophisticated chunking from the start. The focus is on simplicity and core functionality rather than complex text processing strategies.

## Future Considerations

For longer documents that need better chunking, consider:
- Breaking large documents into logical sections before adding them
- Using multiple `/vadd` commands for different parts of a document
- Future enhancement requests for more sophisticated text splitting algorithms
