"""
Core slash commands for Ocat.

Implements basic commands like exit, clear, and config.
"""

from typing import List, Any
import sys
import json

from . import command, BaseCommand, CommandResult
from rich.table import Table
from rich.panel import Panel


@command(
    name="exit",
    description="Exit the Ocat application",
    usage="/exit",
    aliases=["quit", "q"],
)
class ExitCommand(BaseCommand):
    """Command to exit the application."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the exit command.

        Parameters
        ----------
        args : List[str]
            Command arguments
        context : Any
            Command execution context

        Returns
        -------
        CommandResult
            Result of command execution
        """
        context.console.print("👋 Goodbye!", style="bold blue")
        sys.exit(0)


@command(name="clear", description="Clear conversation history", usage="/clear")
class ClearCommand(BaseCommand):
    """Command to clear conversation history."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the clear command.

        Parameters
        ----------
        args : List[str]
            Command arguments
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Clear conversation history
            context.clear_history()

            # Clear the console screen
            context.console.clear()

            # Show welcome message again
            if hasattr(context, "show_welcome"):
                context.show_welcome()

            return CommandResult.success("Conversation history cleared.")

        except Exception as e:
            return CommandResult.error(f"Failed to clear history: {e}")


@command(
    name="config", description="Show current configuration settings", usage="/config"
)
class ConfigCommand(BaseCommand):
    """Command to display current configuration."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the config command.

        Parameters
        ----------
        args : List[str]
            Command arguments
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            config = context.config

            # Create a formatted configuration display
            config_table = Table(title="Current Configuration")
            config_table.add_column("Setting", style="cyan", no_wrap=True)
            config_table.add_column("Value", style="white")

            # LLM settings
            config_table.add_row("Model", config.llm.model)
            config_table.add_row("Temperature", str(config.llm.temperature))
            config_table.add_row("Max Tokens", str(config.llm.max_tokens))

            # Vector store settings
            config_table.add_row(
                "Vector Store Enabled", str(config.vector_store.enabled)
            )
            if config.vector_store.enabled:
                config_table.add_row("Vector Store Path", config.vector_store.path)
                config_table.add_row(
                    "Similarity Threshold",
                    str(config.vector_store.similarity_threshold),
                )
                config_table.add_row(
                    "Chat Window", str(config.vector_store.chat_window)
                )
                config_table.add_row(
                    "Context Results", str(config.vector_store.context_results)
                )

            # Display settings
            config_table.add_row("User Label", config.display.user_label)
            config_table.add_row("Assistant Label", config.display.assistant_label)
            config_table.add_row("Line Width", str(config.display.line_width))
            config_table.add_row(
                "Response on New Line", str(config.display.response_on_new_line)
            )

            # Logging settings
            config_table.add_row("Log Level", config.logging.level)

            context.console.print(config_table)
            context.console.print()

            return CommandResult.success("Configuration displayed.")

        except Exception as e:
            return CommandResult.error(f"Failed to display configuration: {e}")
