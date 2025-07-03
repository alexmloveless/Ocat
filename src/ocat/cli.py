"""
CLI module for Ocat - Interactive LLM Chat CLI tool.

This module provides the main command-line interface for the Ocat application,
handling user input, command parsing, and interaction coordination.
"""

# Disable ChromaDB telemetry before any imports to prevent telemetry errors
import os

os.environ["ANONYMIZED_TELEMETRY"] = "False"
# Disable tokenizers parallelism to prevent fork warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import argparse
from typing import Optional, List
import logging
import asyncio

from .utils.logging import setup_logger, LogLevel

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings

from . import __version__
from .chat import ChatSession
from .config import Config


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for Ocat CLI.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="ocat",
        description="An interactive LLM Chat CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=f"ocat {__version__}")

    # Configuration file
    parser.add_argument("--config", type=str, help="Path to configuration file")

    # Model configuration overrides
    parser.add_argument("--model", type=str, help="LLM model to use for chat")

    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature setting for model responses (0.0-1.0)",
    )

    parser.add_argument("--max-tokens", type=int, help="Maximum tokens for responses")

    # Vector store configuration overrides
    parser.add_argument(
        "--vector-store-path", type=str, help="Path to vector store directory"
    )

    parser.add_argument(
        "--no-vector-store",
        action="store_true",
        help="Disable vector store functionality",
    )

    parser.add_argument(
        "--similarity-threshold",
        type=float,
        help="Vector similarity threshold (0.0-1.0)",
    )

    # Logging configuration overrides
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        help="Set logging level",
    )

    # Display configuration overrides
    parser.add_argument(
        "--no-rich", action="store_true", help="Disable rich text formatting"
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color output"
    )

    parser.add_argument("--line-width", type=int, help="CLI line width in characters")

    # Profile name override
    parser.add_argument("--profile", type=str, help="Configuration profile name")

    # Special modes
    parser.add_argument(
        "--dummy-mode",
        action="store_true",
        help="Use dummy responses for testing (no real LLM calls)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed error traces",
    )

    # Headless mode options for vector store operations
    headless_group = parser.add_argument_group(
        "headless mode", "Non-interactive operations for automation"
    )

    headless_group.add_argument(
        "--add-to-vector-store",
        type=str,
        help="Add text document to vector store and exit",
    )

    headless_group.add_argument(
        "--query-vector-store", type=str, help="Query vector store and exit"
    )

    headless_group.add_argument(
        "--vector-store-stats",
        action="store_true",
        help="Display vector store statistics and exit",
    )

    return parser


