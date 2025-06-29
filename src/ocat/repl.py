"""
REPL module for Ocat - Interactive LLM Chat CLI tool.

This module facilitates an interactive prompt-based interface
using prompt_toolkit for intuitive user interaction.
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from typing import Optional

from rich.console import Console

__all__ = ["start_repl"]

def start_repl(console: Optional[Console] = None) -> None:
    """
    Start the REPL session using prompt_toolkit.
    
    Parameters
    ----------
    console : Optional[Console]
        Rich console instance for output
    """
    if console is None:
        console = Console()

    session = PromptSession(
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory()
    )

    console.print("Entering REPL. Type your message or 'exit' to quit.", style="italic blue")
    
    while True:
        try:
            user_input = session.prompt("🐱 [1mREPL> [0m")
            if user_input.strip().lower() in ("exit", "quit"):
                console.print("Goodbye! 👋", style="green")
                break
            console.print(f"You typed: {user_input}", style="italic")
        except (KeyboardInterrupt, EOFError):
            console.print("Exiting REPL. Goodbye! 👋", style="green")
            break

