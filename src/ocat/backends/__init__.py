"""
Module containing the base LLMBackend interface and utility classes for different backend implementations.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List


class LLMBackend(ABC):
    """
    Abstract base class defining the interface for LLM backend implementations.

    Methods
    -------
    generate_response(messages: List[Dict]) -> str
        Generates a synchronous response from the LLM.

    generate_streaming_response(messages: List[Dict]) -> AsyncIterator[str]
        Generates an asynchronous streaming response from the LLM.
    """

    @abstractmethod
    async def generate_response(self, messages: List[Dict]) -> str:
        pass

    @abstractmethod
    async def generate_streaming_response(
        self, messages: List[Dict]
    ) -> AsyncIterator[str]:
        pass


# Import all backend implementations
from .openai_backend import OpenAIBackend
from .anthropic_backend import AnthropicBackend
from .google_backend import GoogleBackend
from .mock_backend import MockLLMBackend
from .factory import (
    create_backend,
    create_backend_for_model,
    detect_provider_from_model,
)

__all__ = [
    "LLMBackend",
    "OpenAIBackend",
    "AnthropicBackend",
    "GoogleBackend",
    "MockLLMBackend",
    "create_backend",
    "create_backend_for_model",
    "detect_provider_from_model",
]
