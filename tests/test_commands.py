"""
Tests for the slash command system.

Tests the command registry, parser, and execution functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from rich.console import Console

from src.ocat.commands import (
    BaseCommand,
    CommandRegistry,
    CommandResult,
    get_registry,
    command,
    CommandError,
)
from src.ocat.commands.parser import CommandParser
from src.ocat.config import Config


# Create a test command for testing
@command(
    name="testcmd", description="Test command", usage="/testcmd [arg]", aliases=["tc"]
)
class TestCmdCommand(BaseCommand):
    """Test command for unit testing."""

    async def execute(self, args, context):
        if args and args[0] == "error":
            return CommandResult.error("Test error")
        return CommandResult.ok(f"Test successful with args: {args}")


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock(spec=Config)
    config.logging = Mock()
    config.logging.level = "INFO"
    config.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    config.logging.show_context = False
    return config


@pytest.fixture
def mock_console():
    """Create a mock Rich console."""
    return Mock(spec=Console)


@pytest.fixture
def mock_context(mock_config, mock_console):
    """Create a mock command execution context."""
    context = Mock()
    context.config = mock_config
    context.console = mock_console
    context.clear_history = Mock()
    context.show_welcome = Mock()
    return context


@pytest.fixture
def command_parser(mock_config):
    """Create a command parser for testing."""
    return CommandParser(mock_config)


class TestCommandRegistry:
    """Test the command registry functionality."""

    def test_command_registration(self):
        """Test that commands are properly registered."""
        registry = CommandRegistry()
        test_cmd = TestCmdCommand("test", "Test command")

        registry.register(test_cmd, aliases=["t"])

        assert registry.get_command("test") == test_cmd
        assert registry.get_command("t") == test_cmd
        assert "test" in registry.list_commands()

    def test_get_aliases(self):
        """Test getting aliases for a command."""
        registry = CommandRegistry()
        test_cmd = TestCmdCommand("test", "Test command")

        registry.register(test_cmd, aliases=["t", "tst"])

        aliases = registry.get_aliases("test")
        assert "t" in aliases
        assert "tst" in aliases

    def test_unknown_command(self):
        """Test getting unknown command returns None."""
        registry = CommandRegistry()
        assert registry.get_command("unknown") is None


class TestCommandParser:
    """Test the command parser functionality."""

    def test_is_command(self, command_parser):
        """Test command detection."""
        assert command_parser.is_command("/help")
        assert command_parser.is_command("  /exit  ")
        assert not command_parser.is_command("hello")
        assert not command_parser.is_command("regular message")

    def test_parse_command(self, command_parser):
        """Test command parsing."""
        # Simple command
        name, args = command_parser.parse_command("/help")
        assert name == "help"
        assert args == []

        # Command with arguments
        name, args = command_parser.parse_command("/test arg1 arg2")
        assert name == "test"
        assert args == ["arg1", "arg2"]

        # Command with quoted arguments
        name, args = command_parser.parse_command('/test "arg with spaces" arg2')
        assert name == "test"
        assert args == ["arg with spaces", "arg2"]

        # Invalid command syntax
        name, args = command_parser.parse_command("/")
        assert name is None
        assert args == []

    @pytest.mark.asyncio
    async def test_execute_command_success(self, command_parser, mock_context):
        """Test successful command execution."""
        result = await command_parser.execute_command("/testcmd arg1", mock_context)

        assert result.success
        assert "Test successful" in result.message

    @pytest.mark.asyncio
    async def test_execute_command_error(self, command_parser, mock_context):
        """Test command execution with error."""
        result = await command_parser.execute_command("/testcmd error", mock_context)

        assert not result.success
        assert "Test error" in result.message

    @pytest.mark.asyncio
    async def test_execute_unknown_command(self, command_parser, mock_context):
        """Test execution of unknown command."""
        result = await command_parser.execute_command("/unknown", mock_context)

        assert not result.success
        assert "Unknown command" in result.message

    @pytest.mark.asyncio
    async def test_execute_invalid_syntax(self, command_parser, mock_context):
        """Test execution with invalid syntax."""
        result = await command_parser.execute_command("/", mock_context)

        assert not result.success
        assert "Invalid command syntax" in result.message


class TestCommandResult:
    """Test the CommandResult class."""

    def test_success_result(self):
        """Test creating success result."""
        result = CommandResult.ok("Success message", {"data": "value"})

        assert result.success
        assert result.message == "Success message"
        assert result.data == {"data": "value"}

    def test_error_result(self):
        """Test creating error result."""
        result = CommandResult.error("Error message")

        assert not result.success
        assert result.message == "Error message"
        assert result.data is None


class TestCommandDecorator:
    """Test the command decorator functionality."""

    def test_command_decorator_registration(self):
        """Test that the @command decorator registers commands."""
        registry = get_registry()

        # The TestCmdCommand should be registered by the decorator
        assert registry.get_command("testcmd") is not None
        assert registry.get_command("tc") is not None  # alias

    def test_command_decorator_properties(self):
        """Test that decorator sets correct command properties."""
        registry = get_registry()
        test_cmd = registry.get_command("testcmd")

        assert test_cmd.name == "testcmd"
        assert test_cmd.description == "Test command"
        assert test_cmd.usage == "/testcmd [arg]"


@pytest.mark.asyncio
async def test_integration_with_chat_session():
    """Test integration with ChatSession (mock test)."""
    # This would test the integration but requires full ChatSession setup
    # For now, we'll just test that the command parser can be created
    mock_config = Mock()
    mock_config.logging = Mock()
    mock_config.logging.level = "INFO"

    parser = CommandParser(mock_config)
    assert parser is not None
    assert parser.registry is not None
