"""
Ollama backend implementation for Ocat LLM integration.

This module provides the Ollama-specific implementation of the LLMBackend interface,
using the langchain-ollama package for local model interactions.
"""

import os
from typing import AsyncIterator, Dict, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from . import LLMBackend
from ..exceptions import LLMError


class OllamaBackend(LLMBackend):
    """
    Ollama backend implementation using langchain-ollama.

    Parameters
    ----------
    model : str
        The Ollama model name (e.g., 'llama3.2', 'mistral', 'codellama').
    temperature : float
        Controls randomness in responses (0.0-1.0).
    max_tokens : int
        Maximum number of tokens in the response.
    base_url : str, optional
        Ollama server URL. Defaults to http://localhost:11434.

    Raises
    ------
    LLMError
        If Ollama server is not accessible or model initialization fails.
    """

    def __init__(
        self,
        model: str,
        temperature: float = 1.0,
        max_tokens: int = 4000,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        # Use provided base URL or default to localhost
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

        try:
            self.llm = ChatOllama(
                model=model,
                temperature=temperature,
                num_predict=max_tokens,
                base_url=self.base_url,
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize Ollama backend: {e}")

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
        Generate a complete response from Ollama.

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
            raise LLMError(f"Ollama API call failed: {e}")

    async def generate_streaming_response(
        self, messages: List[Dict]
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from Ollama.

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
            raise LLMError(f"Ollama streaming API call failed: {e}")
