"""
History and model management commands for Ocat.

Implements commands for managing conversation history and LLM model switching.
"""

from typing import List, Any
import json

from . import command, BaseCommand, CommandResult
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


@command(name="history", description="Show chat history", usage="/history [n]")
class HistoryCommand(BaseCommand):
    """Command to display conversation history."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the history command.

        Parameters
        ----------
        args : List[str]
            Command arguments - optional number of messages to show
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Get conversation history
            history = context.get_conversation_history()

            # Filter out system messages for display
            user_messages = [msg for msg in history if msg["role"] != "system"]

            if not user_messages:
                return CommandResult.ok("No conversation history available.")

            # Parse number of messages to show
            num_messages = len(user_messages)
            if args:
                try:
                    num_messages = min(int(args[0]), len(user_messages))
                except ValueError:
                    return CommandResult.error(
                        "Invalid number format. Use: /history [number]"
                    )

            # Display history
            history_table = Table(
                title=f"Conversation History (last {num_messages} messages)"
            )
            history_table.add_column("Role", style="cyan", no_wrap=True)
            history_table.add_column("Message", style="white")

            # Show last n messages
            for msg in user_messages[-num_messages:]:
                role = msg["role"].title()
                content = msg["content"]

                # Truncate long messages
                if len(content) > 100:
                    content = content[:97] + "..."

                history_table.add_row(role, content)

            context.console.print(history_table)
            context.console.print()

            return CommandResult.ok(f"Displayed {num_messages} messages from history.")

        except Exception as e:
            return CommandResult.error(f"Failed to display history: {e}")


@command(
    name="delete", description="Remove n most recent exchanges", usage="/delete [n=1]"
)
class DeleteCommand(BaseCommand):
    """Command to delete recent conversation exchanges."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the delete command.

        Parameters
        ----------
        args : List[str]
            Command arguments - optional number of exchanges to delete
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Parse number of exchanges to delete
            num_exchanges = 1
            if args:
                try:
                    num_exchanges = int(args[0])
                    if num_exchanges < 1:
                        return CommandResult.error("Number must be positive.")
                except ValueError:
                    return CommandResult.error(
                        "Invalid number format. Use: /delete [number]"
                    )

            # Get current messages
            messages = context.messages

            # Filter out system messages
            non_system_messages = [msg for msg in messages if msg.role != "system"]
            system_messages = [msg for msg in messages if msg.role == "system"]

            if len(non_system_messages) < num_exchanges * 2:
                return CommandResult.error(
                    f"Not enough exchanges to delete. "
                    f"Only {len(non_system_messages) // 2} exchanges available."
                )

            # Remove the specified number of exchanges (user + assistant pairs)
            messages_to_remove = num_exchanges * 2
            remaining_messages = non_system_messages[:-messages_to_remove]

            # Reconstruct message list with system messages
            context.messages = system_messages + remaining_messages

            return CommandResult.ok(
                f"Deleted {num_exchanges} exchange(s) from conversation history."
            )

        except Exception as e:
            return CommandResult.error(f"Failed to delete exchanges: {e}")


@command(name="model", description="Change the LLM model", usage="/model <model_name>")
class ModelCommand(BaseCommand):
    """Command to change the active LLM model."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the model command.

        Parameters
        ----------
        args : List[str]
            Command arguments - new model name
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            # Show current model
            current_model = context.config.llm.model
            context.console.print(f"Current model: {current_model}")
            return CommandResult.ok("Current model displayed.")

        try:
            new_model = args[0]
            old_model = context.config.llm.model

            # Update configuration
            context.config.llm.model = new_model

            # Reinitialize the LLM backend with new model
            if not context.dummy_mode:
                from ..backends import create_backend

                context.llm_backend = create_backend(context.config)
                context.logger.info(f"LLM backend reinitialized for model: {new_model}")

            context.console.print(
                f"✅ Model changed from '{old_model}' to '{new_model}'", style="green"
            )

            return CommandResult.ok(f"Model changed to {new_model}.")

        except Exception as e:
            return CommandResult.error(f"Failed to change model: {e}")


@command(name="showsys", description="Show current system prompt", usage="/showsys")
class ShowSystemCommand(BaseCommand):
    """Command to display the current system prompt."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the showsys command.

        Parameters
        ----------
        args : List[str]
            Command arguments (unused)
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Find system messages
            system_messages = [msg for msg in context.messages if msg.role == "system"]

            if not system_messages:
                return CommandResult.ok("No system prompt configured.")

            # Display system prompt(s)
            for i, msg in enumerate(system_messages):
                title = (
                    f"System Prompt {i+1}"
                    if len(system_messages) > 1
                    else "System Prompt"
                )

                panel = Panel(
                    msg.content, title=title, border_style="yellow", padding=(1, 2)
                )

                context.console.print(panel)
                context.console.print()

            return CommandResult.ok("System prompt displayed.")

        except Exception as e:
            return CommandResult.error(f"Failed to display system prompt: {e}")


@command(name="loglevel", description="Set logging level", usage="/loglevel <level>")
class LogLevelCommand(BaseCommand):
    """Command to change the logging level."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the loglevel command.

        Parameters
        ----------
        args : List[str]
            Command arguments - new log level
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        valid_levels = ["DEBUG", "INFO", "WARN", "ERROR"]

        if not args:
            current_level = context.config.logging.level
            context.console.print(f"Current log level: {current_level}")
            context.console.print(f"Valid levels: {', '.join(valid_levels)}")
            return CommandResult.ok("Current log level displayed.")

        try:
            new_level = args[0].upper()

            if new_level not in valid_levels:
                return CommandResult.error(
                    f"Invalid log level '{new_level}'. "
                    f"Valid levels: {', '.join(valid_levels)}"
                )

            old_level = context.config.logging.level
            context.config.logging.level = new_level

            # Update logger level
            from ..utils.logging import LogLevel
            import logging

            logger = logging.getLogger("ocat")
            logger.setLevel(LogLevel[new_level].value)

            context.console.print(
                f"✅ Log level changed from '{old_level}' to '{new_level}'",
                style="green",
            )

            return CommandResult.ok(f"Log level changed to {new_level}.")

        except Exception as e:
            return CommandResult.error(f"Failed to change log level: {e}")
