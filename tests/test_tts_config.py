"""
Tests for the TTS configuration of Ocat.
"""

import pytest
import yaml
import tempfile
import os
from pathlib import Path

from ocat.config import Config, TTSConfig
from ocat.exceptions import ConfigError


def test_tts_config_defaults():
    """Test that TTSConfig initializes with expected defaults."""
    tts_config = TTSConfig()
    
    assert tts_config.enabled == True
    assert tts_config.voice == "nova"
    assert tts_config.model == "tts-1"
    assert tts_config.audio_dir == "/tmp"


def test_tts_config_in_main_config():
    """Test that TTS config is included in main Config."""
    config = Config()
    
    assert hasattr(config, 'tts')
    assert isinstance(config.tts, TTSConfig)
    assert config.tts.enabled == True
    assert config.tts.voice == "nova"


def test_tts_config_from_file():
    """Test loading TTS configuration from a YAML file."""
    config_data = {
        "tts": {
            "enabled": False,
            "voice": "fable",
            "model": "tts-1-hd",
            "audio_dir": "/custom/audio"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        config = Config.load(temp_path)
        
        assert config.tts.enabled == False
        assert config.tts.voice == "fable"
        assert config.tts.model == "tts-1-hd"
        assert config.tts.audio_dir == "/custom/audio"
    finally:
        os.unlink(temp_path)


def test_tts_voice_validation():
    """Test TTS voice validation."""
    # Valid voices should work
    valid_voices = ["alloy", "echo", "fable", "nova", "onyx", "shimmer"]
    for voice in valid_voices:
        config = TTSConfig(voice=voice)
        assert config.voice == voice.lower()
    
    # Invalid voice should raise error
    with pytest.raises(ValueError, match="Voice must be one of"):
        TTSConfig(voice="invalid_voice")


def test_tts_model_validation():
    """Test TTS model validation."""
    # Valid models should work
    valid_models = ["tts-1", "tts-1-hd"]
    for model in valid_models:
        config = TTSConfig(model=model)
        assert config.model == model
    
    # Invalid model should raise error
    with pytest.raises(ValueError, match="Model must be one of"):
        TTSConfig(model="invalid_model")


def test_tts_config_save_and_load():
    """Test saving and loading TTS configuration."""
    config = Config()
    config.tts.enabled = False
    config.tts.voice = "shimmer"
    config.tts.model = "tts-1-hd"
    config.tts.audio_dir = "/test/audio"
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = f.name
    
    try:
        config.save(temp_path)
        
        # Load the saved file and verify TTS contents
        loaded_config = Config.load(temp_path)
        
        assert loaded_config.tts.enabled == False
        assert loaded_config.tts.voice == "shimmer"
        assert loaded_config.tts.model == "tts-1-hd"
        assert loaded_config.tts.audio_dir == "/test/audio"
    finally:
        os.unlink(temp_path)
