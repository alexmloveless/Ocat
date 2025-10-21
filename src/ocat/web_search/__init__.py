"""
Web search functionality for Ocat.

This module provides web search capabilities including:
- Search engine abstraction
- Content extraction from web pages
- Content processing and truncation
- Integration with chat system
"""

from .engine import SearchEngine
from .scraper import ContentScraper
from .processor import ContentProcessor
from .integration import WebSearchIntegration

__all__ = [
    "SearchEngine",
    "ContentScraper",
    "ContentProcessor",
    "WebSearchIntegration",
]
