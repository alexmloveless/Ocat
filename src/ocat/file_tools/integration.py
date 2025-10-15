"""
Integration layer for file operation tools with the chat system.

Detects file operation intent and routes to pydantic-ai file agent.
"""

import re
from typing import Optional, Any
from pathlib import Path

from ..utils.logging import setup_logger, LogLevel
from .tools import file_agent, create_file_integration


class FileIntegration:
    """Integration between chat system and file operation tools."""

    def __init__(self, config, current_directory: Path):
        """
        Initialize file integration.

        Parameters
        ----------
        config : Config
            Ocat configuration
        current_directory : Path
            Current working directory
        """
        self.config = config
        self.current_directory = current_directory
        self.logger = setup_logger(
            "ocat.file_tools", LogLevel[config.logging.level], config
        )

        # Create file storage for tools
        self.file_storage = create_file_integration(config, current_directory)

        # File operation detection patterns
        self.file_patterns = [
            # Read operations
            r"\b(read|show|display|open|cat|view)\s+(?:the\s+)?(?:file\s+)?([^\s]+\.[a-zA-Z0-9]+)",
            r"\b(read|show|display|open|cat|view)\s+([a-zA-Z0-9_.-]+:[^\s]+)",  # location aliases
            r"\bwhat(?:\'s|s)?\s+in\s+(?:the\s+)?(?:file\s+)?([^\s]+\.[a-zA-Z0-9]+)",
            # Write operations
            r"\b(write|save|create)\s+(?:to\s+)?(?:the\s+)?(?:file\s+)?([^\s]+\.[a-zA-Z0-9]+)",
            r"\b(write|save|create)\s+(?:to\s+)?([a-zA-Z0-9_.-]+:[^\s]+)",
            # List operations
            r"\b(list|ls|show)\s+(?:the\s+)?(?:contents?\s+of\s+)?(?:directory\s+)?([^\s]+/?)",
            r"\bwhat(?:\'s|s)?\s+in\s+(?:the\s+)?(?:directory\s+)?([^\s]+/?)",
            r"\bshow\s+(?:me\s+)?(?:the\s+)?(?:directory\s+)?([^\s]+/?)",
            # Search operations
            r"\b(search|find|look\s+for)\s+([^\s]+)(?:\s+in\s+([^\s]+))?",
            # Tree operations
            r"\b(tree|structure|hierarchy)\s+(?:of\s+)?(?:the\s+)?(?:directory\s+)?([^\s]*)",
        ]

        # Compile patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.file_patterns
        ]

    def detect_file_intent(self, message: str, routing_marker: str = "@") -> bool:
        """
        Detect if a message should be routed to file operations.
        Now uses explicit marker-based routing instead of keyword detection.

        Parameters
        ----------
        message : str
            User message to analyze
        routing_marker : str
            The marker symbol that must prefix file operation messages

        Returns
        -------
        bool
            True if file operation intent detected (starts with routing marker)
        """
        # Check if the input starts with the routing marker
        stripped_input = message.strip()
        return stripped_input.startswith(routing_marker)

    async def handle_file_request(self, message: str) -> Optional[str]:
        """
        Handle file operation request using pydantic-ai agent.

        Parameters
        ----------
        message : str
            User message requesting file operation

        Returns
        -------
        Optional[str]
            Response from file agent, or None if failed
        """
        try:
            self.logger.debug(f"Processing file request: {message}")

            # Update current directory in file storage
            self.file_storage.context.current_directory = self.current_directory

            # Run the file agent with the user's request
            result = await file_agent.run(message, deps=self.file_storage)

            self.logger.debug("File operation completed successfully")
            return result.data

        except Exception as e:
            self.logger.error(f"File operation failed: {e}")
            return f"Sorry, I couldn't complete that file operation: {str(e)}"

    def update_current_directory(self, new_directory: Path):
        """
        Update the current working directory.

        Parameters
        ----------
        new_directory : Path
            New current directory
        """
        self.current_directory = new_directory
        self.file_storage.context.current_directory = new_directory
        self.logger.debug(f"Updated current directory to: {new_directory}")


def create_file_integration_for_session(
    config, current_directory: Path
) -> FileIntegration:
    """
    Create a FileIntegration instance for a chat session.

    Parameters
    ----------
    config : Config
        Ocat configuration
    current_directory : Path
        Current working directory

    Returns
    -------
    FileIntegration
        Configured file integration instance
    """
    return FileIntegration(config, current_directory)
