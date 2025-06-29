"""
Mock LLM backend implementation for testing and dummy mode.

This module provides a mock implementation of the LLMBackend interface that returns
predefined responses without making actual API calls. Useful for testing, CI/CD,
and development without API costs.
"""

import asyncio
import random
from typing import AsyncIterator, Dict, List

from . import LLMBackend


class MockLLMBackend(LLMBackend):
    """
    Mock LLM backend that returns predefined responses for testing.

    Parameters
    ----------
    responses : List[str], optional
        List of predefined responses to cycle through. If not provided, uses default responses.
    simulate_streaming : bool, default=True
        Whether to simulate streaming behavior with artificial delays.
    stream_delay : float, default=0.05
        Delay in seconds between streaming chunks.
    """

    def __init__(
        self,
        responses: List[str] = None,
        simulate_streaming: bool = True,
        stream_delay: float = 0.05,
    ):
        self.responses = responses or self._get_default_responses()
        self.call_count = 0
        self.simulate_streaming = simulate_streaming
        self.stream_delay = stream_delay

    def _get_default_responses(self) -> List[str]:
        """
        Get default mock responses for testing.

        Returns
        -------
        List[str]
            List of default mock responses.
        """
        return [
            "This is a mock response from the LLM backend. I'm here to help with testing and development without making actual API calls.",
            "Here's another mock response! This backend is perfect for CI/CD pipelines and local development.",
            "Mock response #3: I can simulate different types of content including **markdown**, `code`, and lists:\n\n1. Item one\n2. Item two\n3. Item three",
            "```python\n# This is a mock code response\ndef hello_world():\n    print('Hello from the mock backend!')\n    return 'success'\n```",
            "This is a longer mock response to test how the system handles various response lengths. It includes multiple sentences and should help validate text wrapping and formatting capabilities.",
            "Short response.",
            "**Bold text**, *italic text*, and `inline code` are all supported in this mock response. Here's a link: [Mock Link](https://example.com)",
            "Error simulation: This response helps test error handling pathways in the application.",
            "Final mock response with some technical content:\n\n## Technical Details\n\n- API responses are mocked\n- No network calls are made\n- Perfect for testing\n- Deterministic behavior",
        ]

    async def generate_response(self, messages: List[Dict]) -> str:
        """
        Generate a mock response.

        Parameters
        ----------
        messages : List[Dict]
            List of message dictionaries (used for logging but not processing).

        Returns
        -------
        str
            A predefined mock response.
        """
        # Cycle through responses based on call count
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        # Add slight delay to simulate API latency
        if self.simulate_streaming:
            await asyncio.sleep(0.1)

        return response

    async def generate_streaming_response(
        self, messages: List[Dict]
    ) -> AsyncIterator[str]:
        """
        Generate a mock streaming response.

        Parameters
        ----------
        messages : List[Dict]
            List of message dictionaries (used for logging but not processing).

        Yields
        ------
        str
            Chunks of the mock response to simulate streaming.
        """
        # Get the response that would be returned by generate_response
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        if not self.simulate_streaming:
            # Return the whole response at once
            yield response
            return

        # Split response into words for streaming simulation
        words = response.split()
        chunk_size = max(1, len(words) // 10)  # Aim for ~10 chunks

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            if i + chunk_size < len(words):
                chunk += " "  # Add space except for last chunk

            yield chunk
            await asyncio.sleep(self.stream_delay)

    def reset_call_count(self) -> None:
        """Reset the call counter to start from the beginning of responses."""
        self.call_count = 0

    def add_response(self, response: str) -> None:
        """
        Add a new response to the list.

        Parameters
        ----------
        response : str
            New response to add to the mock response list.
        """
        self.responses.append(response)

    def set_responses(self, responses: List[str]) -> None:
        """
        Replace all responses with a new list.

        Parameters
        ----------
        responses : List[str]
            New list of responses to use.
        """
        self.responses = responses
        self.call_count = 0
