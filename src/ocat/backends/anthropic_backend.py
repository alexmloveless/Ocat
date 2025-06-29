"""
Anthropic backend implementation for Ocat LLM integration.

This module provides the Anthropic-specific implementation of the LLMBackend interface,
using the langchain-anthropic package for API interactions.
"""

import os
from typing import AsyncIterator, Dict, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from . import LLMBackend
from ..exceptions import LLMError


class AnthropicBackend(LLMBackend):
    """
    Anthropic backend implementation using langchain-anthropic.

    Parameters
    ----------
    model : str
        The Anthropic model name (e.g., 'claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307').
    temperature : float
        Controls randomness in responses (0.0-1.0).
    max_tokens : int
        Maximum number of tokens in the response.
    api_key : str, optional
        Anthropic API key. If not provided, will use ANTHROPIC_API_KEY environment variable.

    Raises
    ------
    LLMError
        If API key is not provided or invalid.
    """

    def __init__(
        self,
        model: str,
        temperature: float = 1.0,
        max_tokens: int = 4000,
        api_key: str = None,
    ):
        # Use provided API key or fall back to environment variable
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise LLMError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        try:
            self.llm = ChatAnthropic(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=self.api_key,
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize Anthropic backend: {e}")

    def _convert_messages(self, messages: List[Dict]) -> List:
        """
        Convert message dictionaries to LangChain message objects.

        Parameters
        ----------
        messages : List[Dict]
            List of message dictionaries with 'role' and 'content' keys.

        Returns
        -------
        List
            List of LangChain message objects.
        """
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                # Default to human message for unknown roles
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    async def generate_response(self, messages: List[Dict]) -> str:
        """
        Generate a complete response from Anthropic.

        Parameters
        ----------
        messages : List[Dict]
            List of message dictionaries containing conversation history.

        Returns
        -------
        str
            The generated response content.

        Raises
        ------
        LLMError
            If the API call fails or returns an invalid response.
        """
        try:
            langchain_messages = self._convert_messages(messages)
            response = await self.llm.ainvoke(langchain_messages)
            return response.content
        except Exception as e:
            raise LLMError(f"Anthropic API call failed: {e}")

    async def generate_streaming_response(
        self, messages: List[Dict]
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from Anthropic.

        Parameters
        ----------
        messages : List[Dict]
            List of message dictionaries containing conversation history.

        Yields
        ------
        str
            Chunks of the response as they are generated.

        Raises
        ------
        LLMError
            If the API call fails or returns an invalid response.
        """
        try:
            langchain_messages = self._convert_messages(messages)
            async for chunk in self.llm.astream(langchain_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            raise LLMError(f"Anthropic streaming API call failed: {e}")
