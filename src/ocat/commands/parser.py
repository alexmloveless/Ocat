"""
Command parser for Ocat slash commands.

Handles parsing of user input to detect and execute slash commands.
"""

import shlex
from typing import List, Optional, Tuple, Any
import logging

from . import get_registry, CommandResult, CommandError
from ..utils.logging import setup_logger, LogLevel


class CommandParser:
    """Parser for slash commands."""

    def __init__(self, config):
        """
        Initialize command parser.

        Parameters
        ----------
        config : Config
            Configuration object for logging setup
        """
        self.registry = get_registry()
        self.logger = setup_logger(
            "ocat.commands.parser", LogLevel[config.logging.level], config
        )

    def is_command(self, user_input: str) -> bool:
        """
        Check if user input is a slash command.

        Parameters
        ----------
        user_input : str
            User input to check

        Returns
        -------
        bool
            True if input starts with '/', False otherwise
        """
        return user_input.strip().startswith("/")

    def parse_command(self, user_input: str) -> Tuple[Optional[str], List[str]]:
        """
        Parse a command line into command name and arguments.

        Parameters
        ----------
        user_input : str
            Raw user input starting with '/'

        Returns
        -------
        Tuple[Optional[str], List[str]]
            Tuple of (command_name, arguments) or (None, []) if parsing fails
        """
        try:
            # Remove leading slash and split using shell-like parsing
            command_line = user_input.strip()[1:]  # Remove the '/'

            if not command_line:
                return None, []

            # Use shlex to properly handle quoted arguments
            parts = shlex.split(command_line)

            if not parts:
                return None, []

            command_name = parts[0]
            args = parts[1:] if len(parts) > 1 else []

            return command_name, args

        except ValueError as e:
            # shlex.split can raise ValueError for malformed input
            self.logger.warning(f"Failed to parse command: {e}")
            return None, []

    async def execute_command(self, user_input: str, context: Any) -> CommandResult:
        """
        Execute a slash command from user input.

        Parameters
        ----------
        user_input : str
            Raw user input starting with '/'
        context : Any
            Command execution context (ChatSession instance)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Parse the command
            command_name, args = self.parse_command(user_input)

            if command_name is None:
                return CommandResult.error("Invalid command syntax")

            # Find the command in the registry
            command = self.registry.get_command(command_name)

            if command is None:
                available_commands = list(self.registry.list_commands().keys())
                return CommandResult.error(
                    f"Unknown command: '{command_name}'. "
                    f"Available commands: {', '.join(available_commands)}. "
                    f"Type '/help' for more information."
                )

            self.logger.debug(f"Executing command: {command_name} with args: {args}")

            # Execute the command
            result = await command.execute(args, context)

            self.logger.debug(
                f"Command {command_name} completed with success: {result.success}"
            )

            return result

        except CommandError as e:
            self.logger.error(f"Command error: {e}")
            return CommandResult.error(str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error executing command: {e}")
            return CommandResult.error(f"Unexpected error: {e}")

    def get_available_commands(self) -> List[str]:
        """
        Get list of available command names.

        Returns
        -------
        List[str]
            List of available command names
        """
        return list(self.registry.list_commands().keys())
