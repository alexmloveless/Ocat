"""
Memory suggester module for Ocat.

Detects facts that are good candidates for long-term memory,
checks if they (or something very similar) are already stored,
and provides a cleaned fact string to be stored.
"""

import re
from typing import Optional
from .storage import ProductivityStorage
from .models import Memory, EntityType


# Regex patterns for detecting personal facts
PERSONAL_FACT_RE = re.compile(
    r"\b(?:I|my|mine)\b.+?\b(?:is|am|are|was|were|have|work|live|like|love|enjoy|prefer|hate|dislike)\b\s+(.{3,120})",
    re.IGNORECASE,
)
QUESTION_RE = re.compile(r"\?$")


class MemorySuggester:
    """
    Detect facts that are good candidates for long-term memory,
    check if they (or something very similar) are already stored,
    and give back a cleaned fact string to be stored.
    """

    def __init__(self, storage: ProductivityStorage):
        """
        Initialize the memory suggester.

        Parameters
        ----------
        storage : ProductivityStorage
            The productivity storage instance for searching existing memories
        """
        self.storage = storage

    def extract_fact(self, user_msg: str) -> Optional[str]:
        """
        Extract a personal fact from a user message.

        Parameters
        ----------
        user_msg : str
            The user's message to analyze

        Returns
        -------
        Optional[str]
            Extracted fact if found, None otherwise
        """
        # Don't store questions
        if QUESTION_RE.search(user_msg):
            return None

        # Look for personal fact patterns
        match = PERSONAL_FACT_RE.search(user_msg)
        if not match:
            return None

        fact = match.group(1).strip(" .")

        # Filter out facts that are too short to be meaningful
        if len(fact.split()) < 2:
            return None

        return fact

    def is_duplicate(self, fact: str) -> bool:
        """
        Check if a similar fact is already stored in memories.

        Parameters
        ----------
        fact : str
            The fact to check for duplicates

        Returns
        -------
        bool
            True if a similar fact already exists, False otherwise
        """
        hits = self.storage.search_entities(
            query=fact,
            entity_types=[EntityType.MEMORY],
            limit=3,
        )
        return len(hits) > 0

    def should_suggest(self, user_msg: str) -> Optional[str]:
        """
        Determine if we should suggest storing a fact from the user message.

        Parameters
        ----------
        user_msg : str
            The user's message to analyze

        Returns
        -------
        Optional[str]
            The fact to suggest storing, or None if no suggestion should be made
        """
        fact = self.extract_fact(user_msg)
        if not fact:
            return None

        if self.is_duplicate(fact):
            return None

        return fact
