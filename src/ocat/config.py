"""
Configuration module for Ocat.

Handles loading and managing configuration settings for the application,
including LLM model settings, vector store, UI preferences, and more.
"""

import os
import yaml
from pathlib import Path

from importlib.resources import files as resource_files
from typing import Optional, Dict, Any, List
from pydantic import (
    BaseModel,
    Field,
    validator,
    field_validator,
    computed_field,
    ValidationError,
    model_validator,
)

from .exceptions import ConfigError
from .utils import validate_location_aliases


class ModelConfig(BaseModel):
    """
    LLM model configuration.

    Attributes
    ----------
    model : str
        The LLM model to use (default: "gpt-4o-mini")
    temperature : float
        Temperature setting for model responses (0.0-1.0)
    max_tokens : int
        Maximum tokens for responses
    system_prompt_files : List[str]
        List of files containing system prompts to concatenate
    base_prompt_file : str
        Path to base prompt file that is prepended to system prompts
    override_base_prompt : bool
        Whether to override the default base prompt (warns user)
    """

    model: str = Field(default="gpt-4o-mini", description="LLM model name")
    temperature: float = Field(
        default=1.0, ge=0.0, le=2.0, description="Response randomness (0.0-2.0)"
    )
    max_tokens: int = Field(default=4000, gt=0, description="Maximum response tokens")
    system_prompt_files: List[str] = Field(
        default_factory=list, description="System prompt file paths"
    )
    base_prompt_file: str = Field(
        default="",  # Will be set to package default in post_init
        description="Path to base prompt file (prepended to system prompts)",
    )
    override_base_prompt: bool = Field(
        default=False,
        description="Override base prompt (may cause unexpected behavior)",
    )

    @model_validator(mode="after")
    def set_default_base_prompt_file(self):
        """Set default base prompt file to package location if not specified."""
        if not self.base_prompt_file:
            try:
                # Get the package resource path for the base prompt file
                package_files = resource_files("ocat")
                base_prompt_path = package_files / "base_prompt.md"
                self.base_prompt_file = str(base_prompt_path)
            except Exception:
                # Fallback to relative path if package resources fail
                import ocat

                ocat_dir = Path(ocat.__file__).parent
                self.base_prompt_file = str(ocat_dir / "base_prompt.md")
        return self


class VectorStoreConfig(BaseModel):
    """
    Vector store configuration for conversation memory.

    Attributes
    ----------
    enabled : bool
        Enable the vector database for conversation memory
    path : str
        Path to vector store directory
    similarity_threshold : float
        Threshold for similarity matching (0.0-1.0)
    chat_window : int
        Number of recent exchanges to use for context queries
    context_results : int
        Number of similar exchanges to return for context
    search_context_window : int
        Number of recent exchanges to include in context search query
    """

    enabled: bool = Field(default=True, description="Enable vector store")
    path: str = Field(
        default="./vector_stores/default/", description="Vector store directory path"
    )
    similarity_threshold: float = Field(
        default=0.65, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"
    )
    chat_window: int = Field(
        default=3, gt=0, description="Recent exchanges for context queries"
    )
    context_results: int = Field(
        default=5, gt=0, description="Number of context results to return"
    )
    search_context_window: int = Field(
        default=3,
        gt=0,
        description="Number of recent exchanges to include in context search query",
    )
    memory_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for including memories in context (0.0-1.0)",
    )
    memory_results: int = Field(
        default=3, gt=0, description="Maximum number of memories to include in context"
    )


class EmbeddingConfig(BaseModel):
    """
    Embedding model configuration.

    Attributes
    ----------
    model : str
        Embedding model name
    dimensions : int
        Embedding vector dimensions
    chunk_size : int
        Text chunk size for embeddings
    """

    model: str = Field(
        default="text-embedding-3-small", description="Embedding model name"
    )
    dimensions: int = Field(
        default=1536, gt=0, description="Embedding vector dimensions"
    )
    chunk_size: int = Field(default=1000, gt=0, description="Text chunk size")


