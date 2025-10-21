"""
Tests for web search functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from bs4 import BeautifulSoup

from src.ocat.web_search.engine import SearchEngine, SearchResult
from src.ocat.web_search.scraper import ContentScraper, PageContent
from src.ocat.web_search.processor import ContentProcessor
from src.ocat.config import Config


class TestSearchEngine:
    """Tests for SearchEngine class."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
        config = Config()
        config.web_search.enabled = True
        config.web_search.timeout = 5
        config.web_search.max_results = 3
        return config

    @pytest.fixture
    def search_engine(self, config):
        """Create a SearchEngine instance."""
        return SearchEngine(config)

    def test_init(self, search_engine, config):
        """Test SearchEngine initialization."""
        assert search_engine.config == config
        assert search_engine.timeout == 5
        assert search_engine.web_config == config.web_search

    @pytest.mark.asyncio
    async def test_search_disabled(self, search_engine):
        """Test search returns empty when disabled."""
        search_engine.web_config.enabled = False
        results = await search_engine.search("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_unknown_engine(self, search_engine):
        """Test search with unknown engine returns empty."""
        results = await search_engine.search("test", engine="unknown")
        assert results == []


class TestContentScraper:
    """Tests for ContentScraper class."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
        return Config()

    @pytest.fixture
    def scraper(self, config):
        """Create a ContentScraper instance."""
        return ContentScraper(config)

    def test_init(self, scraper, config):
        """Test ContentScraper initialization."""
        assert scraper.config == config
        assert scraper.timeout == config.web_search.timeout

    def test_is_html_url(self, scraper):
        """Test HTML URL detection."""
        assert scraper._is_html_url("https://example.com/page.html")
        assert scraper._is_html_url("https://example.com/")
        assert scraper._is_html_url("https://example.com/article")

        assert not scraper._is_html_url("https://example.com/file.pdf")
        assert not scraper._is_html_url("https://example.com/image.jpg")
        assert not scraper._is_html_url("https://example.com/video.mp4")

    def test_extract_content(self, scraper):
        """Test content extraction from HTML."""
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <script>console.log('test');</script>
            <style>.hidden { display: none; }</style>
            <main>
                <h1>Main Content</h1>
                <p>This is the main content of the page.</p>
            </main>
            <nav>Navigation</nav>
            <footer>Footer content</footer>
        </body>
        </html>
        """

        result = scraper._extract_content("https://example.com", html)

        assert result.success
        assert result.title == "Test Page"
        assert "Main Content" in result.text
        assert "main content of the page" in result.text
        assert "console.log" not in result.text
        assert "Navigation" not in result.text
        assert "Footer content" not in result.text


class TestContentProcessor:
    """Tests for ContentProcessor class."""

    @pytest.fixture
    def config(self):
        """Create a test config."""
        config = Config()
        config.web_search.content_threshold = 10  # Small threshold for testing
        return config

    @pytest.fixture
    def processor(self, config):
        """Create a ContentProcessor instance."""
        return ContentProcessor(config)

    def test_init(self, processor, config):
        """Test ContentProcessor initialization."""
        assert processor.config == config
        assert processor.content_threshold == 10

    def test_clean_text(self, processor):
        """Test text cleaning."""
        text = "This is a test    with   extra  spaces and   \n\n  newlines."
        cleaned = processor._clean_text(text)
        assert cleaned == "This is a test with extra spaces and newlines."

    def test_process_text_no_truncation(self, processor):
        """Test text processing without truncation."""
        text = "Short text here"
        processed = processor._process_text(text)
        assert processed == text

    def test_process_text_with_truncation(self, processor):
        """Test text processing with truncation."""
        words = ["word"] * 15  # 15 words, threshold is 10
        text = " ".join(words)

        processed = processor._process_text(text)
        processed_words = processed.replace("...", "").split()

        assert len(processed_words) <= 10
        assert processed.endswith("...")

    def test_process_content(self, processor):
        """Test full content processing."""
        page_contents = [
            PageContent("url1", "Title 1", "Content for page one", True),
            PageContent("url2", "Title 2", "Content for page two", True),
            PageContent("url3", "", "", False, "Error loading"),
        ]

        result = processor.process_content("test query", page_contents)

        assert result.query == "test query"
        assert len(result.results) == 2  # Only successful pages
        assert result.total_found == 3
        assert result.successful_scrapes == 2

        # Check formatted content
        formatted = result.format_for_context()
        assert "test query" in formatted
        assert "Title 1" in formatted
        assert "Title 2" in formatted


class TestWebSearchConfig:
    """Tests for web search configuration."""

    def test_default_config(self):
        """Test default web search configuration."""
        config = Config()

        assert config.web_search.enabled is True
        assert config.web_search.default_engine == "duckduckgo"
        assert config.web_search.content_threshold == 500
        assert config.web_search.max_results == 3
        assert config.web_search.timeout == 10
        assert "google" in config.web_search.engines
        assert "bing" in config.web_search.engines
        assert "duckduckgo" in config.web_search.engines

    def test_config_validation(self):
        """Test configuration validation."""
        from src.ocat.config import WebSearchConfig

        # Test valid config
        config = WebSearchConfig()
        assert config.default_engine in config.engines

        # Test invalid default engine
        with pytest.raises(ValueError):
            WebSearchConfig(
                default_engine="nonexistent", engines={"google": "url", "bing": "url"}
            )


if __name__ == "__main__":
    pytest.main([__file__])
