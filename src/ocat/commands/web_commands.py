"""
Web search slash commands for Ocat.
"""

from typing import List, Any
import logging

from . import command, BaseCommand, CommandResult, CommandError
from ..web_search import SearchEngine, ContentScraper, ContentProcessor
from ..utils.logging import setup_logger, LogLevel
from rich.panel import Panel


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


@command(
    name="url",
    description="Attach content from a single URL to the chat",
    usage="/url <url>",
)
class UrlCommand(BaseCommand):
    """Command to fetch and attach content from a single URL."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the URL command.

        Parameters
        ----------
        args : List[str]
            List containing the URL to fetch
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error("No URL specified. Usage: /url <url>")

        if len(args) > 1:
            return CommandResult.error("Only one URL can be processed at a time.")

        url = args[0].strip()

        # Basic URL validation
        if not (url.startswith("http://") or url.startswith("https://")):
            return CommandResult.error("URL must start with http:// or https://")

        try:
            # Get config from context
            config = context.config

            # Initialize components
            logger = setup_logger(
                "ocat.commands.url", LogLevel[config.logging.level], config
            )
            content_scraper = ContentScraper(config)

            logger.info(f"Fetching content from URL: {url}")

            # Scrape content from the URL
            page_content = await content_scraper.scrape_url(url)

            if not page_content.success:
                return CommandResult.error(
                    f"Failed to fetch content from {url}: {page_content.error or 'Unknown error'}"
                )

            # Create content with header like the attach command
            title = page_content.title if page_content.title else "Untitled"
            content_header = f"\n--- URL: {title} ({url}) ---\n"
            combined_content = content_header + page_content.text

            # Add as user message to the conversation
            from ..chat import Message

            url_message = Message(
                role="user", content=f"[URL Content]\n{combined_content}"
            )
            context.messages.append(url_message)

            # Display confirmation
            context.console.print(
                Panel(
                    f"URL content attached successfully:\n  • {title}\n  • {url}",
                    title="URL Attached",
                    border_style="green",
                )
            )

            # Ask if user wants to add to vector store (same as attach command) - skip in dummy mode
            if (
                hasattr(context, "vector_store")
                and context.vector_store
                and context.config.vector_store.enabled
                and not getattr(context, "dummy_mode", False)
            ):
                try:
                    # Ask user if they want to add to vector store
                    context.console.print(
                        "\n[yellow]Would you like to also add this URL content to the vector store for future reference? (y/n)[/yellow]"
                    )

                    # Get user response
                    response = input().lower().strip()

                    if response in ["y", "yes"]:
                        # Add URL content to vector store
                        thread_id = getattr(context, "thread_id", "url_session")
                        session_id = getattr(context, "session_id", "url_session")

                        try:
                            # Add URL content to vector store as document
                            exchange_ids = context.vector_store.add_document(
                                text=page_content.text,
                                thread_id=thread_id,
                                session_id=session_id,
                                source_file=url,  # Use URL as source file
                                metadata={
                                    "source": "url_command",
                                    "url": url,
                                    "title": title,
                                    "attached_in_session": session_id,
                                    "attached_in_thread": thread_id,
                                },
                            )

                            context.console.print(
                                f"[green]✅ Added URL content to vector store as {len(exchange_ids)} chunk(s)[/green]"
                            )

                        except Exception as e:
                            context.console.print(
                                f"[red]Warning: Could not add URL content to vector store: {e}[/red]"
                            )

                except KeyboardInterrupt:
                    context.console.print(
                        "\n[yellow]Skipped adding to vector store[/yellow]"
                    )
                except Exception as e:
                    context.console.print(
                        f"[red]Error with vector store prompt: {e}[/red]"
                    )

            return CommandResult.ok(f"Attached content from {url} to conversation.")

        except Exception as e:
            try:
                logger.error(f"URL command failed: {e}")
            except:
                pass  # Ignore logging errors in error handler
            return CommandResult.error(f"Failed to fetch URL content: {e}")
