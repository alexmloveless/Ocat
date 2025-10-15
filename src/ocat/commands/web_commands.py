"""
Web search slash commands for Ocat.
"""

from typing import List, Any
import logging

from . import Command, CommandResult, CommandError, register_command
from ..web_search import SearchEngine, ContentScraper, ContentProcessor
from ..utils.logging import setup_logger, LogLevel


@register_command("web")
class WebSearchCommand(Command):
    """Web search command that fetches and processes search results."""
    
    name = "web"
    description = "Search the web and retrieve content from results"
    usage = '/web "search query" [search_engine]'
    
    def __init__(self, config):
        """
        Initialize web search command.
        
        Parameters
        ----------
        config : Config
            Configuration object
        """
        self.config = config
        self.logger = setup_logger(
            "ocat.commands.web", LogLevel[config.logging.level], config
        )
        
        # Initialize web search components
        self.search_engine = SearchEngine(config)
        self.content_scraper = ContentScraper(config)
        self.content_processor = ContentProcessor(config)
        
    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute web search command.
        
        Parameters
        ----------
        args : List[str]
            Command arguments
        context : Any
            Chat session context
            
        Returns
        -------
        CommandResult
            Command execution result
        """
        try:
            # Check if web search is enabled
            if not self.config.web_search.enabled:
                return CommandResult.error("Web search is disabled")
                
            # Parse arguments
            if not args:
                return CommandResult.error("Usage: /web \"search query\" [search_engine]")
                
            query = args[0]
            search_engine = args[1] if len(args) > 1 else None
            
            if not query.strip():
                return CommandResult.error("Search query cannot be empty")
                
            self.logger.info(f"Executing web search for: '{query}'")
            
            # Step 1: Perform search
            search_results = await self.search_engine.search(query, search_engine)
            
            if not search_results:
                return CommandResult.success(
                    f"No search results found for '{query}'",
                    data={"search_results": None}
                )
                
            # Step 2: Extract URLs for scraping
            urls = [result.url for result in search_results]
            self.logger.info(f"Found {len(urls)} search results, scraping content...")
            
            # Step 3: Scrape content from URLs
            page_contents = await self.content_scraper.scrape_urls(urls)
            
            # Step 4: Process and format content
            processed_content = self.content_processor.process_content(query, page_contents)
            
            # Step 5: Prepare result
            if processed_content.results:
                # Add processed content to context for the chat system
                formatted_content = processed_content.format_for_context()
                
                # Add to context so it's included in the next LLM request
                if hasattr(context, 'add_search_context'):
                    context.add_search_context(formatted_content)
                else:
                    # Fallback: store in context for manual handling
                    if not hasattr(context, 'web_search_results'):
                        context.web_search_results = []
                    context.web_search_results.append(formatted_content)
                
                success_msg = (f"Found {len(processed_content.results)} results for '{query}'. "
                             f"Content added to conversation context.")
                
                return CommandResult.success(
                    success_msg,
                    data={
                        "search_results": processed_content.results,
                        "formatted_content": formatted_content
                    }
                )
            else:
                return CommandResult.success(
                    f"Search completed but no relevant content found for '{query}'",
                    data={"search_results": None}
                )
                
        except Exception as e:
            self.logger.error(f"Web search command failed: {e}")
            return CommandResult.error(f"Web search failed: {e}")
