"""
Chat session module for Ocat.

Handles the core chat functionality, including message processing,
LLM interactions, and conversation management.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table

from .config import Config


@dataclass
class Message:
    """
    Represents a single message in the chat conversation.

    Attributes
    ----------
    role : str
        Role of the message sender ("user", "assistant", "system")
    content : str
        Content of the message
    timestamp : float
        Unix timestamp when message was created
    """

    role: str
    content: str
    timestamp: float = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = time.time()


class ChatSession:
    """
    Manages a chat session with an LLM.

    This class handles conversation history, message processing,
    and interaction with the LLM backend.
    """

    def __init__(self, config: Config, console: Console):
        """
        Initialize a new chat session.

        Parameters
        ----------
        config : Config
            Configuration object containing LLM settings
        console : Console
            Rich console instance for output
        """
        self.config = config
        self.console = console
        self.messages: List[Message] = []

        # Add system message if configured (from system prompt files)
        if config.llm.system_prompt_files:
            # Load and concatenate system prompt files
            system_content = self._load_system_prompts(config.llm.system_prompt_files)
            if system_content:
                self.messages.append(Message(role="system", content=system_content))

    def process_message(self, user_input: str) -> None:
        """
        Process a user message and generate a response.

        Parameters
        ----------
        user_input : str
            The user's input message
        """
        # Add user message to conversation
        user_message = Message(role="user", content=user_input)
        self.messages.append(user_message)

        # Display user message
        self._display_message(user_message)

        try:
            # Generate response from LLM
            response = self._generate_response()

            # Add assistant message to conversation
            assistant_message = Message(role="assistant", content=response)
            self.messages.append(assistant_message)

            # Display assistant message
            self._display_message(assistant_message)

        except Exception as e:
            self.console.print(f"Error generating response: {e}", style="red")

    def _generate_response(self) -> str:
        """
        Generate a response from the LLM.

        Returns
        -------
        str
            The generated response

        Note
        ----
        This is a placeholder implementation. In a real implementation,
        this would connect to an actual LLM API (OpenAI, Anthropic, etc.).
        """
        # Placeholder response - in real implementation, this would call the LLM API
        responses = [
            "I'm a placeholder response. To connect to real LLMs, implement the API client in this method.",
            "This is where the actual LLM integration would happen. You'll need to add API calls here.",
            "Hello! I'm currently running in demo mode. Configure your API settings to enable real LLM responses.",
            "I understand you're testing the CLI. The LLM integration is ready to be implemented here.",
        ]

        import random

        return random.choice(responses)

    def _display_message(self, message: Message) -> None:
        """
        Display a message in the console.

        Parameters
        ----------
        message : Message
            The message to display
        """
        if message.role == "user":
            # Display user message with simple formatting
            user_text = Text("You: ", style="bold blue")
            user_text.append(message.content)
            self.console.print(user_text)
            self.console.print()

        elif message.role == "assistant":
            # Display assistant message in a panel with markdown formatting
            try:
                # Try to render as markdown for better formatting
                content = Markdown(message.content)
            except:
                # Fallback to plain text if markdown parsing fails
                content = message.content

            panel = Panel(
                content, title="🤖 Assistant", border_style="green", padding=(1, 2)
            )
            self.console.print(panel)
            self.console.print()

    def show_help(self) -> None:
        """Display help information for available commands."""
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")

        commands = [
            ("help, h", "Show this help message"),
            ("clear", "Clear the screen and show welcome message"),
            ("exit, quit, q", "Exit the application"),
            ("Ctrl+C", "Interrupt current operation"),
            ("Ctrl+D", "Exit the application"),
        ]

        for command, description in commands:
            help_table.add_row(command, description)

        self.console.print(help_table)
        self.console.print()

        # Additional help text
        help_text = [
            "💡 Tips:",
            "• Type your message and press Enter to chat",
            "• Use arrow keys to navigate command history",
            "• Configure your LLM settings in ~/.ocat/config.json",
            "• Set environment variables like OCAT_API_KEY for authentication",
        ]

        for tip in help_text:
            self.console.print(tip, style="dim")
        self.console.print()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history in API format.

        Returns
        -------
        List[Dict[str, Any]]
            List of messages in API format
        """
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def clear_history(self) -> None:
        """Clear the conversation history, keeping only the system message."""
        system_messages = [msg for msg in self.messages if msg.role == "system"]
        self.messages = system_messages
