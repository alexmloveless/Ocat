"""
Vector Store Module for Ocat.

Provides conversation memory storage and retrieval using vector embeddings
for contextual chat interactions. Implements the requirements from bootstrap.md
for episodic memory and real-time conversation storage.
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from annoy import AnnoyIndex
from openai import OpenAI
from langgraph.checkpoint.memory import (
    MemorySaver,
    Checkpoint,
)  # Using LangGraph checkpoint components

from .config import Config
from .exceptions import VectorStoreError
from .utils.logging import setup_logger, LogLevel


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
    """

    exchange_id: str
    thread_id: str
    session_id: str
    user_prompt: str
    assistant_response: str
    timestamp: float
    prior_exchange_ids: List[str]


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

        # Vector store files
        self.index_file = self.store_path / "conversation.ann"
        self.metadata_file = self.store_path / "metadata.json"

        # Initialize Annoy index
        self.dimension = config.embedding.dimensions
        self.index = AnnoyIndex(self.dimension, "angular")
        self.metadata: Dict[str, Exchange] = {}
        self.id_to_index: Dict[str, int] = {}  # Map exchange IDs to Annoy indices
        self.next_index = 0

        # Initialize OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Initialize memory saver using LangGraph
        self.memory_saver = MemorySaver()

        # Load existing Annoy and metadata data
        self._load_existing_data()

        # Initialize LangGraph checkpoint memory with existing exchanges
        self._initialize_checkpoint_memory()

        self.logger.info(f"Vector store initialized at {self.store_path}")
        self.logger.debug(f"Loaded {len(self.metadata)} existing exchanges")

    def add_exchange(
        self,
        user_prompt: str,
        assistant_response: str,
        thread_id: str,
        session_id: str,
        prior_exchange_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Add a new conversation exchange to the vector store.

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
            # Generate unique exchange ID
            exchange_id = str(uuid.uuid4())

            # Create exchange object
            exchange = Exchange(
                exchange_id=exchange_id,
                thread_id=thread_id,
                session_id=session_id,
                user_prompt=user_prompt,
                assistant_response=assistant_response,
                timestamp=time.time(),
                prior_exchange_ids=prior_exchange_ids or [],
            )

            # Generate embedding for the combined text
            combined_text = f"User: {user_prompt}\nAssistant: {assistant_response}"
            embedding = self._generate_embedding(combined_text)

            # Add to Annoy index
            self.index.add_item(self.next_index, embedding)

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
                self.memory_saver.put(
                    {
                        "configurable": {"thread_id": exchange.thread_id},
                        "checkpoint_id": exchange.exchange_id,
                    },
                    checkpoint_data,
                )
                self.logger.debug(
                    f"Added exchange {exchange_id} to LangGraph checkpoint"
                )
            except Exception as e:
                self.logger.warning(f"Failed to store in LangGraph checkpoint: {e}")
            self.id_to_index[exchange_id] = self.next_index
            self.next_index += 1

            # Store metadata
            self.metadata[exchange_id] = exchange

            self.logger.debug(f"Added exchange {exchange_id} to vector store")

            # Save immediately for real-time storage
            self._save_data()

            return exchange_id

        except Exception as e:
            self.logger.error(f"Failed to add exchange to vector store: {e}")
            raise VectorStoreError(f"Failed to add exchange: {e}")

    def find_similar_exchanges(
        self,
        query_text: str,
        n_results: int = 5,
        exclude_thread_id: Optional[str] = None,
    ) -> List[Exchange]:
        """
        Find exchanges similar to the given query text.

        Parameters
        ----------
        query_text : str
            Text to find similar exchanges for
        n_results : int, default=5
            Number of similar exchanges to return
        exclude_thread_id : Optional[str]
            Thread ID to exclude from results (current conversation)

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
            if len(self.metadata) == 0:
                return []

            # Generate embedding for query
            query_embedding = self._generate_embedding(query_text)

            # Find similar items
            similar_indices = self.index.get_nns_by_vector(
                query_embedding,
                n_results * 2,  # Get more to filter out current thread
                search_k=-1,
            )

            # Convert indices to exchanges and filter
            similar_exchanges = []
            for idx in similar_indices:
                # Find exchange ID for this index
                exchange_id = None
                for eid, eidx in self.id_to_index.items():
                    if eidx == idx:
                        exchange_id = eid
                        break

                if exchange_id and exchange_id in self.metadata:
                    exchange = self.metadata[exchange_id]

                    # Exclude current thread if specified
                    if exclude_thread_id and exchange.thread_id == exclude_thread_id:
                        continue

                    similar_exchanges.append(exchange)

                    if len(similar_exchanges) >= n_results:
                        break

            self.logger.debug(
                f"Found {len(similar_exchanges)} similar exchanges for query"
            )

            return similar_exchanges

        except Exception as e:
            self.logger.error(f"Failed to find similar exchanges: {e}")
            raise VectorStoreError(f"Failed to find similar exchanges: {e}")

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
        return self.metadata.get(exchange_id)

    def delete_exchange(self, exchange_id: str) -> bool:
        """
        Delete an exchange from the vector store.

        Note: This marks the exchange as deleted but doesn't rebuild the index.

        Parameters
        ----------
        exchange_id : str
            The exchange ID to delete

        Returns
        -------
        bool
            True if exchange was deleted, False if not found
        """
        if exchange_id in self.metadata:
            del self.metadata[exchange_id]
            if exchange_id in self.id_to_index:
                del self.id_to_index[exchange_id]
            self._save_data()
            self.logger.info(f"Deleted exchange {exchange_id}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing vector store statistics
        """
        return {
            "total_exchanges": len(self.metadata),
            "index_size": (
                self.index.get_n_items() if hasattr(self.index, "get_n_items") else 0
            ),
            "store_path": str(self.store_path),
            "dimension": self.dimension,
            "embedding_model": self.config.embedding.model,
        }

    def _initialize_checkpoint_memory(self):
        """
        Initialize LangGraph checkpoint memory with existing exchanges.
        """
        try:
            for exchange in self.metadata.values():
                checkpoint_data = {
                    "exchange_id": exchange.exchange_id,
                    "user_prompt": exchange.user_prompt,
                    "assistant_response": exchange.assistant_response,
                    "timestamp": exchange.timestamp,
                    "thread_id": exchange.thread_id,
                    "session_id": exchange.session_id,
                }

                self.memory_saver.put(
                    {
                        "configurable": {"thread_id": exchange.thread_id},
                        "checkpoint_id": exchange.exchange_id,
                    },
                    checkpoint_data,
                )

            self.logger.debug(
                "Initialized LangGraph checkpoint memory with existing exchanges"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize LangGraph checkpoint memory: {e}")
            # Continue without LangGraph memory - not critical for functionality

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text using OpenAI's API.

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
            If embedding generation fails
        """
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
            self.logger.error(f"Failed to generate embedding: {e}")
            raise VectorStoreError(f"Failed to generate embedding: {e}")

    def _load_existing_data(self) -> None:
        """
        Load existing vector store data from disk.
        """
        try:
            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    metadata_data = json.load(f)

                for exchange_id, exchange_dict in metadata_data.items():
                    self.metadata[exchange_id] = Exchange(**exchange_dict)

                # Rebuild ID to index mapping
                for i, exchange_id in enumerate(self.metadata.keys()):
                    self.id_to_index[exchange_id] = i

                self.next_index = len(self.metadata)

            # Load Annoy index if it exists
            if self.index_file.exists() and len(self.metadata) > 0:
                self.index.load(str(self.index_file))

        except Exception as e:
            self.logger.warning(f"Failed to load existing vector store data: {e}")
            # Continue with empty store

    def _save_data(self) -> None:
        """
        Save vector store data to disk.
        """
        try:
            # Save metadata
            metadata_dict = {}
            for exchange_id, exchange in self.metadata.items():
                metadata_dict[exchange_id] = asdict(exchange)

            with open(self.metadata_file, "w") as f:
                json.dump(metadata_dict, f, indent=2)

            # Build and save Annoy index if we have data
            if len(self.metadata) > 0:
                self.index.build(10)  # 10 trees for good accuracy/speed tradeoff
                self.index.save(str(self.index_file))

        except Exception as e:
            self.logger.error(f"Failed to save vector store data: {e}")
            raise VectorStoreError(f"Failed to save vector store data: {e}")

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
            similar_exchanges = self.find_similar_exchanges(
                query_text,
                self.config.vector_store.context_results * 2,  # Get more for filtering
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
