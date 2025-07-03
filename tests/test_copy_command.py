"""
Tests for the copy command functionality.
"""

import pytest
from unittest.mock import Mock, patch

from src.ocat.commands.clipboard_commands import CopyCommand, strip_markdown_formatting
from src.ocat.commands import CommandResult
from src.ocat.chat import Message


class TestCopyCommand:
    """Test the copy command."""

    @pytest.fixture
    def copy_command(self):
        """Create a copy command instance."""
        return CopyCommand("copy", "Copy last response to clipboard", "/copy")

    @pytest.fixture
    def mock_context_with_messages(self):
        """Create a mock context with messages."""
        context = Mock()
        context.messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="User question"),
            Message(role="assistant", content="**Bold text** and `code` here."),
        ]
        return context

    @pytest.fixture
    def mock_context_no_assistant(self):
        """Create a mock context with no assistant messages."""
        context = Mock()
        context.messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="User question"),
        ]
        return context

    @pytest.mark.asyncio
    async def test_copy_command_success(self, copy_command, mock_context_with_messages):
        """Test successful copy operation."""
        with patch(
            "src.ocat.commands.clipboard_commands.copy_to_clipboard", return_value=True
        ):
            result = await copy_command.execute([], mock_context_with_messages)

            assert result.success
            assert "Copied last response to clipboard" in result.message
            assert "characters" in result.message

    @pytest.mark.asyncio
    async def test_copy_command_no_assistant_messages(
        self, copy_command, mock_context_no_assistant
    ):
        """Test copy command with no assistant messages."""
        result = await copy_command.execute([], mock_context_no_assistant)

        assert not result.success
        assert result.message == "No assistant responses to copy"

    @pytest.mark.asyncio
    async def test_copy_command_clipboard_failure(
        self, copy_command, mock_context_with_messages
    ):
        """Test copy command when clipboard operation fails."""
        with patch(
            "src.ocat.commands.clipboard_commands.copy_to_clipboard", return_value=False
        ):
            result = await copy_command.execute([], mock_context_with_messages)

            assert not result.success
            assert "Failed to copy to clipboard" in result.message

    def test_strip_markdown_formatting(self):
        """Test markdown formatting removal."""
        markdown_text = """
# Header

**Bold text** and *italic text*.

`inline code` and:

```python
def function():
    return "code block"
```

[Link text](http://example.com)

---

Normal text here.
        """

        plain_text = strip_markdown_formatting(markdown_text)

        # Should remove all markdown formatting
        assert "**" not in plain_text
        assert "*" not in plain_text
        assert "`" not in plain_text
        assert "#" not in plain_text
        assert "[" not in plain_text
        assert "]" not in plain_text
        assert "(" not in plain_text
        assert "---" not in plain_text

        # Should keep the actual text content
        assert "Header" in plain_text
        assert "Bold text" in plain_text
        assert "italic text" in plain_text
        assert "inline code" in plain_text
        assert "Link text" in plain_text
        assert "Normal text here" in plain_text

    def test_strip_markdown_code_blocks(self):
        """Test code block removal specifically."""
        text = "Before ```python\ncode here\n``` after"
        result = strip_markdown_formatting(text)
        assert "Before  after" in result.replace("\n", " ")
        assert "python" not in result
        assert "code here" not in result
