"""
Regression test for vector store bug identified on 2025-06-30.

This test reproduces a bug where the ConversationVectorStore.find_similar_exchanges()
method fails to return the correct similar exchange when searching for specific terms.
The bug appears to affect the relevance ranking or similarity search functionality.

This test is marked with xfail initially to keep CI green until the fix is shipped.
Once the bug is fixed, the xfail decorator should be removed.
"""

import pytest
import tempfile
from ocat.vector_store import ConversationVectorStore
from ocat.config import Config


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
    config.logging.level = "DEBUG"  # Enable debug logging for tests
    return config


@pytest.fixture
def vector_store(vector_store_config):
    """Initialize and yield a new ConversationVectorStore."""
    return ConversationVectorStore(vector_store_config)


@pytest.mark.xfail(
    reason="Bug: vector store similarity search not returning correct results"
)
def test_vector_store_metallica_search_bug(vector_store):
    """
    Test that reproduces the vector store bug where similarity search fails.

    The bug: When searching for "metallica" after adding three clearly different
    exchanges about cats, dogs, and metallica, the search should return the
    metallica exchange but currently fails to do so.

    This test will fail until the vector store similarity search bug is fixed.
    """
    # Add three clearly different exchanges
    cats_exchange_id = vector_store.add_exchange(
        user_prompt="Tell me about cats",
        assistant_response="Cats are independent and graceful animals. They are popular pets known for their hunting skills and affectionate nature when they choose to be.",
        thread_id="thread1",
        session_id="session1",
    )

    dogs_exchange_id = vector_store.add_exchange(
        user_prompt="What about dogs?",
        assistant_response="Dogs are loyal and friendly companions. They are known as man's best friend and come in many different breeds with varying temperaments.",
        thread_id="thread2",
        session_id="session1",
    )

    metallica_exchange_id = vector_store.add_exchange(
        user_prompt="Tell me about metallica",
        assistant_response="Metallica is a legendary heavy metal band formed in 1981. They are known for iconic albums like Master of Puppets and The Black Album, and have influenced countless metal bands.",
        thread_id="thread3",
        session_id="session1",
    )

    # Search for "metallica" - should return the metallica exchange
    similar_exchanges = vector_store.find_similar_exchanges("metallica", n_results=1)

    # Verify we got results
    assert (
        len(similar_exchanges) > 0
    ), "Expected at least one similar exchange to be returned"

    # The most similar exchange should be the metallica one
    most_similar = similar_exchanges[0]

    # This assertion should pass once the bug is fixed
    assert "metallica" in most_similar.assistant_response.lower(), (
        f"Expected the most similar exchange to contain 'metallica' in the assistant response. "
        f"Got exchange_id: {most_similar.exchange_id}, "
        f"response: '{most_similar.assistant_response}'"
    )

    # Additional verification: ensure it's the correct exchange
    assert most_similar.exchange_id == metallica_exchange_id, (
        f"Expected the metallica exchange (ID: {metallica_exchange_id}) to be returned, "
        f"but got exchange ID: {most_similar.exchange_id}"
    )


@pytest.mark.xfail(reason="Bug: vector store similarity search ranking issues")
def test_vector_store_search_relevance_ranking(vector_store):
    """
    Test that verifies correct relevance ranking in similarity search.

    This test ensures that when searching for specific terms, the most relevant
    exchange is returned first in the results list.
    """
    # Add exchanges with varying relevance to "music"
    classical_id = vector_store.add_exchange(
        user_prompt="I enjoy classical music",
        assistant_response="Classical music has a rich history spanning centuries, with composers like Bach, Mozart, and Beethoven creating timeless masterpieces.",
        thread_id="thread1",
        session_id="session1",
    )

    food_id = vector_store.add_exchange(
        user_prompt="What's for dinner?",
        assistant_response="How about some pasta with marinara sauce? It's quick to make and quite delicious.",
        thread_id="thread2",
        session_id="session1",
    )

    rock_music_id = vector_store.add_exchange(
        user_prompt="Tell me about rock music",
        assistant_response="Rock music emerged in the 1950s and has evolved into many subgenres. It typically features electric guitars, bass, and drums, with powerful vocals.",
        thread_id="thread3",
        session_id="session1",
    )

    # Search for "music" - should return music-related exchanges first
    similar_exchanges = vector_store.find_similar_exchanges("music", n_results=3)

    # Verify we got results
    assert (
        len(similar_exchanges) >= 2
    ), "Expected at least 2 similar exchanges to be returned"

    # The top results should be music-related, not the food exchange
    top_two_exchanges = similar_exchanges[:2]
    music_exchange_ids = {classical_id, rock_music_id}

    returned_music_ids = {ex.exchange_id for ex in top_two_exchanges}

    # This should pass once the ranking bug is fixed
    assert returned_music_ids == music_exchange_ids, (
        f"Expected the top 2 results to be the music-related exchanges "
        f"(IDs: {music_exchange_ids}), but got IDs: {returned_music_ids}"
    )

    # Verify the food exchange is not in the top results
    for exchange in top_two_exchanges:
        assert (
            exchange.exchange_id != food_id
        ), f"Food exchange (ID: {food_id}) should not be in top 2 results for 'music' search"


@pytest.mark.xfail(reason="Bug: vector store empty results on valid searches")
def test_vector_store_non_empty_search_results(vector_store):
    """
    Test that ensures searches return non-empty results when relevant data exists.

    This addresses a potential bug where valid searches return empty results
    even when the vector store contains relevant exchanges.
    """
    # Add a diverse set of exchanges
    programming_id = vector_store.add_exchange(
        user_prompt="How do I learn Python programming?",
        assistant_response="Python is a great language for beginners. Start with basic syntax, then move to data structures, functions, and object-oriented programming.",
        thread_id="thread1",
        session_id="session1",
    )

    cooking_id = vector_store.add_exchange(
        user_prompt="How do I cook a good steak?",
        assistant_response="For a good steak, let it reach room temperature, season well, and cook on high heat. Use a meat thermometer for desired doneness.",
        thread_id="thread2",
        session_id="session1",
    )

    travel_id = vector_store.add_exchange(
        user_prompt="Best places to travel in Europe?",
        assistant_response="Europe offers amazing destinations like Paris for culture, Barcelona for architecture, and the Swiss Alps for natural beauty.",
        thread_id="thread3",
        session_id="session1",
    )

    # These searches should all return non-empty results
    search_terms = ["programming", "cooking", "travel", "Python", "steak", "Europe"]

    for term in search_terms:
        results = vector_store.find_similar_exchanges(term, n_results=3)

        # This should pass once the bug is fixed
        assert len(results) > 0, (
            f"Search for '{term}' returned empty results, but vector store contains "
            f"relevant exchanges. This indicates a search functionality bug."
        )

        # Verify results are actual Exchange objects
        for exchange in results:
            assert hasattr(
                exchange, "exchange_id"
            ), "Result should be an Exchange object"
            assert hasattr(
                exchange, "user_prompt"
            ), "Result should have user_prompt attribute"
            assert hasattr(
                exchange, "assistant_response"
            ), "Result should have assistant_response attribute"
