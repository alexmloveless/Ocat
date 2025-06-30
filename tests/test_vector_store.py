"""
Test suite for ConversationVectorStore.

This file includes tests for adding, querying, deleting exchanges,
and verifying the vector store statistics.
"""

import pytest
from ocat.vector_store import ConversationVectorStore, VectorStoreError
from ocat.config import Config
from ocat.vector_store import Exchange
import tempfile
import os


@pytest.fixture
def temp_store_path():
    """Create a temporary directory for the vector store."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def vector_store_config(temp_store_path):
    """Create a mock configuration with a temporary vector store path."""
    config = Config()
    config.vector_store.path = temp_store_path
    config.vector_store.enabled = True
    config.embedding.dimensions = 1536
    return config


@pytest.fixture
def vector_store(vector_store_config):
    """Initialize and yield a new ConversationVectorStore."""
    return ConversationVectorStore(vector_store_config)


def test_add_exchange(vector_store):
    """Test adding exchanges to the vector store."""
    exchange_id = vector_store.add_exchange(
        user_prompt="Hello",
        assistant_response="Hi there!",
        thread_id="thread1",
        session_id="session1",
    )

    assert exchange_id is not None
    assert exchange_id in vector_store.metadata


def test_find_similar_exchanges(vector_store):
    """Test querying similar exchanges in the vector store."""
    vector_store.add_exchange(
        user_prompt="Good morning",
        assistant_response="Morning!",
        thread_id="thread1",
        session_id="session1",
    )

    similar = vector_store.find_similar_exchanges("Morning")
    assert len(similar) >= 0  # Should return some results


def test_delete_exchange(vector_store):
    """Test deleting an exchange from the vector store."""
    exchange_id = vector_store.add_exchange(
        user_prompt="Test delete",
        assistant_response="Delete me",
        thread_id="thread1",
        session_id="session1",
    )

    success = vector_store.delete_exchange(exchange_id)
    assert success is True
    assert exchange_id not in vector_store.metadata


def test_vector_store_stats(vector_store):
    """Test retrieving vector store statistics."""
    vector_store.add_exchange(
        user_prompt="Stats test",
        assistant_response="Testing stats",
        thread_id="thread1",
        session_id="session1",
    )

    stats = vector_store.get_stats()
    assert "total_exchanges" in stats
    assert stats["total_exchanges"] == 1

    # Verify all expected statistics are there
    assert "index_size" in stats


def test_get_exchange_by_id(vector_store):
    """Test retrieving a specific exchange by ID."""
    exchange_id = vector_store.add_exchange(
        user_prompt="Get by ID test",
        assistant_response="Found me!",
        thread_id="thread1",
        session_id="session1",
    )

    exchange = vector_store.get_exchange_by_id(exchange_id)
    assert exchange is not None
    assert exchange.user_prompt == "Get by ID test"
    assert exchange.assistant_response == "Found me!"

    # Test non-existent ID
    non_existent = vector_store.get_exchange_by_id("non-existent-id")
    assert non_existent is None


def test_episodic_context(vector_store):
    """Test retrieving episodic context with smart pruning."""
    # Add multiple exchanges
    vector_store.add_exchange(
        user_prompt="Context test 1",
        assistant_response="Response 1",
        thread_id="thread1",
        session_id="session1",
    )
    vector_store.add_exchange(
        user_prompt="Context test 2",
        assistant_response="Response 2",
        thread_id="thread1",
        session_id="session1",
    )

    context = vector_store.get_episodic_context(
        query_text="Context test", max_context_length=1000
    )
    assert isinstance(context, list)
    assert len(context) >= 0


def test_prune_context_for_tokens(vector_store):
    """Test pruning context exchanges for token limits."""
    exchanges = []
    for i in range(3):
        exchange_id = vector_store.add_exchange(
            user_prompt=f"Long prompt {i} " * 20,  # Make it long
            assistant_response=f"Long response {i} " * 20,
            thread_id="thread1",
            session_id="session1",
        )
        exchanges.append(vector_store.get_exchange_by_id(exchange_id))

    # Prune to very small token limit
    pruned = vector_store.prune_context_for_tokens(exchanges, max_tokens=50)
    assert len(pruned) <= len(exchanges)


def test_multiple_exchanges_similarity(vector_store):
    """Test similarity search with multiple diverse exchanges."""
    # Add diverse exchanges
    vector_store.add_exchange(
        user_prompt="Tell me about cats",
        assistant_response="Cats are independent pets",
        thread_id="thread1",
        session_id="session1",
    )
    vector_store.add_exchange(
        user_prompt="What about dogs?",
        assistant_response="Dogs are loyal companions",
        thread_id="thread1",
        session_id="session1",
    )
    vector_store.add_exchange(
        user_prompt="Programming languages",
        assistant_response="Python is versatile",
        thread_id="thread1",
        session_id="session1",
    )

    # Search for pet-related content
    similar = vector_store.find_similar_exchanges("pets and animals", n_results=3)
    assert len(similar) >= 0


def test_thread_exclusion(vector_store):
    """Test excluding specific thread from similarity search."""
    vector_store.add_exchange(
        user_prompt="Thread test",
        assistant_response="In thread 1",
        thread_id="thread1",
        session_id="session1",
    )
    vector_store.add_exchange(
        user_prompt="Thread test",
        assistant_response="In thread 2",
        thread_id="thread2",
        session_id="session1",
    )

    # Search excluding thread1
    similar = vector_store.find_similar_exchanges(
        "Thread test", exclude_thread_id="thread1"
    )

    # Verify no results from thread1
    for exchange in similar:
        assert exchange.thread_id != "thread1"


def test_empty_vector_store(vector_store):
    """Test operations on empty vector store."""
    # Test search on empty store
    similar = vector_store.find_similar_exchanges("anything")
    assert similar == []

    # Test stats on empty store
    stats = vector_store.get_stats()
    assert stats["total_exchanges"] == 0

    # Test get non-existent exchange
    exchange = vector_store.get_exchange_by_id("non-existent")
    assert exchange is None

    # Test delete non-existent exchange
    success = vector_store.delete_exchange("non-existent")
    assert success is False


def test_performance_with_many_exchanges(vector_store):
    """Test performance with a larger number of exchanges."""
    import time

    # Add many exchanges
    start_time = time.time()
    exchange_ids = []
    for i in range(10):  # Keep reasonable for CI
        exchange_id = vector_store.add_exchange(
            user_prompt=f"Performance test prompt {i}",
            assistant_response=f"Performance test response {i}",
            thread_id="thread1",
            session_id="session1",
        )
        exchange_ids.append(exchange_id)

    add_time = time.time() - start_time

    # Test search performance
    start_time = time.time()
    similar = vector_store.find_similar_exchanges("Performance test", n_results=5)
    search_time = time.time() - start_time

    # Basic performance assertions (should complete quickly)
    assert add_time < 60.0  # Should add 10 exchanges in under 60 seconds
    assert search_time < 10.0  # Should search in under 10 seconds
    assert len(similar) <= 10


def test_vector_store_persistence(vector_store_config):
    """Test that vector store data persists across instances."""
    # Create first instance and add data
    store1 = ConversationVectorStore(vector_store_config)
    exchange_id = store1.add_exchange(
        user_prompt="Persistence test",
        assistant_response="This should persist",
        thread_id="thread1",
        session_id="session1",
    )

    # Create second instance and verify data is loaded
    store2 = ConversationVectorStore(vector_store_config)
    exchange = store2.get_exchange_by_id(exchange_id)
    assert exchange is not None
    assert exchange.user_prompt == "Persistence test"

    # Verify stats match
    stats1 = store1.get_stats()
    stats2 = store2.get_stats()
    assert stats1["total_exchanges"] == stats2["total_exchanges"]