class DisplayConfig(BaseModel):
    """
    UI and display configuration.

    Attributes
    ----------
    user_label : str
        Label for user input
    assistant_label : str
        Label for assistant responses
    no_rich : bool
        Disable rich text formatting
    no_color : bool
        Disable ANSI color output
    line_width : int
        CLI line width (characters)
    response_on_new_line : bool
        Whether responses start on new line
    exchange_delimiter : str
        Character(s) to use for separating exchanges
    exchange_delimiter_length : int
        Length of exchange delimiter line
    high_contrast : bool
        Use high contrast colors for accessibility
    prompt_symbol : str
        Prompt symbol for chat input (configurable)
    """

    user_label: str = Field(default="User", description="Label for user input")
    assistant_label: str = Field(
        default="Assistant", description="Label for assistant responses"
    )
    no_rich: bool = Field(default=False, description="Disable rich text formatting")
    no_color: bool = Field(default=False, description="Disable ANSI color output")
    line_width: int = Field(default=80, gt=0, description="CLI line width (characters)")
    response_on_new_line: bool = Field(
        default=True, description="Start responses on new line"
    )
    exchange_delimiter: str = Field(
        default="─", description="Character(s) for exchange separation"
    )
    exchange_delimiter_length: int = Field(
        default=60, gt=0, description="Length of exchange delimiter line"
    )
    high_contrast: bool = Field(
        default=True, description="Use high contrast colors for accessibility"
    )
    prompt_symbol: str = Field(
        default="🐱 > ",
        description="Prompt symbol for chat input (configurable from config)",
    )


