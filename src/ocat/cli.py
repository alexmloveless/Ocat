"""
CLI module for Ocat - Interactive LLM Chat CLI tool.

This module provides the main command-line interface for the Ocat application,
handling user input, command parsing, and interaction coordination.
"""

import sys
import argparse
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

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
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"ocat {__version__}"
    )
    
    # Configuration file
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    # Model configuration overrides
    parser.add_argument(
        "--model",
        type=str,
        help="LLM model to use for chat"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature setting for model responses (0.0-1.0)"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum tokens for responses"
    )
    
    # Vector store configuration overrides
    parser.add_argument(
        "--vector-store-path",
        type=str,
        help="Path to vector store directory"
    )
    
    parser.add_argument(
        "--no-vector-store",
        action="store_true",
        help="Disable vector store functionality"
    )
    
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        help="Vector similarity threshold (0.0-1.0)"
    )
    
    # Logging configuration overrides
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARN", "ERROR"],
        help="Set logging level"
    )
    
    # Display configuration overrides
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable rich text formatting"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output"
    )
    
    parser.add_argument(
        "--line-width",
        type=int,
        help="CLI line width in characters"
    )
    
    # Profile name override
    parser.add_argument(
        "--profile",
        type=str,
        help="Configuration profile name"
    )
    
    # Special modes
    parser.add_argument(
        "--dummy-mode",
        action="store_true",
        help="Use dummy responses for testing (no real LLM calls)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed error traces"
    )
    
    # Headless mode options for vector store operations
    headless_group = parser.add_argument_group('headless mode', 
        'Non-interactive operations for automation')
    
    headless_group.add_argument(
        "--add-to-vector-store",
        type=str,
        help="Add text document to vector store and exit"
    )
    
    headless_group.add_argument(
        "--query-vector-store",
        type=str,
        help="Query vector store and exit"
    )
    
    headless_group.add_argument(
        "--vector-store-stats",
        action="store_true",
        help="Display vector store statistics and exit"
    )
    
    return parser


def display_welcome(console: Console) -> None:
    """
    Display welcome message and basic instructions.
    
    Parameters
    ----------
    console : Console
        Rich console instance for output
    """
    welcome_text = Text("Welcome to Ocat!", style="bold blue")
    subtitle = Text("An interactive LLM Chat CLI tool", style="italic")
    
    panel = Panel(
        f"{welcome_text}\n{subtitle}\n\nType 'help' for commands or 'exit' to quit.",
        title="🐱 Ocat",
        border_style="blue"
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
        if getattr(parsed_args, 'max_tokens', None) is not None:
            cli_overrides["max_tokens"] = parsed_args.max_tokens
            
        # Vector store configuration overrides
        if getattr(parsed_args, 'vector_store_path', None):
            cli_overrides["vector_store_path"] = parsed_args.vector_store_path
        if getattr(parsed_args, 'no_vector_store', False):
            cli_overrides["no_vector_store"] = True
        if getattr(parsed_args, 'similarity_threshold', None) is not None:
            cli_overrides["similarity_threshold"] = parsed_args.similarity_threshold
            
        # Logging configuration overrides
        if getattr(parsed_args, 'log_level', None):
            cli_overrides["log_level"] = parsed_args.log_level
            
        # Display configuration overrides
        if getattr(parsed_args, 'no_rich', False):
            cli_overrides["no_rich"] = True
        if getattr(parsed_args, 'no_color', False):
            cli_overrides["no_color"] = True
        if getattr(parsed_args, 'line_width', None) is not None:
            cli_overrides["line_width"] = parsed_args.line_width
            
        # Profile name override
        if getattr(parsed_args, 'profile', None):
            cli_overrides["profile"] = parsed_args.profile
        
        # Load configuration with CLI overrides
        config = Config.load(parsed_args.config, cli_overrides if cli_overrides else None)
        
        # Handle headless mode operations
        if hasattr(parsed_args, 'add_to_vector_store') and parsed_args.add_to_vector_store:
            return handle_headless_add_to_vector_store(parsed_args.add_to_vector_store, config, console)
        elif hasattr(parsed_args, 'query_vector_store') and parsed_args.query_vector_store:
            return handle_headless_query_vector_store(parsed_args.query_vector_store, config, console)
        elif hasattr(parsed_args, 'vector_store_stats') and parsed_args.vector_store_stats:
            return handle_headless_vector_store_stats(config, console)
        
        # Display welcome message
        display_welcome(console)
        
        # Initialize chat session
        chat_session = ChatSession(config, console)
        
        # Create prompt session with history and auto-suggest
        prompt_session = PromptSession(
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory()
        )
        
        # Main interactive loop
        while True:
            try:
                # Get user input
                user_input = prompt_session.prompt("🐱 > ", multiline=False)
                
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
                    display_welcome(console)
                    continue
                
                # Process chat message
                chat_session.process_message(user_input)
                
            except KeyboardInterrupt:
                console.print("\\n\\nInterrupted by user", style="yellow")
                break
            except EOFError:
                console.print("\\n\\nGoodbye! 👋", style="green")
                break
        
        return 0
        
    except Exception as e:
        console.print(f"Error: {e}", style="bold red")
        if parsed_args.debug:
            import traceback
            console.print("\\nDebug traceback:", style="yellow")
            console.print(traceback.format_exc())
        return 1


def handle_headless_add_to_vector_store(file_path: str, config: Config, console: Console) -> int:
    """
    Handle headless mode operation: add document to vector store.
    
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
        console.print(f"[yellow]Adding document to vector store: {file_path}[/yellow]")
        # TODO: Implement vector store addition when vector store module is ready
        console.print("[red]Vector store not yet implemented[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Error adding document: {e}[/red]")
        return 1


def handle_headless_query_vector_store(query: str, config: Config, console: Console) -> int:
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
        console.print(f"[yellow]Querying vector store: {query}[/yellow]")
        # TODO: Implement vector store querying when vector store module is ready
        console.print("[red]Vector store not yet implemented[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Error querying vector store: {e}[/red]")
        return 1


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
        console.print("[yellow]Vector store statistics:[/yellow]")
        # TODO: Implement vector store stats when vector store module is ready
        console.print("[red]Vector store not yet implemented[/red]")
        return 1
    except Exception as e:
        console.print(f"[red]Error getting vector store stats: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