def display_welcome(console: Console, config: Optional[Config] = None) -> None:
    """
    Display welcome message and basic instructions.

    Parameters
    ----------
    console : Console
        Rich console instance for output
    config : Optional[Config]
        Configuration instance to show model and profile info
    """
    # Create welcome message as specified in bootstrap
    welcome_lines = [
        "Welcome to Ocat - Otherworldy Chats at (the) Terminal",
        "Type your messages to chat with the LLM.",
        "Type /help to see available commands.",
        "Type /exit to quit the application.",
    ]

    # Add model and profile information if config is available
    if config:
        welcome_lines.append(f"Model: {config.llm.model}")
        if config.profile_name:
            welcome_lines.append(f"Profile: {config.profile_name}")

    # Create panel with proper width consideration
    welcome_content = "\n".join(welcome_lines)

    # Use line width from config if available, otherwise default to 70
    panel_width = config.display.line_width - 4 if config else 70

    panel = Panel(
        welcome_content,
        title="🐱 Ocat",
        border_style="bright_blue",
        width=min(panel_width, 76),  # Max width for readability
        padding=(1, 2),
    )

    console.print(panel)
    console.print()


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the Ocat CLI application.

    Parameters
    ----------
    args : Optional[List[str]]
        Command line arguments (defaults to sys.argv if None)

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Initialize console for rich output
    console = Console()

    try:
        # Extract CLI overrides from parsed arguments
        cli_overrides = {}

        # Model configuration overrides
        if parsed_args.model:
            cli_overrides["model"] = parsed_args.model
        if parsed_args.temperature is not None:
            cli_overrides["temperature"] = parsed_args.temperature
        if getattr(parsed_args, "max_tokens", None) is not None:
            cli_overrides["max_tokens"] = parsed_args.max_tokens

        # Vector store configuration overrides
        if getattr(parsed_args, "vector_store_path", None):
            cli_overrides["vector_store_path"] = parsed_args.vector_store_path
        if getattr(parsed_args, "no_vector_store", False):
            cli_overrides["no_vector_store"] = True
        if getattr(parsed_args, "similarity_threshold", None) is not None:
            cli_overrides["similarity_threshold"] = parsed_args.similarity_threshold

        # Logging configuration overrides
        if getattr(parsed_args, "log_level", None):
            cli_overrides["log_level"] = parsed_args.log_level

        # Display configuration overrides
        if getattr(parsed_args, "no_rich", False):
            cli_overrides["no_rich"] = True
        if getattr(parsed_args, "no_color", False):
            cli_overrides["no_color"] = True
        if getattr(parsed_args, "line_width", None) is not None:
            cli_overrides["line_width"] = parsed_args.line_width

        # Profile name override
        if getattr(parsed_args, "profile", None):
            cli_overrides["profile"] = parsed_args.profile

        # Load configuration with CLI overrides
        config = Config.load(
            parsed_args.config, cli_overrides if cli_overrides else None
        )

        # Set up logging after config is loaded
        logger = setup_logger("ocat.cli", LogLevel[config.logging.level], config)
        logger.info(f"Starting Ocat CLI with model: {config.llm.model}")

        # Handle headless mode operations
        if (
            hasattr(parsed_args, "add_to_vector_store")
            and parsed_args.add_to_vector_store
        ):
            return handle_headless_add_to_vector_store(
                parsed_args.add_to_vector_store, config, console
            )
        elif (
            hasattr(parsed_args, "query_vector_store")
            and parsed_args.query_vector_store
        ):
            return handle_headless_query_vector_store(
                parsed_args.query_vector_store, config, console
            )
        elif (
            hasattr(parsed_args, "vector_store_stats")
            and parsed_args.vector_store_stats
        ):
            return handle_headless_vector_store_stats(config, console)

        # Display welcome message
        display_welcome(console, config)

        # Initialize chat session (check for dummy mode)
        dummy_mode = getattr(parsed_args, "dummy_mode", False)
        chat_session = ChatSession(config, console, dummy_mode=dummy_mode)

        # Run the async main loop
        return asyncio.run(run_interactive_chat(chat_session, console, config))

    except Exception as e:
        # Create a basic logger for error reporting if config loading failed
        error_logger = logging.getLogger("ocat.cli.error")
        error_logger.setLevel(logging.ERROR)
        error_logger.addHandler(logging.StreamHandler())
        error_logger.error(f"Error: {e}")
        console.print(f"Error: {e}", style="bold red")
        if parsed_args.debug:
            import traceback

            console.print("\\nDebug traceback:", style="yellow")
            console.print(traceback.format_exc())
        return 1


def handle_headless_add_to_vector_store(
    file_path: str, config: Config, console: Console
) -> int:
    """
    Handle headless mode operation: add text document to vector store.

    Parameters
    ----------
    file_path : str
        Path to the text document to add
    config : Config
        Configuration instance
    console : Console
        Rich console for output

    Returns
    -------
    int
        Exit code (0 for success, 1 for error)
    """
    try:
        from .vector_store import ConversationVectorStore
        import uuid
        import time

        console.print(f"[yellow]Adding document to vector store: {file_path}[/yellow]")

        # Check if file exists
        if not os.path.exists(file_path):
            console.print(f"[red]File not found: {file_path}[/red]")
            return 1

        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            console.print(f"[red]File is empty: {file_path}[/red]")
            return 1

        # Initialize vector store
        vector_store = ConversationVectorStore(config)

        # Create exchange from document content
        exchange_id = vector_store.add_exchange(
            user_prompt=f"Document: {os.path.basename(file_path)}",
            assistant_response=content,
            thread_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
        )

        console.print(f"[green]Successfully added document to vector store[/green]")
        console.print(f"Exchange ID: {exchange_id}")
        return 0

    except Exception as e:
        console.print(f"[red]Error adding document: {e}[/red]")
        return 1


def handle_headless_query_vector_store(
    query: str, config: Config, console: Console
) -> int:
    """
    Handle headless mode operation: query vector store.

    Parameters
    ----------
    query : str
        Query string to search for
    config : Config
        Configuration instance
    console : Console
        Rich console for output

    Returns
    -------
    int
        Exit code (0 for success, 1 for error)
    """
    try:
        from .vector_store import ConversationVectorStore

        console.print(f"[yellow]Querying vector store: {query}[/yellow]")

        # Initialize vector store
        vector_store = ConversationVectorStore(config)

        # Find similar exchanges
        similar_exchanges = vector_store.find_similar_exchanges(
            query_text=query, n_results=config.vector_store.context_results
        )

        if not similar_exchanges:
            console.print("[yellow]No similar exchanges found.[/yellow]")
            return 0

        console.print(
            f"[green]Found {len(similar_exchanges)} similar exchanges:[/green]\n"
        )

        for i, exchange in enumerate(similar_exchanges, 1):
            console.print(f"[bold cyan]Result {i}:[/bold cyan]")
            console.print(f"Exchange ID: {exchange.exchange_id}")
            console.print(f"Thread ID: {exchange.thread_id}")
            console.print(f"Timestamp: {exchange.timestamp}")
            console.print(f"User: {exchange.user_prompt}")
            console.print(
                f"Assistant: {exchange.assistant_response[:200]}..."
                if len(exchange.assistant_response) > 200
                else f"Assistant: {exchange.assistant_response}"
            )
            console.print("" + "-" * 50)

        return 0

    except Exception as e:
        console.print(f"[red]Error querying vector store: {e}[/red]")
        return 1


