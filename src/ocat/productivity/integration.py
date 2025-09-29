"""
Integration layer for productivity system with main Ocat chat.

Provides seamless integration between the traditional Ocat chat system
and the pydantic-ai productivity agent.
"""

import re
from typing import Optional, TYPE_CHECKING
from .tools import productivity_agent
from .storage import ProductivityStorage
from .memory_suggester import MemorySuggester

if TYPE_CHECKING:
    from ..chat import ChatSession


class ProductivityIntegration:
    """
    Integration layer between Ocat chat and productivity system.

    Detects productivity-related requests and routes them to the
    pydantic-ai productivity agent while maintaining the normal
    chat flow for other requests.
    """

    def __init__(self, storage: ProductivityStorage):
        """
        Initialize productivity integration.

        Parameters
        ----------
        storage : ProductivityStorage
            The productivity storage instance
        """
        self.storage = storage

        # Initialize memory suggester for proactive memory management
        self.memory_suggester = MemorySuggester(storage)

        # Note: Keyword-based routing has been replaced with explicit marker-based routing
        # The old productivity_keywords, productivity_phrases, and compiled_patterns
        # are no longer used and can be removed in a future cleanup

    def should_use_productivity_agent(self, user_input: str, routing_marker: str = "%") -> bool:
        """
        Determine if the user input should be handled by the productivity agent.
        Now uses explicit marker-based routing instead of keyword detection.

        Parameters
        ----------
        user_input : str
            The user's input message
        routing_marker : str
            The marker symbol that must prefix productivity messages

        Returns
        -------
        bool
            True if this should be handled by productivity agent
        """
        # Check if the input starts with the routing marker
        stripped_input = user_input.strip()
        return stripped_input.startswith(routing_marker)

    async def process_productivity_request(
        self, user_input: str, chat_session: "ChatSession"
    ) -> Optional[str]:
        """
        Process a productivity request using the pydantic-ai agent.

        Parameters
        ----------
        user_input : str
            The user's input message
        chat_session : ChatSession
            The current chat session for context

        Returns
        -------
        Optional[str]
            The response from the productivity agent, or None if failed
        """
        try:
            # Run the productivity agent with the user input
            result = await productivity_agent.run(user_input, deps=self.storage)

            # Log the productivity action for the chat session
            if chat_session.logger:
                chat_session.logger.info(
                    f"Processed productivity request: {user_input[:50]}..."
                )

            return result.output  # type: ignore[attr-defined]

        except Exception as e:
            # Log the error but don't crash the chat
            if chat_session.logger:
                chat_session.logger.error(f"Productivity agent error: {e}")

            # Also print to console for debugging
            print(f"Productivity agent error: {e}")
            import traceback

            traceback.print_exc()

            # Return a helpful error message
            return (
                "I encountered an issue processing your productivity request. "
                "Please try rephrasing your request or contact support if the problem persists."
            )

    def get_system_prompt_addition(self) -> str:
        """
        Get additional system prompt text to inform the main agent about productivity capabilities.

        Returns
        -------
        str
            Additional system prompt text
        """
        return """

## Productivity Capabilities

You have access to a comprehensive productivity system that can help users manage:
- Tasks and todos with due dates, priorities, and categories
- Events and meetings with dates, times, and participants  
- Reminders with trigger times and categories
- Memories for storing important information

When users make requests related to productivity (creating tasks, scheduling events, setting reminders, etc.), 
the system will automatically route these to specialized productivity tools for handling.

You should acknowledge productivity actions and provide helpful context about what was created or updated.
"""

    def maybe_extract_memory_fact(self, user_msg: str) -> Optional[str]:
        """
        Extract a fact from user message that might be worth remembering.

        Parameters
        ----------
        user_msg : str
            The user's message to analyze

        Returns
        -------
        Optional[str]
            The fact to suggest storing, or None if no suggestion should be made
        """
        return self.memory_suggester.should_suggest(user_msg)

    def store_memory(self, fact: str) -> str:
        """
        Store a fact as a memory in the productivity system.

        Parameters
        ----------
        fact : str
            The fact to store

        Returns
        -------
        str
            The pseudo-ID of the created memory
        """
        from .models import Memory  # Local import to avoid circular dependency
        from datetime import datetime

        memory = Memory(
            pseudo_id=f"memory{len(self.storage.search_entities('', limit=1000)) + 1:03d}",
            content=fact,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            category=None,
        )
        pseudo_id = self.storage.create_entity(memory)
        return pseudo_id


def create_productivity_integration(
    chat_session: "ChatSession",
) -> Optional[ProductivityIntegration]:
    """
    Create a productivity integration instance for a chat session.

    Parameters
    ----------
    chat_session : ChatSession
        The chat session to integrate with

    Returns
    -------
    Optional[ProductivityIntegration]
        The integration instance, or None if productivity is disabled
    """
    try:
        # Check if vector store is available (required for productivity)
        if not chat_session.vector_store:
            chat_session.logger.warning(
                "Productivity disabled: vector store not available"
            )
            return None

        # Create productivity storage
        storage = ProductivityStorage(chat_session.vector_store)

        # Create and return integration
        integration = ProductivityIntegration(storage)

        chat_session.logger.info("Productivity integration enabled")
        return integration

    except Exception as e:
        chat_session.logger.error(f"Failed to initialize productivity integration: {e}")
        return None
