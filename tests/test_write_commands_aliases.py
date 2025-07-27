"""
Tests for location alias expansion in write commands.

Tests that all write commands (writemd, writejson, writeresp, writecode)
properly expand location aliases.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock

from src.ocat.commands.file_commands import (
    WriteMarkdownCommand,
    WriteJsonCommand,
    WriteResponseCommand,
    WriteCodeCommand,
)
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
        "exports": str(temp_dir / "exports"),
        "code": str(temp_dir / "code"),
        "conv": str(temp_dir / "conversations"),
        "myfile": str(temp_dir / "specific_export.md"),  # File alias
    }
    config.llm = Mock()
    config.llm.model = "gpt-4o-mini"
    config.llm.temperature = 0.7
    config.llm.max_tokens = 4000
    config.display = Mock()
    config.display.user_label = "User"
    config.display.assistant_label = "Assistant"
    return config


@pytest.fixture
def mock_context_with_conversation(mock_config):
    """Create a mock context with a complete conversation."""
    context = Mock()
    context.config = mock_config
    context.console = Mock()
    context.messages = [
        Message(role="user", content="Can you write a hello world function?"),
        Message(
            role="assistant",
            content="Sure! Here's a simple hello world function:\n\n```python\ndef hello_world():\n    print('Hello, World!')\n\nhello_world()\n```\n\nThis function prints 'Hello, World!' when called.",
        ),
        Message(role="user", content="Can you also add some comments?"),
        Message(
            role="assistant",
            content="Of course! Here's the commented version:\n\n```python\ndef hello_world():\n    # Print a greeting message\n    print('Hello, World!')\n\n# Call the function\nhello_world()\n```\n\nNow it has helpful comments!",
        ),
    ]
    return context


class TestWriteCommandsAliases:
    """Test location alias expansion in write commands."""

    @pytest.mark.asyncio
    async def test_writemd_with_directory_alias(
        self, temp_dir, mock_context_with_conversation
    ):
        """Test writemd command with directory alias."""
        cmd = WriteMarkdownCommand("writemd", "Export conversation to Markdown")

        # Create the exports directory
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir(exist_ok=True)

        # Execute writemd command using directory alias
        result = await cmd.execute(
            ["exports:conversation.md"], mock_context_with_conversation
        )

        assert result.success
        target_file = exports_dir / "conversation.md"
        assert target_file.exists()

        content = target_file.read_text()
        assert "# Conversation Export" in content
        assert "hello world function" in content
        assert "```python" in content

    @pytest.mark.asyncio
    async def test_writemd_with_file_alias(
        self, temp_dir, mock_context_with_conversation
    ):
        """Test writemd command with file alias."""
        cmd = WriteMarkdownCommand("writemd", "Export conversation to Markdown")

        # Execute writemd command using file alias
        result = await cmd.execute(["myfile"], mock_context_with_conversation)

        assert result.success
        target_file = temp_dir / "specific_export.md"
        assert target_file.exists()

        content = target_file.read_text()
        assert "# Conversation Export" in content

    @pytest.mark.asyncio
    async def test_writejson_with_alias(self, temp_dir, mock_context_with_conversation):
        """Test writejson command with directory alias."""
        cmd = WriteJsonCommand("writejson", "Export conversation to JSON")

        # Create the exports directory
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir(exist_ok=True)

        # Execute writejson command using alias
        result = await cmd.execute(
            ["exports:conversation.json"], mock_context_with_conversation
        )

        assert result.success
        target_file = exports_dir / "conversation.json"
        assert target_file.exists()

        # Verify JSON content
        with open(target_file) as f:
            data = json.load(f)

        assert "conversation" in data
        assert "config" in data
        assert len(data["conversation"]) == 4  # 4 messages in our test conversation

    @pytest.mark.asyncio
    async def test_writeresp_with_alias_md_format(
        self, temp_dir, mock_context_with_conversation
    ):
        """Test writeresp command with alias in markdown format."""
        cmd = WriteResponseCommand("writeresp", "Export last exchange")

        # Create the exports directory
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir(exist_ok=True)

        # Execute writeresp command using alias
        result = await cmd.execute(
            ["exports:last_exchange.md", "md"], mock_context_with_conversation
        )

        assert result.success
        target_file = exports_dir / "last_exchange.md"
        assert target_file.exists()

        content = target_file.read_text()
        assert "# Last Exchange" in content
        assert "Can you also add some comments?" in content
        assert "Of course!" in content

    @pytest.mark.asyncio
    async def test_writeresp_with_alias_json_format(
        self, temp_dir, mock_context_with_conversation
    ):
        """Test writeresp command with alias in JSON format."""
        cmd = WriteResponseCommand("writeresp", "Export last exchange")

        # Create the exports directory
        exports_dir = temp_dir / "exports"
        exports_dir.mkdir(exist_ok=True)

        # Execute writeresp command using alias
        result = await cmd.execute(
            ["exports:last_exchange.json", "json"], mock_context_with_conversation
        )

        assert result.success
        target_file = exports_dir / "last_exchange.json"
        assert target_file.exists()

        # Verify JSON content
        with open(target_file) as f:
            data = json.load(f)

        assert "exchange" in data
        assert "user" in data["exchange"]
        assert "assistant" in data["exchange"]
        assert data["exchange"]["user"]["content"] == "Can you also add some comments?"

    @pytest.mark.asyncio
    async def test_writecode_with_alias(self, temp_dir, mock_context_with_conversation):
        """Test writecode command with directory alias."""
        cmd = WriteCodeCommand("writecode", "Extract code from last response")

        # Create the code directory
        code_dir = temp_dir / "code"
        code_dir.mkdir(exist_ok=True)

        # Execute writecode command using alias
        result = await cmd.execute(["code:hello.py"], mock_context_with_conversation)

        assert result.success
        target_file = code_dir / "hello.py"
        assert target_file.exists()

        content = target_file.read_text()
        assert "def hello_world():" in content
        assert "print('Hello, World!')" in content
        assert "hello_world()" in content

    @pytest.mark.asyncio
    async def test_invalid_alias_error(self, mock_context_with_conversation):
        """Test error handling for invalid aliases."""
        cmd = WriteMarkdownCommand("writemd", "Export conversation to Markdown")

        # Execute with invalid alias
        result = await cmd.execute(
            ["invalid_alias:file.md"], mock_context_with_conversation
        )

        assert not result.success
        assert "Location alias 'invalid_alias' not found" in result.message

    @pytest.mark.asyncio
    async def test_nested_directory_creation_with_alias(
        self, temp_dir, mock_context_with_conversation
    ):
        """Test that parent directories are created when using aliases."""
        cmd = WriteJsonCommand("writejson", "Export conversation to JSON")

        # Execute with nested path using alias (exports directory doesn't exist yet)
        result = await cmd.execute(
            ["exports:nested/deep/conversation.json"], mock_context_with_conversation
        )

        assert result.success
        target_file = temp_dir / "exports" / "nested" / "deep" / "conversation.json"
        assert target_file.exists()
        assert target_file.parent.exists()

    @pytest.mark.asyncio
    async def test_regular_path_still_works(
        self, temp_dir, mock_context_with_conversation
    ):
        """Test that regular paths (without aliases) still work."""
        cmd = WriteMarkdownCommand("writemd", "Export conversation to Markdown")

        target_file = temp_dir / "regular_path.md"

        # Execute with regular path
        result = await cmd.execute([str(target_file)], mock_context_with_conversation)

        assert result.success
        assert target_file.exists()


class TestWriteCommandsWithoutConversation:
    """Test write commands error handling when conversation is empty."""

    @pytest.fixture
    def mock_context_empty(self, mock_config):
        """Create a mock context with no conversation."""
        context = Mock()
        context.config = mock_config
        context.console = Mock()
        context.messages = []
        return context

    @pytest.mark.asyncio
    async def test_writecode_no_assistant_messages(self, temp_dir, mock_context_empty):
        """Test writecode command when no assistant messages exist."""
        cmd = WriteCodeCommand("writecode", "Extract code from last response")

        result = await cmd.execute([str(temp_dir / "test.py")], mock_context_empty)

        assert not result.success
        assert "No assistant responses found" in result.message

    @pytest.mark.asyncio
    async def test_writeresp_no_complete_exchange(self, temp_dir, mock_context_empty):
        """Test writeresp command when no complete exchange exists."""
        cmd = WriteResponseCommand("writeresp", "Export last exchange")

        result = await cmd.execute([str(temp_dir / "test.md")], mock_context_empty)

        assert not result.success
        assert "No complete exchange found" in result.message


if __name__ == "__main__":
    pytest.main([__file__])
