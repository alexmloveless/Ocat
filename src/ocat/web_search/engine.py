"""
Search engine abstraction for web search functionality.
"""

import asyncio
import aiohttp
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import logging

from ..utils.logging import setup_logger, LogLevel


class SearchResult:
    """Represents a single search result."""

    def __init__(self, title: str, url: str, snippet: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet

    def __repr__(self):
        return f"SearchResult(title='{self.title}', url='{self.url}')"


class SearchEngine:
    """Abstraction for different search engines."""

    def __init__(self, config):
        """
        Initialize search engine.

        Parameters
        ----------
        config : Config
            Configuration object containing web_search settings
        """
        self.config = config
        self.web_config = config.web_search
        self.timeout = self.web_config.timeout
        self.logger = setup_logger(
            "ocat.web_search.engine", LogLevel[config.logging.level], config
        )

    async def search(
        self,
        query: str,
        engine: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[SearchResult]:
        """
        Perform a web search.

        Parameters
        ----------
        query : str
            Search query
        engine : Optional[str]
            Search engine to use (defaults to configured default)
        max_results : Optional[int]
            Maximum number of results (defaults to configured max)

        Returns
        -------
        List[SearchResult]
            List of search results
        """
        if not self.web_config.enabled:
            self.logger.warning("Web search is disabled")
            return []

        engine = engine or self.web_config.default_engine
        max_results = max_results or self.web_config.max_results

        if engine not in self.web_config.engines:
            available = ", ".join(self.web_config.engines.keys())
            self.logger.error(
                f"Unknown search engine: {engine}. Available: {available}"
            )
            return []

        self.logger.info(f"Searching '{query}' using {engine}")

        try:
            if engine == "duckduckgo":
                return await self._search_duckduckgo(query, max_results)
            elif engine == "google":
                return await self._search_google(query, max_results)
            elif engine == "bing":
                return await self._search_bing(query, max_results)
            else:
                self.logger.error(f"Search engine {engine} not implemented")
                return []

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    async def _search_duckduckgo(
        self, query: str, max_results: int
    ) -> List[SearchResult]:
        """Search using DuckDuckGo."""
        search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            async with session.get(search_url, headers=headers) as response:
                if response.status != 200:
                    self.logger.error(
                        f"DuckDuckGo search failed with status {response.status}"
                    )
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                results = []
                result_elements = soup.find_all("div", class_="result")[:max_results]

                for element in result_elements:
                    title_elem = element.find("a", class_="result__a")
                    snippet_elem = element.find("a", class_="result__snippet")

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get("href", "")
                        snippet = (
                            snippet_elem.get_text(strip=True) if snippet_elem else ""
                        )

                        # Clean up URL (DuckDuckGo sometimes uses redirects)
                        if url.startswith("/l/?uddg="):
                            url = url.split("uddg=")[1] if "uddg=" in url else url

                        if title and url:
                            results.append(SearchResult(title, url, snippet))

                self.logger.info(f"Found {len(results)} DuckDuckGo results")
                return results

    async def _search_google(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Google (simplified - may be blocked)."""
        # Note: This is a basic implementation that may be blocked by Google
        # In production, you'd want to use Google Custom Search API
        search_url = (
            f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
        )

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            async with session.get(search_url, headers=headers) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"Google search failed with status {response.status}"
                    )
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                results = []
                # Google's HTML structure changes frequently
                result_elements = soup.find_all("div", class_="g")[:max_results]

                for element in result_elements:
                    title_elem = element.find("h3")
                    link_elem = element.find("a")
                    snippet_elem = element.find("span", {"data-ved": True})

                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get("href", "")
                        snippet = (
                            snippet_elem.get_text(strip=True) if snippet_elem else ""
                        )

                        if title and url and url.startswith("http"):
                            results.append(SearchResult(title, url, snippet))

                self.logger.info(f"Found {len(results)} Google results")
                return results

    async def _search_bing(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Bing."""
        search_url = (
            f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
        )

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            async with session.get(search_url, headers=headers) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"Bing search failed with status {response.status}"
                    )
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                results = []
                result_elements = soup.find_all("li", class_="b_algo")[:max_results]

                for element in result_elements:
                    title_elem = element.find("h2")
                    link_elem = title_elem.find("a") if title_elem else None
                    snippet_elem = element.find("p")

                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get("href", "")
                        snippet = (
                            snippet_elem.get_text(strip=True) if snippet_elem else ""
                        )

                        if title and url:
                            results.append(SearchResult(title, url, snippet))

                self.logger.info(f"Found {len(results)} Bing results")
                return results
