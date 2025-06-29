"""
Tests for the CLI module of Ocat.
"""

import pytest
from unittest.mock import Mock, patch
from io import StringIO

from ocat.cli import create_parser, main
from ocat.config import Config


def test_create_parser():
    """Test that the argument parser is created correctly."""
    parser = create_parser()

    # Test that parser exists and has expected attributes
    assert parser.prog == "ocat"
    assert "interactive LLM Chat CLI tool" in parser.description


def test_parser_arguments():
    """Test that the parser handles arguments correctly."""
    parser = create_parser()

    # Test version argument
    with pytest.raises(SystemExit):
        parser.parse_args(["--version"])

    # Test config argument
    args = parser.parse_args(["--config", "test_config.json"])
    assert args.config == "test_config.json"

    # Test model argument
    args = parser.parse_args(["--model", "gpt-4"])
    assert args.model == "gpt-4"

    # Test debug flag
    args = parser.parse_args(["--debug"])
    assert args.debug is True


@patch("ocat.cli.Config.load")
@patch("ocat.cli.ChatSession")
@patch("ocat.cli.PromptSession")
@patch("ocat.cli.Console")
def test_main_basic_flow(
    mock_console, mock_prompt_session, mock_chat_session, mock_config_load
):
    """Test the basic flow of the main function."""
    # Setup mocks
    mock_config = Mock(spec=Config)
    # Add logging configuration to mock
    mock_logging = Mock()
    mock_logging.level = "WARN"
    mock_logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    mock_logging.show_context = False
    mock_config.logging = mock_logging
    mock_config.llm = Mock()
    mock_config.llm.model = "gpt-4o-mini"
    mock_config_load.return_value = mock_config

    mock_prompt = Mock()
    mock_prompt_session.return_value = mock_prompt
    mock_prompt.prompt.side_effect = ["test message", "exit"]

    mock_chat = Mock()
    mock_chat_session.return_value = mock_chat

    # Run main function
    result = main(["--debug"])

    # Verify interactions
    assert result == 0
    mock_config_load.assert_called_once()
    mock_chat_session.assert_called_once()
    mock_chat.process_message.assert_called_once_with("test message")


@patch("ocat.cli.Config.load")
def test_main_with_config_override(mock_config_load):
    """Test that command line arguments override config."""
    mock_config = Mock(spec=Config)
    mock_config_load.return_value = mock_config

    with patch("ocat.cli.ChatSession"), patch(
        "ocat.cli.PromptSession"
    ) as mock_prompt_session, patch("ocat.cli.Console"):

        mock_prompt = Mock()
        mock_prompt_session.return_value = mock_prompt
        mock_prompt.prompt.return_value = "exit"

        result = main(["--model", "gpt-4", "--config", "custom.json"])

        # Verify config was loaded with custom path and CLI overrides
        mock_config_load.assert_called_once_with("custom.json", {"model": "gpt-4"})
