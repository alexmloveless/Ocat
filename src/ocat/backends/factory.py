"""
Backend factory for automatic LLM provider selection and backend creation.

This module provides factory functions to automatically detect the appropriate
LLM provider based on the model name and create the corresponding backend instance.
"""

from typing import Optional

from . import LLMBackend
from .openai_backend import OpenAIBackend
from .anthropic_backend import AnthropicBackend
from .google_backend import GoogleBackend
from ..config import OcatConfig
from ..exceptions import LLMError

# Model name patterns for automatic provider detection
OPENAI_MODELS = {
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4-turbo", 
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-1106-preview",
    "gpt-4-0613",
    "gpt-3.5-turbo-16k",
}

ANTHROPIC_MODELS = {
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022", 
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-2.1",
    "claude-2.0",
    "claude-instant-1.2",
}

GOOGLE_MODELS = {
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "gemini-pro",
    "gemini-pro-vision",
}


def detect_provider_from_model(model: str) -> str:
    """
    Detect the LLM provider based on the model name.

    Parameters
    ----------
    model : str
        The model name to analyze.

    Returns
    -------
    str
        The provider name ('openai', 'anthropic', 'google').

    Raises
    ------
    LLMError
        If the model is not recognized or provider cannot be determined.
    """
    model_lower = model.lower()
    
    # Check for exact matches first
    if model in OPENAI_MODELS:
        return "openai"
    if model in ANTHROPIC_MODELS:
        return "anthropic"
    if model in GOOGLE_MODELS:
        return "google"
    
    # Check for partial matches by common prefixes
    if model_lower.startswith(("gpt-", "o1-")):
        return "openai"
    elif model_lower.startswith("claude"):
        return "anthropic"
    elif model_lower.startswith(("gemini", "palm", "bison")):
        return "google"
    
    # If no match found, raise an error
    raise LLMError(
        f"Unable to detect provider for model '{model}'. "
        f"Supported providers: OpenAI (gpt-*), Anthropic (claude-*), Google (gemini-*)"
    )


def create_backend(config: OcatConfig, api_key: Optional[str] = None) -> LLMBackend:
    """
    Create the appropriate LLM backend based on configuration.

    Parameters
    ----------
    config : OcatConfig
        The Ocat configuration object containing model and LLM settings.
    api_key : str, optional
        Optional API key override. If not provided, will use environment variables.

    Returns
    -------
    LLMBackend
        An instance of the appropriate backend implementation.

    Raises
    ------
    LLMError
        If the provider cannot be determined or backend creation fails.
    """
    model = config.llm.model
    provider = detect_provider_from_model(model)
    
    backend_kwargs = {
        "model": model,
        "temperature": config.llm.temperature,
        "max_tokens": config.llm.max_tokens,
    }
    
    if api_key:
        backend_kwargs["api_key"] = api_key
    
    if provider == "openai":
        return OpenAIBackend(**backend_kwargs)
    elif provider == "anthropic":
        return AnthropicBackend(**backend_kwargs)
    elif provider == "google":
        return GoogleBackend(**backend_kwargs)
    else:
        raise LLMError(f"Unsupported provider: {provider}")


def create_backend_for_model(
    model: str,
    temperature: float = 1.0,
    max_tokens: int = 4000,
    api_key: Optional[str] = None,
) -> LLMBackend:
    """
    Create a backend instance for a specific model with custom parameters.

    This is a convenience function for creating backends without a full config object.

    Parameters
    ----------
    model : str
        The model name to use.
    temperature : float, default=1.0
        Controls randomness in responses (0.0-1.0).
    max_tokens : int, default=4000
        Maximum number of tokens in the response.
    api_key : str, optional
        Optional API key override.

    Returns
    -------
    LLMBackend
        An instance of the appropriate backend implementation.

    Raises
    ------
    LLMError
        If the provider cannot be determined or backend creation fails.
    """
    provider = detect_provider_from_model(model)
    
    backend_kwargs = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    if api_key:
        backend_kwargs["api_key"] = api_key
    
    if provider == "openai":
        return OpenAIBackend(**backend_kwargs)
    elif provider == "anthropic":
        return AnthropicBackend(**backend_kwargs)
    elif provider == "google":
        return GoogleBackend(**backend_kwargs)
    else:
        raise LLMError(f"Unsupported provider: {provider}")
