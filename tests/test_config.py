"""
Tests for the configuration module of Ocat.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from ocat.config import Config


def test_config_defaults():
    """Test that Config initializes with expected defaults."""
    config = Config()
    
    assert config.model == "gpt-3.5-turbo"
    assert config.api_key is None
    assert config.api_base is None
    assert config.max_tokens == 2048
    assert config.temperature == 0.7
    assert config.system_prompt == "You are a helpful AI assistant."


def test_config_from_file():
    """Test loading configuration from a JSON file."""
    config_data = {
        "model": "gpt-4",
        "api_key": "test-key",
        "max_tokens": 4096,
        "temperature": 0.8,
        "system_prompt": "Custom prompt"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name
    
    try:
        # Clear any existing environment variables that might override file config
        env_vars_to_remove = [
            "OCAT_API_KEY", "OPENAI_API_KEY", "OCAT_MODEL", 
            "OCAT_MAX_TOKENS", "OCAT_TEMPERATURE", "OCAT_SYSTEM_PROMPT"
        ]
        
        # Store original values and clear them
        original_values = {}
        for var in env_vars_to_remove:
            original_values[var] = os.environ.pop(var, None)
        
        try:
            config = Config.load(temp_path)
            
            assert config.model == "gpt-4"
            assert config.api_key == "test-key"
            assert config.max_tokens == 4096
            assert config.temperature == 0.8
            assert config.system_prompt == "Custom prompt"
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
        "OCAT_API_KEY": "env-key",
        "OCAT_MAX_TOKENS": "1024",
        "OCAT_TEMPERATURE": "0.5"
    }
    
    # Clear any existing OpenAI API key that might interfere
    openai_key_backup = os.environ.pop("OPENAI_API_KEY", None)
    
    try:
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            
            assert config.model == "gpt-4"
            assert config.api_key == "env-key"
            assert config.max_tokens == 1024
            assert config.temperature == 0.5
    finally:
        # Restore OpenAI key if it existed
        if openai_key_backup is not None:
            os.environ["OPENAI_API_KEY"] = openai_key_backup


def test_config_openai_api_key():
    """Test that OPENAI_API_KEY environment variable is recognized."""
    # Clear any existing OCAT_API_KEY that might take precedence
    ocat_key_backup = os.environ.pop("OCAT_API_KEY", None)
    
    try:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"}, clear=False):
            config = Config.load()
            assert config.api_key == "openai-key"
    finally:
        # Restore OCAT key if it existed
        if ocat_key_backup is not None:
            os.environ["OCAT_API_KEY"] = ocat_key_backup


def test_config_save():
    """Test saving configuration to a file."""
    config = Config(
        model="gpt-4",
        api_key="test-key",
        max_tokens=1024
    )
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        config.save(temp_path)
        
        # Load the saved file and verify contents
        with open(temp_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["model"] == "gpt-4"
        assert saved_data["api_key"] == "test-key"
        assert saved_data["max_tokens"] == 1024
        
    finally:
        os.unlink(temp_path)


def test_config_to_dict():
    """Test converting configuration to dictionary."""
    config = Config(
        model="gpt-4",
        api_key="test-key"
    )
    
    config_dict = config.to_dict()
    
    assert isinstance(config_dict, dict)
    assert config_dict["model"] == "gpt-4"
    assert config_dict["api_key"] == "test-key"


def test_config_invalid_json():
    """Test handling of invalid JSON in config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Invalid JSON"):
            Config.load(temp_path)
            
    finally:
        os.unlink(temp_path)
