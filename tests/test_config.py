"""
Tests for the configuration module of Ocat.
"""

import pytest
import yaml
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from ocat.config import Config


def test_config_defaults():
    """Test that Config initializes with expected defaults."""
    config = Config()

    assert config.llm.model == "gpt-4o-mini"
    assert config.llm.temperature == 1.0
    assert config.llm.max_tokens == 4000
    assert config.llm.system_prompt_files == []
    assert config.display.assistant_label == "Assistant"
    assert config.display.user_label == "User"
    assert config.vector_store.enabled == True
    assert config.logging.level == "WARN"


def test_config_from_file():
    """Test loading configuration from a YAML file."""
    config_data = {
        "llm": {
            "model": "gpt-4",
            "max_tokens": 4096,
            "temperature": 0.8,
            "system_prompt_files": ["prompt1.txt"],
        },
        "display": {"assistant_label": "AI", "line_width": 100},
        "vector_store": {"enabled": False},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    try:
        # Clear any existing environment variables that might override file config
        env_vars_to_remove = ["OCAT_MODEL", "OCAT_MAX_TOKENS", "OCAT_TEMPERATURE"]

        # Store original values and clear them
        original_values = {}
        for var in env_vars_to_remove:
            original_values[var] = os.environ.pop(var, None)

        try:
            config = Config.load(temp_path)

            assert config.llm.model == "gpt-4"
            assert config.llm.max_tokens == 4096
            assert config.llm.temperature == 0.8
            assert config.llm.system_prompt_files == ["prompt1.txt"]
            assert config.display.assistant_label == "AI"
            assert config.display.line_width == 100
            assert config.vector_store.enabled == False
        finally:
            # Restore original values
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    finally:
        os.unlink(temp_path)


def test_config_from_env():
    """Test loading configuration from environment variables."""
    env_vars = {
        "OCAT_MODEL": "gpt-4",
        "OCAT_MAX_TOKENS": "1024",
        "OCAT_TEMPERATURE": "0.5",
        "OCAT_LOG_LEVEL": "DEBUG",
        "OCAT_PROFILE_NAME": "test-profile",
    }

    try:
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()

            assert config.llm.model == "gpt-4"
            assert config.llm.max_tokens == 1024
            assert config.llm.temperature == 0.5
            assert config.logging.level == "DEBUG"
            assert config.profile_name == "test-profile"
    finally:
        pass


def test_config_vector_store_env():
    """Test vector store configuration from environment variables."""
    env_vars = {
        "OCAT_VECTOR_STORE_PATH": "/custom/path",
        "OCAT_VECTOR_STORE_ENABLED": "false",
    }

    try:
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            assert config.vector_store.path == "/custom/path"
            assert config.vector_store.enabled == False
    finally:
        pass


def test_config_save():
    """Test saving configuration to a YAML file."""
    # Create config with non-default values
    config = Config()
    config.llm.model = "gpt-4"
    config.llm.max_tokens = 1024
    config.display.assistant_label = "AI"
    config.profile_name = "test"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = f.name

    try:
        config.save(temp_path)

        # Load the saved file and verify contents
        with open(temp_path, "r") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["llm"]["model"] == "gpt-4"
        assert saved_data["llm"]["max_tokens"] == 1024
        assert saved_data["display"]["assistant_label"] == "AI"
        assert saved_data["profile_name"] == "test"

    finally:
        os.unlink(temp_path)


def test_config_to_dict():
    """Test converting configuration to dictionary."""
    config = Config()
    config.llm.model = "gpt-4"
    config.profile_name = "test"

    config_dict = config.to_dict()

    assert isinstance(config_dict, dict)
    assert config_dict["llm"]["model"] == "gpt-4"
    assert config_dict["profile_name"] == "test"
    assert "display" in config_dict
    assert "vector_store" in config_dict


def test_config_invalid_yaml():
    """Test handling of invalid YAML in config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: {")  # Invalid YAML syntax
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Invalid YAML"):
            Config.load(temp_path)

    finally:
        os.unlink(temp_path)