class LoggingConfig(BaseModel):
    """
    Logging configuration.

    Attributes
    ----------
    level : str
        Logging level (DEBUG, INFO, WARN, ERROR)
    format : str
        Log message format string
    show_context : bool
        Show context information in INFO logging
    """

    level: str = Field(default="WARN", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format",
    )
    show_context: bool = Field(default=False, description="Show context in INFO logs")

    @field_validator("level")
    def validate_log_level(cls, v):
        """Validate log level is one of the accepted values."""
        valid_levels = ["DEBUG", "INFO", "WARN", "ERROR"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class Config(BaseModel):
    """
    Main configuration class for Ocat application.

    Attributes
    ----------
    profile_name : Optional[str]
        Name of the profile for this configuration
    llm : ModelConfig
        LLM model configuration
    vector_store : VectorStoreConfig
        Vector store configuration
    embedding : EmbeddingConfig
        Embedding configuration
    display : DisplayConfig
        Display and UI configuration
    logging : LoggingConfig
        Logging configuration
    locations : Dict[str, str]
        Location aliases for commands
    """

    profile_name: Optional[str] = Field(default=None, description="Profile name")
    llm: ModelConfig = Field(default_factory=ModelConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    locations: Dict[str, str] = Field(
        default_factory=dict, description="Location aliases"
    )

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        cli_overrides: Optional[Dict[str, Any]] = None,
    ) -> "Config":
        """
        Load configuration from YAML file, environment variables, and CLI overrides.

        Precedence order: CLI args > Environment variables > Config file > Defaults

        Parameters
        ----------
        config_path : Optional[str]
            Path to configuration file (optional)
        cli_overrides : Optional[Dict[str, Any]]
            CLI argument overrides (optional)

        Returns
        -------
        Config
            Loaded configuration instance

        Raises
        ------
        ValueError
            If configuration file is invalid
        """
        config_data = {}

        # Try to load from config file
        if config_path:
            config_data = cls._load_from_file(config_path)
        else:
            # Try default YAML locations
            default_paths = [
                Path.home() / ".ocat" / "config.yaml",
                Path.cwd() / "ocat.yaml",
                Path.cwd() / ".ocat.yaml",
            ]

            for path in default_paths:
                if path.exists():
                    config_data = cls._load_from_file(str(path))
                    break

        # Create config instance with file data
        try:
            config = cls(**config_data)
        except ValidationError as e:
            raise ConfigError(f"Configuration validation failed: {e}")

        # Validate location aliases if any are configured
        if config.locations:
            validation_error = validate_location_aliases(config.locations)
            if validation_error:
                raise ConfigError(
                    f"Location alias validation failed: {validation_error}"
                )

        # Override with environment variables (precedence: env > file > defaults)
        config._load_from_env()

        # Override with CLI arguments (precedence: CLI > env > file > defaults)
        if cli_overrides:
            config._load_from_cli(cli_overrides)

        return config

    @classmethod
    def _load_from_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Parameters
        ----------
        file_path : str
            Path to the YAML configuration file

        Returns
        -------
        Dict[str, Any]
            Configuration data from file

        Raises
        ------
        ValueError
            If YAML file is invalid
        """
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
            return data if data is not None else {}

        except FileNotFoundError:
            return {}  # File doesn't exist, use defaults
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML configuration file {file_path}: {e}")

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Model configuration overrides
        model_env = os.getenv("OCAT_MODEL")
        if model_env:
            self.llm.model = model_env
        max_tokens_env = os.getenv("OCAT_MAX_TOKENS")
        if max_tokens_env:
            self.llm.max_tokens = int(max_tokens_env)
        temperature_env = os.getenv("OCAT_TEMPERATURE")
        if temperature_env:
            self.llm.temperature = float(temperature_env)

        # Vector store configuration overrides
        vector_path_env = os.getenv("OCAT_VECTOR_STORE_PATH")
        if vector_path_env:
            self.vector_store.path = vector_path_env
        vector_enabled_env = os.getenv("OCAT_VECTOR_STORE_ENABLED")
        if vector_enabled_env:
            self.vector_store.enabled = vector_enabled_env.lower() == "true"

        # Logging configuration overrides
        log_level_env = os.getenv("OCAT_LOG_LEVEL")
        if log_level_env:
            self.logging.level = log_level_env.upper()

        # Profile name override
        profile_env = os.getenv("OCAT_PROFILE_NAME")
        if profile_env:
            self.profile_name = profile_env

    def _load_from_cli(self, cli_overrides: Dict[str, Any]) -> None:
        """
        Apply CLI argument overrides to configuration.

        Parameters
        ----------
        cli_overrides : Dict[str, Any]
            Dictionary of CLI argument overrides
        """
        # Model configuration overrides
        if cli_overrides.get("model"):
            self.llm.model = cli_overrides["model"]
        if cli_overrides.get("temperature") is not None:
            self.llm.temperature = cli_overrides["temperature"]
        if cli_overrides.get("max_tokens") is not None:
            self.llm.max_tokens = cli_overrides["max_tokens"]

        # Vector store configuration overrides
        if cli_overrides.get("vector_store_path"):
            self.vector_store.path = cli_overrides["vector_store_path"]
        if cli_overrides.get("no_vector_store"):
            self.vector_store.enabled = False
        if cli_overrides.get("similarity_threshold") is not None:
            self.vector_store.similarity_threshold = cli_overrides[
                "similarity_threshold"
            ]

        # Logging configuration overrides
        if cli_overrides.get("log_level"):
            self.logging.level = cli_overrides["log_level"]

        # Display configuration overrides
        if cli_overrides.get("no_rich"):
            self.display.no_rich = True
        if cli_overrides.get("no_color"):
            self.display.no_color = True
        if cli_overrides.get("line_width") is not None:
            self.display.line_width = cli_overrides["line_width"]

        # Profile name override
        if cli_overrides.get("profile"):
            self.profile_name = cli_overrides["profile"]

    def save(self, file_path: str) -> None:
        """
        Save configuration to YAML file.

        Parameters
        ----------
        file_path : str
            Path where to save the configuration
        """
        # Create directory if it doesn't exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns
        -------
        Dict[str, Any]
            Configuration as dictionary
        """
        return self.model_dump()
