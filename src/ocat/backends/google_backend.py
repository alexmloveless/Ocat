"""
Google backend implementation for Ocat LLM integration.

This module provides the Google-specific implementation of the LLMBackend interface,
using the langchain-google-genai package for API interactions.
"""

import os
from typing import AsyncIterator, Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from . import LLMBackend
from ..exceptions import LLMError


class GoogleBackend(LLMBackend):
    """
    Google backend implementation using langchain-google-genai.

    Parameters
    ----------
    model : str
        The Google model name (e.g., 'gemini-1.5-flash', 'gemini-1.5-pro').
    temperature : float
        Controls randomness in responses (0.0-1.0).
    max_tokens : int
        Maximum number of tokens in the response.
    api_key : str, optional
        Google API key. If not provided, will use GOOGLE_API_KEY environment variable.

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
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise LLMError(
                "Google API key not provided. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                max_output_tokens=max_tokens,  # Google uses max_output_tokens instead of max_tokens
                google_api_key=self.api_key,
            )
        except Exception as e:
            raise LLMError(f"Failed to initialize Google backend: {e}")

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
        Generate a complete response from Google.

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
            raise LLMError(f"Google API call failed: {e}")

    async def generate_streaming_response(
        self, messages: List[Dict]
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from Google.

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
            raise LLMError(f"Google streaming API call failed: {e}")