async def run_interactive_chat(
    chat_session: ChatSession, console: Console, config: Config
) -> int:
    """
    Run the main interactive chat loop.

    Parameters
    ----------
    chat_session : ChatSession
        The chat session instance
    console : Console
        Rich console for output
    config : Config
        Configuration instance

    Returns
    -------
    int
        Exit code (0 for success, 1 for error)
    """
    # Create custom key bindings for intuitive chat input
    # Enter = submit, various alternatives for newline
    bindings = KeyBindings()

    @bindings.add('enter')
    def _(event):
        """Submit the input when Enter is pressed."""
        event.app.exit(result=event.app.current_buffer.text)

    @bindings.add('c-j')  # Ctrl+J for newline (traditional)
    def _(event):
        """Insert newline when Ctrl+J is pressed."""
        event.current_buffer.insert_text('\n')
        
    @bindings.add('escape', 'enter')  # Alt+Enter (Esc+Enter sequence) 
    def _(event):
        """Insert newline when Alt+Enter is pressed."""
        event.current_buffer.insert_text('\n')

    # Try to add Shift+Enter support (may not work in all terminals)
    try:
        @bindings.add('<Shift-Enter>')  # Try the literal Shift+Enter format
        def _(event):
            """Insert newline when Shift+Enter is pressed."""
            event.current_buffer.insert_text('\n')
    except:
        # Shift+Enter not supported in this terminal/environment
        pass

    @bindings.add('c-d')  # Ctrl+D (EOF)
    def _(event):
        """Submit on Ctrl+D for compatibility."""
        if event.app.current_buffer.text.strip():
            event.app.exit(result=event.app.current_buffer.text)
        else:
            # Empty input + Ctrl+D = exit application
            raise EOFError()

    # Create prompt session with custom key bindings
    prompt_session: PromptSession = PromptSession(
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
        multiline=True,
        key_bindings=bindings,
    )

    # Show updated input info
    console.print(
        "[dim](Enter = submit  |  Shift+Enter, Ctrl+J, or Alt+Enter = newline  |  Ctrl+D = submit/exit)[/dim]"
    )

    # Main interactive loop
    while True:
        try:
            # Get user input
            user_input = await asyncio.to_thread(
                prompt_session.prompt, config.display.prompt_symbol
            )

            # Handle empty input
            if not user_input.strip():
                continue

            # Handle built-in commands
            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("Goodbye! 👋", style="green")
                break
            elif user_input.lower() in ["help", "h"]:
                chat_session.show_help()
                continue
            elif user_input.lower() == "clear":
                console.clear()
                display_welcome(console, config)
                continue

            # Process chat message
            await chat_session.process_message(user_input)

        except KeyboardInterrupt:
            console.print("\n\n⚠️  Operation cancelled by user", style="bright_yellow")
            # If we're in the middle of processing, give feedback
            console.print("Press Ctrl+C again to exit the application.", style="dim")
            continue
        except EOFError:
            console.print("\n\nGoodbye! 👋", style="green")
            break
        except Exception as e:
            console.print(f"Unexpected error: {e}", style="red")
            if config.logging.level == "DEBUG":
                import traceback

                console.print(traceback.format_exc(), style="dim red")

    return 0


def handle_headless_vector_store_stats(config: Config, console: Console) -> int:
    """
    Handle headless mode operation: display vector store statistics.

    Parameters
    ----------
    config : Config
        Configuration instance
    console : Console
        Rich console for output

    Returns
    -------
    int
        Exit code (0 for success, 1 for error)
    """
    try:
        from .vector_store import ConversationVectorStore
        from rich.table import Table

        console.print("[yellow]Vector store statistics:[/yellow]\n")

        # Initialize vector store
        vector_store = ConversationVectorStore(config)

        # Get statistics
        stats = vector_store.get_stats()

        # Create a table for better display
        table = Table(title="Vector Store Statistics")
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Total Exchanges", str(stats["total_exchanges"]))
        table.add_row("Collection Count", str(stats["collection_count"]))
        table.add_row("Store Path", stats["store_path"])
        table.add_row("Vector Dimension", str(stats["dimension"]))
        table.add_row("Embedding Model", stats["embedding_model"])

        console.print(table)
        return 0

    except Exception as e:
        console.print(f"[red]Error getting vector store stats: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
