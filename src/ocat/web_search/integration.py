"""
Integration module for web search functionality with the chat system.
"""

from typing import Optional, List, Dict, Any
import logging

from ..utils.logging import setup_logger, LogLevel
from .engine import SearchEngine
from .scraper import ContentScraper  
from .processor import ContentProcessor


class WebSearchIntegration:
    """Handles integration of web search with the chat system."""
    
    def __init__(self, config):
        """
        Initialize web search integration.
        
        Parameters
        ----------
        config : Config
            Configuration object
        """
        self.config = config
        self.logger = setup_logger(
            "ocat.web_search.integration", LogLevel[config.logging.level], config
        )
        
        # Initialize components
        self.search_engine = SearchEngine(config)
        self.content_scraper = ContentScraper(config)
        self.content_processor = ContentProcessor(config)
        
    async def perform_web_search(self, query: str, engine: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a complete web search with content extraction.
        
        Parameters
        ----------
        query : str
            Search query
        engine : Optional[str]
            Search engine to use
            
        Returns
        -------
        Dict[str, Any]
            Search results and metadata
        """
        try:
            # Step 1: Search
            search_results = await self.search_engine.search(query, engine)
            
            if not search_results:
                return {
                    "success": True,
                    "query": query,
                    "results": [],
                    "formatted_content": f"Web search for '{query}' found no results.",
                    "metadata": {
                        "total_found": 0,
                        "successful_scrapes": 0,
                        "engine": engine or self.config.web_search.default_engine
                    }
                }
                
            # Step 2: Scrape content
            urls = [result.url for result in search_results]
            page_contents = await self.content_scraper.scrape_urls(urls)
            
            # Step 3: Process content
            processed_content = self.content_processor.process_content(query, page_contents)
            
            return {
                "success": True,
                "query": query,
                "results": processed_content.results,
                "formatted_content": processed_content.format_for_context(),
                "metadata": {
                    "total_found": processed_content.total_found,
                    "successful_scrapes": processed_content.successful_scrapes,
                    "engine": engine or self.config.web_search.default_engine
                }
            }
            
        except Exception as e:
            self.logger.error(f"Web search integration failed: {e}")
            return {
                "success": False,
                "query": query,
                "results": [],
                "formatted_content": f"Web search for '{query}' failed: {e}",
                "metadata": {
                    "error": str(e),
                    "engine": engine or self.config.web_search.default_engine
                }
            }
    
    def create_search_context_prompt(self, original_prompt: str, search_results: str) -> str:
        """
        Create an enhanced prompt that includes search results.
        
        Parameters
        ----------
        original_prompt : str
            Original user prompt/query
        search_results : str
            Formatted search results content
            
        Returns
        -------
        str
            Enhanced prompt with search context
        """
        search_instruction = """

**Web Search Results:**
The following web search results have been provided to help answer your query. Please analyze the search results and provide a comprehensive response based on the available information. If the search results don't contain relevant information for the query, please state that clearly.

"""
        
        return original_prompt + search_instruction + search_results
