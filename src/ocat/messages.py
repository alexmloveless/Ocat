"""
Message classes for Ocat chat functionality.

Contains message data structures to avoid circular imports.
"""

from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class Message:
    """
    Represents a single message in the chat conversation.

    Attributes
    ----------
    role : str
        Role of the message sender ("user", "assistant", "system")
    content : str
        Content of the message
    timestamp : float
        Unix timestamp when message was created
    """

    role: str
    content: str
    timestamp: Optional[float] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = time.time()
