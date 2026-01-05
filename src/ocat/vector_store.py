"""
Vector Store Module for Ocat.

Provides conversation memory storage and retrieval using vector embeddings
for contextual chat interactions. Implements the requirements from bootstrap.md
for episodic memory and real-time conversation storage.
"""

import hashlib
import os
import time
import uuid
import logging

# Suppress ChromaDB telemetry errors
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

# Disable ChromaDB telemetry globally by setting environment variable before import
os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Disable tokenizers parallelism to prevent fork warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from chromadb import Client
from chromadb.config import Settings
from openai import OpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import (
    Checkpoint,
)  # Using LangGraph checkpoint components

from .config import Config
from .exceptions import VectorStoreError
from .utils.logging import setup_logger, LogLevel
from .chunking import DocumentChunker, ChunkingStrategy, DocumentChunk


@dataclass
class Exchange:
    """
    Represents a single prompt/response exchange.

    Attributes
    ----------
    exchange_id : str
        Unique identifier for this exchange
    thread_id : str
        Thread ID for grouping related exchanges
    session_id : str
        Session ID for the current chat session
    user_prompt : str
        The user's input prompt
    assistant_response : str
        The assistant's response
    timestamp : float
        Unix timestamp when exchange was created
    prior_exchange_ids : List[str]
        IDs of exchanges that provided context for this one
    thread_session_id : str
        Composite ID of thread_id + '_' + session_id
    thread_continuation_seq : int
        Sequence number for thread continuations (0 for original, increments per continuation)
    """

    exchange_id: str
    thread_id: str
    session_id: str
    user_prompt: str
    assistant_response: str
    timestamp: float
    prior_exchange_ids: List[str]
    thread_session_id: str = ""
    thread_continuation_seq: int = 0


