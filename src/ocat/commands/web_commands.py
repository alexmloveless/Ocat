"""
Web search slash commands for Ocat.
"""

from typing import List, Any
import logging

from . import command, BaseCommand, CommandResult, CommandError
from ..web_search import SearchEngine, ContentScraper, ContentProcessor
from ..utils.logging import setup_logger, LogLevel


@command(
    name="web",
    description="Search the web and retrieve content from results",
    usage='/web "search query" [search_engine]',
)
class WebSearchCommand(BaseCommand):
    """Web search command that fetches and processes search results."""

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
            # Get config from context
            config = context.config

            # Check if web search is enabled
            if not config.web_search.enabled:
                return CommandResult.error("Web search is disabled")

            # Initialize components
            logger = setup_logger(
                "ocat.commands.web", LogLevel[config.logging.level], config
            )
            search_engine = SearchEngine(config)
            content_scraper = ContentScraper(config)
            content_processor = ContentProcessor(config)

            # Parse arguments
            if not args:
                return CommandResult.error('Usage: /web "search query" [search_engine]')

            query = args[0]
            engine = args[1] if len(args) > 1 else None

            if not query.strip():
                return CommandResult.error("Search query cannot be empty")

            logger.info(f"Executing web search for: '{query}'")

            # Step 1: Perform search
            search_results = await search_engine.search(query, engine)

            if not search_results:
                return CommandResult.ok(f"No search results found for '{query}'")

            # Step 2: Extract URLs for scraping
            urls = [result.url for result in search_results]
            logger.info(f"Found {len(urls)} search results, scraping content...")

            # Step 3: Scrape content from URLs
            page_contents = await content_scraper.scrape_urls(urls)

            # Step 4: Process and format content
            processed_content = content_processor.process_content(query, page_contents)

            # Step 5: Prepare result
            if processed_content.results:
                # Add processed content to context for the chat system
                formatted_content = processed_content.format_for_context()

                # Add to context so it's included in the next LLM request
                if hasattr(context, "add_search_context"):
                    context.add_search_context(formatted_content)
                else:
                    # Fallback: store in context for manual handling
                    if not hasattr(context, "web_search_results"):
                        context.web_search_results = []
                    context.web_search_results.append(formatted_content)

                success_msg = (
                    f"Found {len(processed_content.results)} results for '{query}'. "
                    f"Content added to conversation context."
                )

                return CommandResult.ok(
                    success_msg,
                    data={
                        "search_results": processed_content.results,
                        "formatted_content": formatted_content,
                    },
                )
            else:
                return CommandResult.ok(
                    f"Search completed but no relevant content found for '{query}'"
                )

        except Exception as e:
            # Create a fallback logger if initialization failed
            try:
                config = context.config
                logger = setup_logger(
                    "ocat.commands.web", LogLevel[config.logging.level], config
                )
                logger.error(f"Web search command failed: {e}")
            except:
                pass  # Ignore logging errors in error handler
            return CommandResult.error(f"Web search failed: {e}")
