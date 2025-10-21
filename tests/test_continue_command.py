"""
Test the /continue command functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.ocat.config import Config
from src.ocat.vector_store import ConversationVectorStore
from src.ocat.chat import ChatSession
from rich.console import Console


@pytest.fixture
def temp_vector_store():
    """Create a temporary vector store for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_vector_store):
    """Create a test configuration with vector store enabled."""
    config = Config()
    config.vector_store.enabled = True
    config.vector_store.path = str(temp_vector_store)
    return config


def test_thread_continuation_metadata(test_config):
    """Test that thread continuation metadata is tracked correctly."""
    vector_store = ConversationVectorStore(test_config)

    # Add initial exchange (seq=0)
    thread_id = "test-thread-123"
    session_id_1 = "session-1"

    ex1_id = vector_store.add_exchange(
        user_prompt="What is Python?",
        assistant_response="Python is a programming language.",
        thread_id=thread_id,
        session_id=session_id_1,
        thread_continuation_seq=0,
    )

    # Verify initial exchange metadata
    ex1 = vector_store.get_exchange_by_id(ex1_id)
    assert ex1 is not None
    assert ex1.thread_id == thread_id
    assert ex1.session_id == session_id_1
    assert ex1.thread_continuation_seq == 0
    assert ex1.thread_session_id == f"{thread_id}_{session_id_1}"

    # Add continuation exchange (seq=1)
    session_id_2 = "session-2"

    ex2_id = vector_store.add_exchange(
        user_prompt="Tell me more about Python.",
        assistant_response="Python is used for web development, data science, and more.",
        thread_id=thread_id,
        session_id=session_id_2,
        thread_continuation_seq=1,
    )

    # Verify continuation exchange metadata
    ex2 = vector_store.get_exchange_by_id(ex2_id)
    assert ex2 is not None
    assert ex2.thread_id == thread_id
    assert ex2.session_id == session_id_2
    assert ex2.thread_continuation_seq == 1
    assert ex2.thread_session_id == f"{thread_id}_{session_id_2}"

    # Verify both exchanges are in the same thread
    thread_exchanges = vector_store.get_exchanges_by_thread_id(thread_id)
    assert len(thread_exchanges) == 2
    assert thread_exchanges[0].exchange_id == ex1_id
    assert thread_exchanges[1].exchange_id == ex2_id


def test_chat_session_continue_thread(test_config):
    """Test that ChatSession can continue an existing thread."""
    console = Console()
    chat_session = ChatSession(test_config, console, dummy_mode=True)

    # Create initial thread with some exchanges
    original_thread_id = chat_session.thread_id
    original_session_id = chat_session.session_id

    # Simulate adding exchanges
    if chat_session.vector_store:
        chat_session.vector_store.add_exchange(
            user_prompt="Hello",
            assistant_response="Hi there!",
            thread_id=original_thread_id,
            session_id=original_session_id,
            thread_continuation_seq=0,
        )

        chat_session.vector_store.add_exchange(
            user_prompt="How are you?",
            assistant_response="I'm doing well, thanks!",
            thread_id=original_thread_id,
            session_id=original_session_id,
            thread_continuation_seq=0,
        )

        # Create new session and continue the thread
        new_chat_session = ChatSession(test_config, console, dummy_mode=True)
        new_session_id = new_chat_session.session_id

        # Continue the original thread
        new_chat_session.continue_thread(original_thread_id)

        # Verify thread continuation properties
        assert new_chat_session.thread_id == original_thread_id
        assert new_chat_session.session_id == new_session_id  # Session should be new
        assert new_chat_session.thread_continuation_seq == 1  # Should increment

        # Verify messages were loaded
        # Exclude system messages
        non_system_messages = [
            msg for msg in new_chat_session.messages if msg.role != "system"
        ]
        assert len(non_system_messages) == 4  # 2 exchanges = 4 messages


def test_continue_thread_with_nonexistent_thread(test_config):
    """Test that continuing a nonexistent thread raises ValueError."""
    console = Console()
    chat_session = ChatSession(test_config, console, dummy_mode=True)

    with pytest.raises(ValueError, match="No exchanges found"):
        chat_session.continue_thread("nonexistent-thread-id")


@pytest.mark.asyncio
async def test_continue_command_execution(test_config):
    """Test the /continue command through the command system."""
    console = Console()
    chat_session = ChatSession(test_config, console, dummy_mode=True)

    # Create a thread with exchanges
    if chat_session.vector_store:
        test_thread_id = "test-thread-for-command"

        chat_session.vector_store.add_exchange(
            user_prompt="Test message",
            assistant_response="Test response",
            thread_id=test_thread_id,
            session_id="test-session",
            thread_continuation_seq=0,
        )

        # Execute the continue command
        from src.ocat.commands.continue_command import ContinueCommand

        command = ContinueCommand("continue", "Test command", "")
        result = await command.execute([test_thread_id], chat_session)

        assert result.success
        assert chat_session.thread_id == test_thread_id
        assert chat_session.thread_continuation_seq == 1
