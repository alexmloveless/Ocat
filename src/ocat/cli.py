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
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="LLM model to use for chat"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
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
        # Load configuration
        config = Config.load(parsed_args.config)
        
        # Override config with command line arguments
        if parsed_args.model:
            config.model_config.model = parsed_args.model
        
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


if __name__ == "__main__":
    sys.exit(main())
