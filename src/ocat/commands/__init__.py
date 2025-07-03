"""
Command system for Ocat slash commands.

This module provides the base infrastructure for implementing slash commands,
including the command registry, decorator pattern, and base command class.
"""

from typing import Dict, Type, Any, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ..utils.logging import setup_logger, LogLevel
from ..exceptions import OcatError


class CommandResult:
    """Result of executing a command."""

    def __init__(
        self, success: bool = True, message: str = "", data: Any = None
    ) -> None:
        """
        Initialize command result.

        Parameters
        ----------
        success : bool, default=True
            Whether the command executed successfully
        message : str, default=""
            Message to display to user
        data : Any, default=None
            Optional data returned by command
        """
        self.success: bool = success
        self.message: str = message
        self.data: Any = data

    @classmethod
    def ok(cls, message: str = "", data: Any = None) -> "CommandResult":
        """Create a successful command result."""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error(cls, message: str) -> "CommandResult":
        """Create an error command result."""
        return cls(success=False, message=message)


class BaseCommand(ABC):
    """Base class for all Ocat commands."""

    def __init__(self, name: str, description: str, usage: str = ""):
        """
        Initialize base command.

        Parameters
        ----------
        name : str
            Name of the command (without slash)
        description : str
            Brief description of what the command does
        usage : str, default=""
            Usage string showing command syntax
        """
        self.name = name
        self.description = description
        self.usage = usage or f"/{name}"

    @abstractmethod
    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the command.

        Parameters
        ----------
        args : List[str]
            Command arguments (excluding the command name)
        context : Any
            Command execution context (ChatSession instance)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        pass


class CommandRegistry:
    """Registry for managing slash commands."""

    def __init__(self):
        """Initialize the command registry."""
        self._commands: Dict[str, BaseCommand] = {}
        self._aliases: Dict[str, str] = {}

    def register(
        self, command: BaseCommand, aliases: Optional[List[str]] = None
    ) -> None:
        """
        Register a command in the registry.

        Parameters
        ----------
        command : BaseCommand
            The command to register
        aliases : Optional[List[str]], default=None
            List of aliases for the command
        """
        self._commands[command.name] = command

        if aliases:
            for alias in aliases:
                self._aliases[alias] = command.name

    def get_command(self, name: str) -> Optional[BaseCommand]:
        """
        Get a command by name or alias.

        Parameters
        ----------
        name : str
            Command name or alias

        Returns
        -------
        Optional[BaseCommand]
            Command instance if found, None otherwise
        """
        # Check if it's an alias first
        if name in self._aliases:
            name = self._aliases[name]

        return self._commands.get(name)

    def list_commands(self) -> Dict[str, BaseCommand]:
        """
        Get all registered commands.

        Returns
        -------
        Dict[str, BaseCommand]
            Dictionary of command names to command instances
        """
        return self._commands.copy()

    def get_aliases(self, command_name: str) -> List[str]:
        """
        Get aliases for a command.

        Parameters
        ----------
        command_name : str
            Name of the command

        Returns
        -------
        List[str]
            List of aliases for the command
        """
        return [
            alias
            for alias, cmd_name in self._aliases.items()
            if cmd_name == command_name
        ]


# Global command registry
_registry = CommandRegistry()


def command(
    name: str, description: str, usage: str = "", aliases: Optional[List[str]] = None
):
    """
    Decorator to register a command class.

    Parameters
    ----------
    name : str
        Name of the command
    description : str
        Description of the command
    usage : str, default=""
        Usage string for the command
    aliases : Optional[List[str]], default=None
        List of aliases for the command
    """

    def decorator(cls: Type[BaseCommand]) -> Type[BaseCommand]:
        # Create an instance of the command and register it
        instance = cls(name, description, usage)
        _registry.register(instance, aliases)
        return cls

    return decorator


def get_registry() -> CommandRegistry:
    """Get the global command registry."""
    return _registry


class CommandError(OcatError):
    """Exception raised when command execution fails."""

    pass


# Import all command modules to register them
from . import help_command
from . import core_commands
from . import history_commands
from . import file_commands
from . import vector_commands
from . import context_commands
from . import remember_command
from . import clipboard_commands