class ConversationVectorStore:
    """
    Enhanced with LangGraph checkpoint capabilities for memory storage.
    """

    """
    Vector store for conversation memory and context retrieval.

    Implements the conversation storage schema specified in bootstrap.md
    with minimal design, storing user prompts and assistant responses
    with unique IDs and context tracking. Enhanced with LangGraph memory.
    """

    def __init__(self, config: Config):
        """
        Initialize the conversation vector store.

        Parameters
        ----------
        config : Config
            Configuration object containing vector store settings
        """
        self.config = config
        self.logger = setup_logger(
            "ocat.vector_store", LogLevel[config.logging.level], config
        )

        # Setup paths
        self.store_path = Path(config.vector_store.path)
        self.store_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        self.dimension = config.embedding.dimensions
        # Disable telemetry to avoid capture() method signature errors
        chroma_settings = Settings(
            persist_directory=str(self.store_path),
            is_persistent=True,
            anonymized_telemetry=False,
        )
        self.chroma = Client(chroma_settings)


        # Initialize OpenAI client for embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None

        # Initialize memory saver using LangGraph
        self.memory_saver = MemorySaver()


        # Initialize ChromaDB collection
        self.collection = self.chroma.get_or_create_collection(
            name="conversation", metadata={"hnsw:space": "cosine"}
        )

        # Initialize document chunker
        self.chunker = DocumentChunker(
            strategy=ChunkingStrategy(config.chunking.strategy),
            chunk_size=config.chunking.chunk_size,
            chunk_overlap=config.chunking.chunk_overlap,
            max_chunk_size=config.chunking.max_chunk_size,
            preserve_sentence_boundaries=config.chunking.preserve_sentence_boundaries,
        )

        # Initialize LangGraph checkpoint memory with existing exchanges
        self._initialize_checkpoint_memory()

        if config.debug:
            self.logger.debug(f"Vector store configuration:")
            self.logger.debug(f"  - Path: {self.store_path}")
            self.logger.debug(f"  - Embedding model: {config.embedding.model}")
            self.logger.debug(f"  - Dimensions: {config.embedding.dimensions}")
            self.logger.debug(f"  - Similarity threshold: {config.vector_store.similarity_threshold}")
            self.logger.debug(f"  - Chunking strategy: {config.chunking.strategy}")
            
        self.logger.info(f"Vector store initialized at {self.store_path}")
        if config.debug:
            collection_count = self.collection.count()
            self.logger.debug(f"ChromaDB collection contains {collection_count} exchanges")
            if self.openai_client:
                self.logger.debug("OpenAI client initialized for embeddings")
            else:
                self.logger.debug("No OpenAI API key found - embeddings will use ChromaDB defaults")

    def add_exchange(
        self,
        user_prompt: str,
        assistant_response: str,
        thread_id: str,
        session_id: str,
        prior_exchange_ids: Optional[List[str]] = None,
        thread_continuation_seq: int = 0,
    ) -> str:
        """
        Add a new conversation exchange to the ChromaDB vector store.

        Parameters
        ----------
        user_prompt : str
            The user's input prompt
        assistant_response : str
            The assistant's response
        thread_id : str
            Thread ID for grouping related exchanges
        session_id : str
            Session ID for the current chat session
        prior_exchange_ids : Optional[List[str]]
            IDs of exchanges that provided context for this one
        thread_continuation_seq : int, default=0
            Sequence number for thread continuations

        Returns
        -------
        str
            The unique exchange ID for the added exchange

        Raises
        ------
        VectorStoreError
            If embedding generation or storage fails
        """
        try:
            if self.config.debug:
                self.logger.debug(f"Adding exchange to vector store:")
                self.logger.debug(f"  - User prompt: '{user_prompt[:100]}{'...' if len(user_prompt) > 100 else ''}'")
                self.logger.debug(f"  - Response: '{assistant_response[:100]}{'...' if len(assistant_response) > 100 else ''}'")
                self.logger.debug(f"  - Thread ID: {thread_id}")
                self.logger.debug(f"  - Session ID: {session_id}")
                self.logger.debug(f"  - Thread continuation seq: {thread_continuation_seq}")
            
            # Generate unique exchange ID
            exchange_id = str(uuid.uuid4())

            # Generate thread_session_id
            thread_session_id = f"{thread_id}_{session_id}"

            # Create exchange object
            exchange = Exchange(
                exchange_id=exchange_id,
                thread_id=thread_id,
                session_id=session_id,
                user_prompt=user_prompt,
                assistant_response=assistant_response,
                timestamp=time.time(),
                prior_exchange_ids=prior_exchange_ids or [],
                thread_session_id=thread_session_id,
                thread_continuation_seq=thread_continuation_seq,
            )

            # Generate combined text for ChromaDB
            combined_text = f"User: {user_prompt}\nAssistant: {assistant_response}"
            
            if self.config.debug:
                self.logger.debug(f"Generated exchange ID: {exchange_id}")
                self.logger.debug(f"Combined text length: {len(combined_text)} characters")

            # Store in ChromaDB (convert metadata to compatible format)
            metadata_dict = asdict(exchange)
            # Convert prior_exchange_ids list to comma-separated string for ChromaDB
            metadata_dict["prior_exchange_ids"] = ",".join(
                metadata_dict["prior_exchange_ids"]
            )

            self.collection.add(
                ids=[exchange_id],
                documents=[combined_text],
                metadatas=[metadata_dict],
            )


            # ChromaDB auto-persists with DuckDB backend

            # Store in LangGraph checkpoint for memory
            checkpoint_data = {
                "exchange_id": exchange.exchange_id,
                "user_prompt": exchange.user_prompt,
                "assistant_response": exchange.assistant_response,
                "timestamp": exchange.timestamp,
                "thread_id": exchange.thread_id,
                "session_id": exchange.session_id,
            }

            try:
                config = {
                    "configurable": {
                        "thread_id": exchange.thread_id,
                        "checkpoint_ns": "",
                    },
                    "checkpoint_id": exchange.exchange_id,
                }
                # Create checkpoint with required metadata and new_versions
                checkpoint = Checkpoint(
                    {
                        "v": 1,
                        "ts": str(exchange.timestamp),
                        "id": exchange.exchange_id,
                        "channel_values": checkpoint_data,
                        "channel_versions": {},
                        "versions_seen": {},
                        "pending_sends": [],
                    }
                )
                metadata = {
                    "source": "vector_store",
                    "thread_id": exchange.thread_id,
                    "session_id": exchange.session_id,
                }
                self.memory_saver.put(
                    config,
                    checkpoint,
                    metadata,
                    {},  # new_versions
                )
                self.logger.debug(
                    f"Added exchange {exchange_id} to LangGraph checkpoint"
                )
            except Exception as e:
                self.logger.warning(f"Failed to store in LangGraph checkpoint: {e}")

            self.logger.debug(f"Added exchange {exchange_id} to ChromaDB vector store")


            return exchange_id

        except Exception as e:
            self.logger.error(f"Failed to add exchange to vector store: {e}")
            raise VectorStoreError(f"Failed to add exchange: {e}")

    def add_document(
        self,
        text: str,
        thread_id: str,
        session_id: str,
        source_file: Optional[str] = None,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Add a document to the vector store using intelligent chunking.

        Parameters
        ----------
        text : str
            The document text to add
        thread_id : str
            Thread ID for the session
        session_id : str
            Session ID for the chat session
        source_file : Optional[str]
            Path to source file if applicable
        document_id : Optional[str]
            Document ID for linking chunks (auto-generated if not provided)
        metadata : Optional[Dict[str, Any]]
            Additional metadata to include with all chunks

        Returns
        -------
        List[str]
            List of exchange IDs for the added chunks

        Raises
        ------
        VectorStoreError
            If chunking or storage fails
        """
        try:
            # Initialize metadata with session/thread info
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update(
                {
                    "thread_id": thread_id,
                    "session_id": session_id,
                    "is_document_chunk": True,
                }
            )

            # Chunk the document
            chunks = self.chunker.chunk_text(
                text=text,
                source_file=source_file,
                document_id=document_id,
                metadata=doc_metadata,
            )

            if not chunks:
                raise VectorStoreError("Document chunking produced no chunks")

            # Add each chunk to the vector store
            exchange_ids = []

            for chunk in chunks:
                # Create exchange metadata with chunk info
                chunk_metadata = asdict(chunk)

                # Add as an exchange with special markers
                exchange_id = self.add_exchange(
                    user_prompt=f"[Document Chunk {chunk.chunk_index + 1}/{chunk.total_chunks}]",
                    assistant_response=chunk.content,
                    thread_id=thread_id,
                    session_id=session_id,
                    prior_exchange_ids=[],
                )

                # Update ChromaDB metadata with chunk information
                try:
                    # Convert prior_exchange_ids list to comma-separated string for ChromaDB
                    chroma_metadata = chunk_metadata.copy()
                    if "metadata" in chroma_metadata and isinstance(
                        chroma_metadata["metadata"], dict
                    ):
                        # Flatten nested metadata
                        nested_meta = chroma_metadata.pop("metadata")
                        chroma_metadata.update(
                            {f"meta_{k}": str(v) for k, v in nested_meta.items()}
                        )

                    # Ensure all values are strings/numbers for ChromaDB
                    for key, value in chroma_metadata.items():
                        if isinstance(value, (list, dict)):
                            chroma_metadata[key] = str(value)

                    self.collection.update(
                        ids=[exchange_id],
                        metadatas=[chroma_metadata],
                    )
                except Exception as e:
                    self.logger.warning(
                        f"Failed to update ChromaDB metadata for chunk {exchange_id}: {e}"
                    )

                exchange_ids.append(exchange_id)

            self.logger.info(
                f"Added document with {len(chunks)} chunks to vector store. "
                f"Document ID: {chunks[0].document_id}"
            )

            return exchange_ids

        except Exception as e:
            self.logger.error(f"Failed to add document to vector store: {e}")
            raise VectorStoreError(f"Failed to add document: {e}")

    def add_file(
        self,
        file_path: str,
        thread_id: str,
        session_id: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Add a file to the vector store using intelligent chunking.

        Parameters
        ----------
        file_path : str
            Path to the file to add
        thread_id : str
            Thread ID for the session
        session_id : str
            Session ID for the chat session
        document_id : Optional[str]
            Document ID for linking chunks (auto-generated if not provided)
        metadata : Optional[Dict[str, Any]]
            Additional metadata to include with all chunks

        Returns
        -------
        List[str]
            List of exchange IDs for the added chunks

        Raises
        ------
        VectorStoreError
            If file reading, chunking, or storage fails
        """
        try:
            # Initialize metadata with file info
            file_metadata = metadata.copy() if metadata else {}

            # Chunk the file
            chunks = self.chunker.chunk_file(
                file_path=file_path,
                document_id=document_id,
                metadata=file_metadata,
            )

            if not chunks:
                raise VectorStoreError(
                    f"File chunking produced no chunks for {file_path}"
                )

            # Use the document text method to add chunks
            # Get text content for the document method
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            return self.add_document(
                text=text_content,
                thread_id=thread_id,
                session_id=session_id,
                source_file=file_path,
                document_id=chunks[0].document_id,  # Use the generated document_id
                metadata=file_metadata,
            )

        except FileNotFoundError:
            raise VectorStoreError(f"File not found: {file_path}")
        except UnicodeDecodeError:
            raise VectorStoreError(f"Cannot read file as text: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to add file to vector store: {e}")
            raise VectorStoreError(f"Failed to add file: {e}")

    def find_similar_exchanges(
        self,
        query_text: str,
        n_results: int = 5,
        exclude_thread_id: Optional[str] = None,
        exclude_memories: bool = False,
    ) -> List[Exchange]:
        """
        Find exchanges similar to the given query text using ChromaDB.

        Parameters
        ----------
        query_text : str
            Text to find similar exchanges for
        n_results : int, default=5
            Number of similar exchanges to return
        exclude_thread_id : Optional[str]
            Thread ID to exclude from results (current conversation)
        exclude_memories : bool, default=False
            Whether to exclude productivity memories from results

        Returns
        -------
        List[Exchange]
            List of similar exchanges, sorted by similarity

        Raises
        ------
        VectorStoreError
            If similarity search fails
        """
        try:
            collection_count = self.collection.count()
            if self.config.debug:
                self.logger.debug(f"Searching for similar exchanges:")
                self.logger.debug(f"  - Query: '{query_text[:150]}{'...' if len(query_text) > 150 else ''}'")
                self.logger.debug(f"  - Requested results: {n_results}")
                self.logger.debug(f"  - Exclude thread: {exclude_thread_id or 'None'}")
                self.logger.debug(f"  - Exclude memories: {exclude_memories}")
                self.logger.debug(f"  - Total exchanges in store: {collection_count}")
            
            if collection_count == 0:
                if self.config.debug:
                    self.logger.debug("No exchanges in vector store - returning empty results")
                return []

            # Query ChromaDB for similar exchanges
            # Get more results than needed to allow for filtering
            if self.config.debug:
                start_time = time.time()
                
            results = self.collection.query(
                query_texts=[query_text], n_results=n_results * 2
            )
            
            if self.config.debug:
                search_time = time.time() - start_time
                raw_results_count = len(results["ids"][0]) if results["ids"] and results["ids"][0] else 0
                self.logger.debug(f"ChromaDB search completed in {search_time:.3f}s, found {raw_results_count} raw results")

            # Filter by exclude_thread_id and limit to n_results
            similar_exchanges = []
            filtered_count = 0
            memory_filtered_count = 0
            thread_filtered_count = 0
            
            result_metadatas = results.get("metadatas", [[]])[0]
            for i, exchange_id in enumerate(results["ids"][0]):
                if i < len(result_metadatas) and result_metadatas[i]:
                    metadata = result_metadatas[i]
                    exchange = self._metadata_to_exchange(exchange_id, metadata)

                    # Exclude current thread if specified
                    if exclude_thread_id and exchange.thread_id == exclude_thread_id:
                        thread_filtered_count += 1
                        continue

                    # Exclude memories if specified
                    if exclude_memories:
                        # Check if this is a productivity memory
                        if metadata.get("entity_type") == "memory":
                            memory_filtered_count += 1
                            continue

                    similar_exchanges.append(exchange)
                    
                    if self.config.debug:
                        # Get similarity score if available
                        distance = None
                        if "distances" in results and results["distances"] and len(results["distances"][0]) > i:
                            distance = results["distances"][0][i]
                            similarity = 1.0 - distance if distance is not None else None
                        else:
                            similarity = None
                        
                        score_info = f" (similarity: {similarity:.3f})" if similarity is not None else ""
                        self.logger.debug(f"  Result {len(similar_exchanges)}: {exchange_id[:8]}... - '{exchange.user_prompt[:80]}{'...' if len(exchange.user_prompt) > 80 else ''}''{score_info}")

                    if len(similar_exchanges) >= n_results:
                        break

            if self.config.debug:
                self.logger.debug(f"Similarity search filtering results:")
                self.logger.debug(f"  - Found {len(similar_exchanges)} relevant exchanges (after filtering)")
                self.logger.debug(f"  - Filtered out {thread_filtered_count} from current thread")
                self.logger.debug(f"  - Filtered out {memory_filtered_count} memory entries")
            else:
                self.logger.debug(
                    f"Found {len(similar_exchanges)} similar exchanges for query using ChromaDB"
                )

            return similar_exchanges

        except Exception as e:
            self.logger.error(f"Failed to find similar exchanges: {e}")
            raise VectorStoreError(f"Failed to find similar exchanges: {e}")

    def find_relevant_memories(
        self,
        query_text: str,
        n_results: int = 3,
        similarity_threshold: float = 0.7,
    ) -> List[Exchange]:
        """
        Find memories relevant to the given query text.

        Parameters
        ----------
        query_text : str
            Text to find relevant memories for
        n_results : int, default=3
            Maximum number of memories to return
        similarity_threshold : float, default=0.7
            Minimum similarity score for inclusion

        Returns
        -------
        List[Exchange]
            List of relevant memory exchanges, sorted by similarity

        Raises
        ------
        VectorStoreError
            If memory search fails
        """
        try:
            collection_count = self.collection.count()
            if collection_count == 0:
                return []

            # Query ChromaDB for similar exchanges
            results = self.collection.query(
                query_texts=[query_text], n_results=n_results * 3  # Get more to filter
            )

            # Filter for memories only and apply threshold
            relevant_memories = []
            distances = results.get("distances", [[]])[0]
            result_metadata = results.get("metadatas", [[]])[0]

            for i, exchange_id in enumerate(results["ids"][0]):
                # Check if this is a productivity memory
                if i < len(result_metadata) and result_metadata[i]:
                    metadata = result_metadata[i]
                    if metadata.get("entity_type") == "memory":
                        # Check similarity threshold (ChromaDB uses distance, so lower is better)
                        if i < len(distances):
                            similarity = (
                                1.0 - distances[i]
                            )  # Convert distance to similarity
                            if similarity >= similarity_threshold:
                                exchange = self._metadata_to_exchange(exchange_id, metadata)
                                relevant_memories.append(exchange)

                if len(relevant_memories) >= n_results:
                    break

            self.logger.debug(
                f"Found {len(relevant_memories)} relevant memories for query"
            )

            return relevant_memories

        except Exception as e:
            self.logger.error(f"Failed to find relevant memories: {e}")
            raise VectorStoreError(f"Failed to find relevant memories: {e}")

    def get_exchange_by_id(self, exchange_id: str) -> Optional[Exchange]:
        """
        Get a specific exchange by its ID.

        Parameters
        ----------
        exchange_id : str
            The exchange ID to retrieve

        Returns
        -------
        Optional[Exchange]
            The exchange if found, None otherwise
        """
        try:
            results = self.collection.get(ids=[exchange_id])
            if results["ids"] and results["metadatas"] and results["metadatas"][0]:
                return self._metadata_to_exchange(exchange_id, results["metadatas"][0])
            return None
        except Exception as e:
            self.logger.error(f"Failed to get exchange {exchange_id}: {e}")
            return None

    def get_exchanges_by_session_id(self, session_id: str) -> List[Exchange]:
        """
        Get all exchanges for a specific session ID.

        Parameters
        ----------
        session_id : str
            The session ID to retrieve exchanges for

        Returns
        -------
        List[Exchange]
            List of exchanges for the session, sorted by timestamp
        """
        exchanges = [
            exchange
            for exchange in self._get_all_exchanges_from_chromadb()
            if exchange.session_id == session_id
        ]
        return sorted(exchanges, key=lambda x: x.timestamp)

    def get_exchanges_by_thread_id(self, thread_id: str) -> List[Exchange]:
        """
        Get all exchanges for a specific thread ID.

        Parameters
        ----------
        thread_id : str
            The thread ID to retrieve exchanges for

        Returns
        -------
        List[Exchange]
            List of exchanges for the thread, sorted by timestamp
        """
        exchanges = [
            exchange
            for exchange in self._get_all_exchanges_from_chromadb()
            if exchange.thread_id == thread_id
        ]
        return sorted(exchanges, key=lambda x: x.timestamp)

    def delete_exchange(self, exchange_id: str) -> bool:
        """
        Delete an exchange from the ChromaDB vector store.

        Parameters
        ----------
        exchange_id : str
            The exchange ID to delete

        Returns
        -------
        bool
            True if exchange was deleted, False if not found
        """
        try:
            # Check if exchange exists
            results = self.collection.get(ids=[exchange_id])
            if not results["ids"]:
                return False
                
            # Delete from ChromaDB
            self.collection.delete(ids=[exchange_id])

            # ChromaDB auto-persists with DuckDB backend
            self.logger.info(f"Deleted exchange {exchange_id} from ChromaDB")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete exchange {exchange_id}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the ChromaDB vector store.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing vector store statistics
        """
        # Get collection count directly from ChromaDB
        collection_count = self.collection.count()
        
        # Count productivity vs conversation exchanges by querying ChromaDB
        productivity_count = 0
        conversation_count = 0
        
        try:
            all_results = self.collection.get()
            if all_results["metadatas"]:
                for metadata in all_results["metadatas"]:
                    if metadata and metadata.get("entity_type") == "memory":
                        productivity_count += 1
                    else:
                        conversation_count += 1
        except Exception as e:
            self.logger.warning(f"Failed to get detailed stats: {e}")
            # Fallback to just using collection count
            conversation_count = collection_count

        return {
            "total_exchanges": collection_count,
            "conversation_exchanges": conversation_count,
            "productivity_exchanges": productivity_count,
            "collection_count": collection_count,
            "store_path": str(self.store_path),
            "dimension": self.dimension,
            "embedding_model": self.config.embedding.model,
        }

    def _initialize_checkpoint_memory(self):
        """
        Initialize LangGraph checkpoint memory with existing exchanges.
        """
        try:
            exchanges = self._get_all_exchanges_from_chromadb()
            for exchange in exchanges:
                checkpoint_data = {
                    "exchange_id": exchange.exchange_id,
                    "user_prompt": exchange.user_prompt,
                    "assistant_response": exchange.assistant_response,
                    "timestamp": exchange.timestamp,
                    "thread_id": exchange.thread_id,
                    "session_id": exchange.session_id,
                }

                config = {
                    "configurable": {
                        "thread_id": exchange.thread_id,
                        "checkpoint_ns": "",
                    },
                    "checkpoint_id": exchange.exchange_id,
                }
                # Create checkpoint with required metadata and new_versions
                checkpoint = Checkpoint(
                    {
                        "v": 1,
                        "ts": str(exchange.timestamp),
                        "id": exchange.exchange_id,
                        "channel_values": checkpoint_data,
                        "channel_versions": {},
                        "versions_seen": {},
                        "pending_sends": [],
                    }
                )
                metadata = {
                    "source": "vector_store",
                    "thread_id": exchange.thread_id,
                    "session_id": exchange.session_id,
                }
                self.memory_saver.put(
                    config,
                    checkpoint,
                    metadata,
                    {},  # new_versions
                )

            self.logger.debug(
                "Initialized LangGraph checkpoint memory with existing exchanges"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize LangGraph checkpoint memory: {e}")
            # Continue without LangGraph memory - not critical for functionality

    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Generate a deterministic fallback embedding for the given text.

        Uses deterministic np.random.default_rng with MD5 hash seed as specified
        for offline test fallback when OPENAI_API_KEY is not set.

        Parameters
        ----------
        text : str
            Text to generate fallback embedding for

        Returns
        -------
        List[float]
            A deterministic embedding vector with specified dimensions
        """
        # Create deterministic seed from text using MD5 hash
        text_bytes = text.encode("utf-8")
        md5_digest = hashlib.md5(text_bytes).digest()

        # Convert MD5 digest to integer for numpy seed
        seed_int = int.from_bytes(md5_digest[:8], "big")  # Use first 8 bytes

        # Use integer seed for deterministic random number generation
        rng = np.random.default_rng(seed_int)

        # Generate deterministic random embedding
        embedding = rng.random(self.dimension).tolist()

        return embedding

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text using OpenAI's API.

        Falls back to deterministic local embedding if OpenAI API fails or key not set,
        ensuring tests and offline usage don't fail with network issues.

        Parameters
        ----------
        text : str
            Text to generate embedding for

        Returns
        -------
        List[float]
            The generated embedding vector

        Raises
        ------
        VectorStoreError
            If both OpenAI and fallback embedding generation fail
        """
        # Check if OPENAI_API_KEY is set for offline fallback
        if not self.openai_client:
            self.logger.debug(
                "OPENAI_API_KEY not set, using deterministic fallback embedding"
            )
            return self._fallback_embedding(text)

        try:
            # Chunk text if it's too long
            if len(text) > self.config.embedding.chunk_size:
                text = text[: self.config.embedding.chunk_size]

            response = self.openai_client.embeddings.create(
                input=text,
                model=self.config.embedding.model,
                dimensions=self.config.embedding.dimensions,
            )

            return response.data[0].embedding

        except Exception as e:
            self.logger.warning(
                f"OpenAI embedding failed, falling back to local embedding generator: {e}"
            )
            return self._fallback_embedding(text)



    def get_episodic_context(
        self,
        query_text: str,
        max_context_length: int = 2000,
        relevance_threshold: float = 0.7,
    ) -> List[Exchange]:
        """
        Get context using LangGraph checkpoint memory with smart pruning.

        Parameters
        ----------
        query_text : str
            Text to find relevant context for
        max_context_length : int
            Maximum total character length for context
        relevance_threshold : float
            Minimum relevance score for including exchanges

        Returns
        -------
        List[Exchange]
            Relevant exchanges optimized for token usage
        """
        try:
            # Use regular similarity search as primary method
            # Enhanced with smart pruning for token optimization
            # Exclude memories since they'll be handled separately
            similar_exchanges = self.find_similar_exchanges(
                query_text,
                self.config.vector_store.context_results * 2,  # Get more for filtering
                exclude_memories=True,
            )

            # Apply smart pruning for context length
            relevant_exchanges = []
            total_length = 0

            for exchange in similar_exchanges:
                # Calculate length of this exchange
                exchange_length = len(exchange.user_prompt) + len(
                    exchange.assistant_response
                )

                # Only add if it fits within context window
                if total_length + exchange_length <= max_context_length:
                    relevant_exchanges.append(exchange)
                    total_length += exchange_length
                else:
                    break  # Stop adding more exchanges

            self.logger.debug(
                f"Smart context pruning returned {len(relevant_exchanges)} exchanges "
                f"with total length {total_length} chars"
            )

            return relevant_exchanges

        except Exception as e:
            self.logger.warning(f"Context retrieval failed: {e}")
            # Fallback to regular similarity search
            return self.find_similar_exchanges(
                query_text, self.config.vector_store.context_results
            )

    def prune_context_for_tokens(
        self, exchanges: List[Exchange], max_tokens: int = 1000
    ) -> List[Exchange]:
        """
        Prune context exchanges to fit within token limit.

        Uses approximate token counting (4 chars per token) for efficiency.

        Parameters
        ----------
        exchanges : List[Exchange]
            List of exchanges to prune
        max_tokens : int
            Maximum number of tokens to use

        Returns
        -------
        List[Exchange]
            Pruned list of exchanges
        """
        max_chars = max_tokens * 4  # Rough approximation: 4 chars per token

        pruned_exchanges = []
        total_chars = 0

        for exchange in exchanges:
            exchange_chars = len(exchange.user_prompt) + len(
                exchange.assistant_response
            )

            if total_chars + exchange_chars <= max_chars:
                pruned_exchanges.append(exchange)
                total_chars += exchange_chars
            else:
                # Try to fit a truncated version
                remaining_chars = max_chars - total_chars
                if remaining_chars > 100:  # Only if we have meaningful space left
                    # Create truncated exchange
                    truncated_prompt = exchange.user_prompt[: remaining_chars // 2]
                    truncated_response = exchange.assistant_response[
                        : remaining_chars // 2
                    ]

                    truncated_exchange = Exchange(
                        exchange_id=exchange.exchange_id,
                        thread_id=exchange.thread_id,
                        session_id=exchange.session_id,
                        user_prompt=truncated_prompt + "...",
                        assistant_response=truncated_response + "...",
                        timestamp=exchange.timestamp,
                        prior_exchange_ids=exchange.prior_exchange_ids,
                    )
                    pruned_exchanges.append(truncated_exchange)

                break

        self.logger.debug(
            f"Pruned {len(exchanges)} exchanges to {len(pruned_exchanges)} "
            f"for token limit {max_tokens}"
        )

        return pruned_exchanges

    def _metadata_to_exchange(self, exchange_id: str, metadata: Dict[str, Any]) -> Exchange:
        """
        Convert ChromaDB metadata dictionary back to Exchange object.
        
        Parameters
        ----------
        exchange_id : str
            The exchange ID
        metadata : Dict[str, Any]
            ChromaDB metadata dictionary
            
        Returns
        -------
        Exchange
            Reconstructed Exchange object
        """
        # Convert prior_exchange_ids back from comma-separated string to list
        prior_ids_str = metadata.get("prior_exchange_ids", "")
        prior_exchange_ids = prior_ids_str.split(",") if prior_ids_str else []
        
        return Exchange(
            exchange_id=exchange_id,
            thread_id=metadata.get("thread_id", ""),
            session_id=metadata.get("session_id", ""),
            user_prompt=metadata.get("user_prompt", ""),
            assistant_response=metadata.get("assistant_response", ""),
            timestamp=float(metadata.get("timestamp", 0.0)),
            prior_exchange_ids=prior_exchange_ids,
            thread_session_id=metadata.get("thread_session_id", ""),
            thread_continuation_seq=int(metadata.get("thread_continuation_seq", 0)),
        )
    
    def _get_all_exchanges_from_chromadb(self) -> List[Exchange]:
        """
        Get all exchanges from ChromaDB.
        
        Returns
        -------
        List[Exchange]
            All exchanges in the vector store
        """
        try:
            # Get all items from ChromaDB
            results = self.collection.get()
            
            exchanges = []
            if results["ids"] and results["metadatas"]:
                for i, exchange_id in enumerate(results["ids"]):
                    if i < len(results["metadatas"]) and results["metadatas"][i]:
                        exchange = self._metadata_to_exchange(exchange_id, results["metadatas"][i])
                        exchanges.append(exchange)
                        
            return exchanges
        except Exception as e:
            self.logger.error(f"Failed to get all exchanges from ChromaDB: {e}")
            return []
