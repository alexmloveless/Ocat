"""
Test cases for base prompt functionality.

Tests the loading and prepending of base prompts to system prompts.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from ocat.config import Config, ModelConfig
from ocat.chat import ChatSession, Message
from rich.console import Console


class TestBasePrompt:
    """Test cases for base prompt functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.console = Console()

    def test_default_base_prompt_file_path(self):
        """Test that default base prompt file path is set correctly."""
        model_config = ModelConfig()

        # Should set the path to package location
        assert model_config.base_prompt_file != ""
        assert "base_prompt.md" in model_config.base_prompt_file

    def test_base_prompt_loading_default(self):
        """Test loading base prompt with default settings."""
        # Create temporary base prompt file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Base Prompt\nThis is the base prompt content.")
            base_prompt_path = f.name

        try:
            # Create config with custom base prompt file
            config = Config()
            config.llm.base_prompt_file = base_prompt_path
            config.llm.system_prompt_files = []
            config.llm.override_base_prompt = False

            # Create mock chat session to test prompt loading
            with patch("ocat.chat.create_backend"), patch(
                "ocat.chat.ConversationVectorStore"
            ):
                chat = ChatSession(config, self.console, dummy_mode=True)

                # Check that system message contains base prompt
                system_messages = [msg for msg in chat.messages if msg.role == "system"]
                assert len(system_messages) == 1
                assert "This is the base prompt content" in system_messages[0].content

        finally:
            os.unlink(base_prompt_path)

    def test_base_prompt_with_user_prompts(self):
        """Test loading base prompt combined with user system prompts."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as base_f:
            base_f.write("# Base Prompt\nThis is the base prompt.")
            base_prompt_path = base_f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as user_f:
            user_f.write("# User Prompt\nThis is the user prompt.")
            user_prompt_path = user_f.name

        try:
            # Create config with both base and user prompts
            config = Config()
            config.llm.base_prompt_file = base_prompt_path
            config.llm.system_prompt_files = [user_prompt_path]
            config.llm.override_base_prompt = False

            # Create mock chat session
            with patch("ocat.chat.create_backend"), patch(
                "ocat.chat.ConversationVectorStore"
            ):
                chat = ChatSession(config, self.console, dummy_mode=True)

                # Check that system message contains both prompts
                system_messages = [msg for msg in chat.messages if msg.role == "system"]
                assert len(system_messages) == 1
                content = system_messages[0].content
                assert "This is the base prompt" in content
                assert "This is the user prompt" in content
                # Base prompt should come first
                assert content.index("base prompt") < content.index("user prompt")

        finally:
            os.unlink(base_prompt_path)
            os.unlink(user_prompt_path)

    def test_base_prompt_override(self):
        """Test that base prompt can be overridden."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as base_f:
            base_f.write("# Base Prompt\nThis is the base prompt.")
            base_prompt_path = base_f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as user_f:
            user_f.write("# User Prompt\nThis is the user prompt.")
            user_prompt_path = user_f.name

        try:
            # Create config with override enabled
            config = Config()
            config.llm.base_prompt_file = base_prompt_path
            config.llm.system_prompt_files = [user_prompt_path]
            config.llm.override_base_prompt = True

            # Create mock chat session
            with patch("ocat.chat.create_backend"), patch(
                "ocat.chat.ConversationVectorStore"
            ):
                chat = ChatSession(config, self.console, dummy_mode=True)

                # Check that system message contains only user prompt
                system_messages = [msg for msg in chat.messages if msg.role == "system"]
                assert len(system_messages) == 1
                content = system_messages[0].content
                assert "This is the base prompt" not in content
                assert "This is the user prompt" in content

        finally:
            os.unlink(base_prompt_path)
            os.unlink(user_prompt_path)

    def test_base_prompt_override_warning(self):
        """Test that warning is displayed when base prompt is overridden."""
        config = Config()
        config.llm.override_base_prompt = True

        # Mock console to capture warning
        mock_console = MagicMock()

        with patch("ocat.chat.create_backend"), patch(
            "ocat.chat.ConversationVectorStore"
        ):
            chat = ChatSession(config, mock_console, dummy_mode=True)

            # Check that warning was printed
            mock_console.print.assert_called()
            warning_calls = [
                call
                for call in mock_console.print.call_args_list
                if "Warning" in str(call)
            ]
            assert len(warning_calls) > 0

    def test_base_prompt_missing_file_handling(self):
        """Test handling of missing base prompt file."""
        config = Config()
        config.llm.base_prompt_file = "/nonexistent/path/base_prompt.md"
        config.llm.system_prompt_files = []
        config.llm.override_base_prompt = False

        # Should not raise exception, just log warning
        with patch("ocat.chat.create_backend"), patch(
            "ocat.chat.ConversationVectorStore"
        ):
            chat = ChatSession(config, self.console, dummy_mode=True)

            # Should have no system messages since base prompt file doesn't exist
            # and no user prompts are provided
            system_messages = [msg for msg in chat.messages if msg.role == "system"]
            assert len(system_messages) <= 1  # May have empty system message
            if system_messages:
                assert system_messages[0].content.strip() == ""

    def test_config_validation_base_prompt_fields(self):
        """Test that config validation includes base prompt fields."""
        config_data = {
            "llm": {
                "model": "gpt-4o-mini",
                "base_prompt_file": "/custom/path/base_prompt.md",
                "override_base_prompt": True,
            }
        }

        config = Config(**config_data)
        assert config.llm.base_prompt_file == "/custom/path/base_prompt.md"
        assert config.llm.override_base_prompt is True

    def test_base_prompt_includes_timestamp(self):
        """Test that base prompt includes current timestamp."""
        # Create temporary base prompt file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Base Prompt\nThis is the base prompt content.")
            base_prompt_path = f.name

        try:
            # Create config with custom base prompt file
            config = Config()
            config.llm.base_prompt_file = base_prompt_path
            config.llm.system_prompt_files = []
            config.llm.override_base_prompt = False

            # Create mock chat session to test prompt loading
            with patch("ocat.chat.create_backend"), patch(
                "ocat.chat.ConversationVectorStore"
            ):
                chat = ChatSession(config, self.console, dummy_mode=True)

                # Check that system message contains base prompt and timestamp
                system_messages = [msg for msg in chat.messages if msg.role == "system"]
                assert len(system_messages) == 1
                content = system_messages[0].content
                
                # Check that original content is present
                assert "This is the base prompt content" in content
                
                # Check that timestamp information is present
                assert "Current Session Information" in content
                assert "Session started at:" in content
                assert "UTC time:" in content
                
                # Check timestamp format
                import re
                # Look for timestamp pattern (YYYY-MM-DD HH:MM:SS)
                timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
                assert re.search(timestamp_pattern, content) is not None

        finally:
            os.unlink(base_prompt_path)
