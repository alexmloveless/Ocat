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

        # Keywords that indicate productivity intent
        self.productivity_keywords = {
            # Task-related
            "task",
            "todo",
            "assignment",
            "work",
            "project",
            # Event-related
            "meeting",
            "event",
            "appointment",
            "schedule",
            "calendar",
            # Reminder-related
            "remind",
            "reminder",
            "alert",
            "notify",
            # Memory-related
            "remember",
            "memory",
            "note",
            "save",
            "store",
            # List-related
            "list",
            "item",
            "items",
            "shopping",
            "books",
            "travel",
            "archive",
            "bucket",
            # Actions
            "create",
            "add",
            "new",
            "make",
            "set",
            "schedule",
            "update",
            "edit",
            "change",
            "modify",
            "mark",
            "show",
            "list",
            "display",
            "find",
            "search",
            "delete",
            "remove",
            "cancel",
            "complete",
            "done",
        }

        # Phrases that strongly indicate productivity intent
        self.productivity_phrases = [
            r"\b(?:create|add|new|make)\s+(?:a\s+)?(?:task|todo|meeting|event|reminder|appointment|list|item)",
            r"\b(?:remind|alert|notify)\s+me\b",
            r"\b(?:remember|save|store)\s+(?:that|this|the)",
            r"\b(?:schedule|book)\s+(?:a\s+)?(?:meeting|appointment)",
            r"\b(?:mark|set)\s+(?:task|todo).*(?:complete|done)",
            r"\b(?:show|list|display)\s+(?:my\s+)?(?:tasks|todos|events|meetings|reminders|lists|items)",
            r"\b(?:what|when).*(?:due|deadline|scheduled)",
            r"\b(?:update|edit|change)\s+(?:task|event|reminder|item)",
            r"\bdue\s+(?:date|by|on|next|tomorrow)",
            r"\bnext\s+(?:week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"\btomorrow\s+at\b",
            r"\bin\s+(?:\d+\s+)?(?:minutes|hours|days|weeks)",
            r"\b(?:add|create).*(?:to|in)\s+(?:list|shopping|books|travel)",
            r"\b(?:archive|remove)\s+(?:item|list)",
            r"\bshow\s+(?:all\s+)?lists\b",
            r"\bitems?\s+in\s+(?:list|shopping|books)",
        ]

        # Compile regex patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.productivity_phrases
        ]

    def should_use_productivity_agent(self, user_input: str) -> bool:
        """
        Determine if the user input should be handled by the productivity agent.

        Parameters
        ----------
        user_input : str
            The user's input message

        Returns
        -------
        bool
            True if this should be handled by productivity agent
        """
        user_input_lower = user_input.lower()

        # Check for strong productivity phrase patterns
        for pattern in self.compiled_patterns:
            if pattern.search(user_input):
                return True

        # Check for productivity keywords (need multiple matches for confidence)
        keyword_matches = sum(
            1 for keyword in self.productivity_keywords if keyword in user_input_lower
        )

        # If multiple productivity keywords, likely a productivity request
        if keyword_matches >= 2:
            return True

        # Single keyword + time/date indicators = productivity request
        if keyword_matches >= 1:
            time_indicators = [
                "tomorrow",
                "today",
                "tonight",
                "morning",
                "afternoon",
                "evening",
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                "next",
                "this",
                "at",
                "by",
                "due",
                "deadline",
                "o'clock",
                "pm",
                "am",
                "week",
                "month",
                "day",
                "hour",
                "minute",
            ]

            if any(indicator in user_input_lower for indicator in time_indicators):
                return True

        return False

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
