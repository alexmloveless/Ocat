"""
Content processor for filtering and formatting scraped content.
"""

from typing import List, Dict, Any
import re
import logging

from ..utils.logging import setup_logger, LogLevel
from .scraper import PageContent


class ProcessedContent:
    """Represents processed and formatted content for the chat system."""

    def __init__(
        self,
        query: str,
        results: List[Dict[str, Any]],
        total_found: int,
        successful_scrapes: int,
    ):
        self.query = query
        self.results = results  # List of {title, url, content, word_count}
        self.total_found = total_found
        self.successful_scrapes = successful_scrapes

    def format_for_context(self) -> str:
        """
        Format the processed content for inclusion in chat context.

        Returns
        -------
        str
            Formatted content ready for the chat system
        """
        if not self.results:
            return f"Web search for '{self.query}' found no relevant content."

        content_parts = [f"Web search results for '{self.query}':"]

        for i, result in enumerate(self.results, 1):
            title = result["title"]
            url = result["url"]
            content = result["content"]

            content_parts.append(f"\n{i}. **{title}**")
            content_parts.append(f"   Source: {url}")
            content_parts.append(f"   Content: {content}")

        summary = f"\n\nSearch summary: Found {self.total_found} results, successfully processed {self.successful_scrapes}."
        content_parts.append(summary)

        return "\n".join(content_parts)

    def __repr__(self):
        return f"ProcessedContent(query='{self.query}', results={len(self.results)})"


class ContentProcessor:
    """Processes and formats scraped content for chat integration."""

    def __init__(self, config):
        """
        Initialize content processor.

        Parameters
        ----------
        config : Config
            Configuration object containing web_search settings
        """
        self.config = config
        self.web_config = config.web_search
        self.content_threshold = self.web_config.content_threshold
        self.logger = setup_logger(
            "ocat.web_search.processor", LogLevel[config.logging.level], config
        )

    def process_content(
        self, query: str, page_contents: List[PageContent]
    ) -> ProcessedContent:
        """
        Process scraped page content for chat integration.

        Parameters
        ----------
        query : str
            Original search query
        page_contents : List[PageContent]
            List of scraped page contents

        Returns
        -------
        ProcessedContent
            Processed and formatted content
        """
        if not page_contents:
            return ProcessedContent(query, [], 0, 0)

        successful_contents = [
            pc for pc in page_contents if pc.success and pc.text.strip()
        ]
        self.logger.info(
            f"Processing {len(successful_contents)} successful page scrapes"
        )

        results = []
        for page_content in successful_contents:
            processed_text = self._process_text(page_content.text)
            if (
                processed_text
            ):  # Only include if there's meaningful content after processing
                results.append(
                    {
                        "title": page_content.title or "Untitled",
                        "url": page_content.url,
                        "content": processed_text,
                        "word_count": len(processed_text.split()),
                    }
                )

        return ProcessedContent(
            query=query,
            results=results,
            total_found=len(page_contents),
            successful_scrapes=len(successful_contents),
        )

    def _process_text(self, text: str) -> str:
        """
        Process and truncate text content.

        Parameters
        ----------
        text : str
            Raw text content

        Returns
        -------
        str
            Processed and potentially truncated text
        """
        if not text:
            return ""

        # Clean up text
        text = self._clean_text(text)

        # Check if truncation is needed
        words = text.split()
        if len(words) <= self.content_threshold:
            return text

        # Truncate to threshold
        truncated_words = words[: self.content_threshold]
        truncated_text = " ".join(truncated_words)

        # Try to end at a sentence boundary near the threshold
        sentences = self._split_sentences(truncated_text)
        if len(sentences) > 1:
            # Remove the last incomplete sentence if it looks cut off
            last_sentence = sentences[-1].strip()
            if not last_sentence.endswith((".", "!", "?", ":", ";")):
                truncated_text = " ".join(sentences[:-1])

        self.logger.debug(
            f"Truncated content from {len(words)} to ~{len(truncated_text.split())} words"
        )

        return (
            truncated_text + "..."
            if len(words) > self.content_threshold
            else truncated_text
        )

    def _clean_text(self, text: str) -> str:
        """
        Clean up text content.

        Parameters
        ----------
        text : str
            Raw text

        Returns
        -------
        str
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common navigation and boilerplate text
        patterns_to_remove = [
            r"\b(cookie|privacy policy|terms of service|subscribe|newsletter|advertisement)\b",
            r"\b(click here|read more|continue reading|learn more)\b",
            r"\b(share|tweet|facebook|linkedin|instagram)\b",
            r"\b(copyright|all rights reserved|\©|\®)\b",
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Remove excessive punctuation
        text = re.sub(r'[^\w\s.,!?;:\-()"\'/]', " ", text)

        # Clean up spacing again after removals
        text = " ".join(text.split())

        return text.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Parameters
        ----------
        text : str
            Text to split

        Returns
        -------
        List[str]
            List of sentences
        """
        # Simple sentence splitting - could be improved with NLTK
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]
