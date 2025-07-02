"""
Tests for the append command functionality.

Tests appending text and last exchange to files with and without location aliases.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.ocat.commands.file_commands import AppendCommand
from src.ocat.commands import CommandResult
from src.ocat.config import Config
from src.ocat.chat import Message


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration with location aliases."""
    config = Mock(spec=Config)
    config.locations = {
        "test": str(temp_dir / "test_dir"),
        "conv": str(temp_dir / "conversations"),
        "myfile": str(temp_dir / "specific_file.txt"),  # File alias
    }
    config.display = Mock()
    config.display.user_label = "User"
    config.display.assistant_label = "Assistant"
    return config


@pytest.fixture
def mock_context(mock_config):
    """Create a mock command execution context."""
    context = Mock()
    context.config = mock_config
    context.console = Mock()
    context.messages = []
    return context


@pytest.fixture
def mock_context_with_messages(mock_context):
    """Create a mock context with some conversation messages."""
    context = mock_context
    context.messages = [
        Message(role="user", content="Hello, how are you?"),
        Message(role="assistant", content="I'm doing well, thank you for asking!"),
        Message(role="user", content="What's the weather like?"),
        Message(
            role="assistant", content="I don't have access to current weather data."
        ),
    ]
    return context


class TestAppendCommand:
    """Test the append command functionality."""

    def test_append_command_creation(self):
        """Test that append command can be created."""
        cmd = AppendCommand("append", "Test description")
        assert cmd.name == "append"
        assert cmd.description == "Test description"

    @pytest.mark.asyncio
    async def test_append_text_to_new_file(self, temp_dir, mock_context):
        """Test appending text to a new file."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")
        target_file = temp_dir / "new_file.txt"

        # Execute append command with text
        result = await cmd.execute([str(target_file), "Hello", "World"], mock_context)

        assert result.success
        assert target_file.exists()
        content = target_file.read_text()
        assert "Hello World" in content

    @pytest.mark.asyncio
    async def test_append_text_to_existing_file(self, temp_dir, mock_context):
        """Test appending text to an existing file."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")
        target_file = temp_dir / "existing_file.txt"

        # Create existing file with content
        target_file.write_text("Initial content\n")

        # Execute append command with text
        result = await cmd.execute([str(target_file), "Appended", "text"], mock_context)

        assert result.success
        content = target_file.read_text()
        assert "Initial content" in content
        assert "Appended text" in content

    @pytest.mark.asyncio
    async def test_append_with_quoted_text(self, temp_dir, mock_context):
        """Test appending quoted text."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")
        target_file = temp_dir / "quoted_file.txt"

        # Execute append command with quoted text
        result = await cmd.execute(
            [str(target_file), '"Hello world with spaces"'], mock_context
        )

        assert result.success
        content = target_file.read_text()
        assert "Hello world with spaces" in content

    @pytest.mark.asyncio
    async def test_append_last_exchange(self, temp_dir, mock_context_with_messages):
        """Test appending last exchange when no text is provided."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")
        target_file = temp_dir / "exchange_file.txt"

        # Execute append command without text (should append last exchange)
        result = await cmd.execute([str(target_file)], mock_context_with_messages)

        assert result.success
        content = target_file.read_text()
        # Should contain the last user and assistant exchange
        assert "What's the weather like?" in content
        assert "I don't have access to current weather data." in content
        assert "User" in content
        assert "Assistant" in content

    @pytest.mark.asyncio
    async def test_append_with_location_alias_directory(self, temp_dir, mock_context):
        """Test appending with a directory location alias."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")

        # Create the test directory
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir(exist_ok=True)

        # Execute append command using alias
        result = await cmd.execute(
            ["test:my_file.txt", "Test", "content"], mock_context
        )

        assert result.success
        target_file = test_dir / "my_file.txt"
        assert target_file.exists()
        content = target_file.read_text()
        assert "Test content" in content

    @pytest.mark.asyncio
    async def test_append_with_location_alias_file(self, temp_dir, mock_context):
        """Test appending with a file location alias."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")

        # Ensure parent directory exists
        (temp_dir).mkdir(exist_ok=True)

        # Execute append command using file alias
        result = await cmd.execute(
            ["myfile", "Content", "for", "specific", "file"], mock_context
        )

        assert result.success
        target_file = temp_dir / "specific_file.txt"
        assert target_file.exists()
        content = target_file.read_text()
        assert "Content for specific file" in content

    @pytest.mark.asyncio
    async def test_append_creates_parent_directories(self, temp_dir, mock_context):
        """Test that append creates parent directories if they don't exist."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")
        target_file = temp_dir / "nested" / "deep" / "file.txt"

        # Execute append command
        result = await cmd.execute(
            [str(target_file), "Deep", "file", "content"], mock_context
        )

        assert result.success
        assert target_file.exists()
        content = target_file.read_text()
        assert "Deep file content" in content

    @pytest.mark.asyncio
    async def test_append_no_file_path_error(self, mock_context):
        """Test error when no file path is provided."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")

        # Execute append command without arguments
        result = await cmd.execute([], mock_context)

        assert not result.success
        assert "No file path specified" in result.message

    @pytest.mark.asyncio
    async def test_append_no_exchange_available_error(self, mock_context):
        """Test error when trying to append last exchange but none exists."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")

        # Mock context with no messages
        mock_context.messages = []

        # Execute append command without text (should try to append last exchange)
        result = await cmd.execute(["/tmp/test_file.txt"], mock_context)

        assert not result.success
        assert "No complete exchange found" in result.message

    @pytest.mark.asyncio
    async def test_append_invalid_location_alias_error(self, mock_context):
        """Test error when using invalid location alias."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")

        # Execute append command with invalid alias
        result = await cmd.execute(["invalid_alias:file.txt", "Test"], mock_context)

        assert not result.success
        assert "Location alias 'invalid_alias' not found" in result.message

    @pytest.mark.asyncio
    async def test_append_ensures_newline_ending(self, temp_dir, mock_context):
        """Test that append ensures content ends with newline."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")
        target_file = temp_dir / "newline_test.txt"

        # Execute append command multiple times
        await cmd.execute([str(target_file), "First line"], mock_context)
        await cmd.execute([str(target_file), "Second line"], mock_context)

        content = target_file.read_text()
        lines = content.split("\n")
        # Should have proper line separation
        assert "First line" in content
        assert "Second line" in content
        assert content.endswith("\n")

    @pytest.mark.asyncio
    async def test_append_permission_error(self, mock_context):
        """Test handling permission errors."""
        cmd = AppendCommand("append", "Append text or last exchange to a file")

        # Try to write to a read-only location (this might be platform-specific)
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = await cmd.execute(["/readonly/file.txt", "Test"], mock_context)

            assert not result.success
            assert (
                "Permission denied" in result.message
                or "Failed to append to file" in result.message
            )


class TestLocationAliasesWithFiles:
    """Test location aliases specifically for file paths."""

    @pytest.mark.asyncio
    async def test_file_alias_resolution(self, temp_dir, mock_config):
        """Test that file aliases resolve correctly."""
        from src.ocat.utils import resolve_path_with_aliases

        # Test file alias resolution
        resolved_path = resolve_path_with_aliases("myfile", mock_config.locations)
        expected_path = temp_dir / "specific_file.txt"

        assert resolved_path == expected_path

    @pytest.mark.asyncio
    async def test_directory_alias_with_file(self, temp_dir, mock_config):
        """Test directory alias with file specification."""
        from src.ocat.utils import resolve_path_with_aliases

        # Test directory alias with file
        resolved_path = resolve_path_with_aliases(
            "test:myfile.txt", mock_config.locations
        )
        expected_path = temp_dir / "test_dir" / "myfile.txt"

        assert resolved_path == expected_path


if __name__ == "__main__":
    pytest.main([__file__])
