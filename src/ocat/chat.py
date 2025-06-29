"""
Chat session module for Ocat.

Handles the core chat functionality, including message processing,
LLM interactions, and conversation management.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging
import asyncio

from .utils.logging import setup_logger, LogLevel
from .exceptions import PromptError, LLMError
from .backends import LLMBackend, create_backend, MockLLMBackend
import time

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

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
    timestamp: Optional[float] = None

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

    def __init__(self, config: Config, console: Console, dummy_mode: bool = False):
        """
        Initialize a new chat session.

        Parameters
        ----------
        config : Config
            Configuration object containing LLM settings
        console : Console
            Rich console instance for output
        dummy_mode : bool, default=False
            Whether to use mock backend instead of real LLM API
        """
        self.config = config
        self.console = console
        self.messages: List[Message] = []
        self.dummy_mode = dummy_mode

        # Set up logging for chat session
        self.logger = setup_logger("ocat.chat", LogLevel[config.logging.level], config)
        self.logger.debug("Chat session initialized")

        # Initialize LLM backend
        try:
            if dummy_mode:
                self.llm_backend = MockLLMBackend()
                self.logger.info("Using mock LLM backend for dummy mode")
            else:
                self.llm_backend = create_backend(config)
                self.logger.info(
                    f"Initialized LLM backend for model: {config.llm.model}"
                )
        except LLMError as e:
            self.logger.error(f"Failed to initialize LLM backend: {e}")
            raise

        # Add system message if configured (from system prompt files)
        if config.llm.system_prompt_files:
            # Load and concatenate system prompt files
            system_content = self._load_system_prompts(config.llm.system_prompt_files)
            if system_content:
                self.messages.append(Message(role="system", content=system_content))
                self.logger.info(
                    f"Loaded system prompt from {len(config.llm.system_prompt_files)} file(s)"
                )

    async def process_message(self, user_input: str) -> None:
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
        self.logger.debug(f"User message added to conversation history")

        # Display user message
        self._display_message(user_message)

        try:
            # Generate response from LLM
            self.logger.debug("Generating assistant response")
            response = await self._generate_response()

            # Add assistant message to conversation
            assistant_message = Message(role="assistant", content=response)
            self.messages.append(assistant_message)
            self.logger.debug("Assistant response generated and added to history")

            # Display assistant message
            self._display_message(assistant_message)

        except LLMError as e:
            self.logger.error(f"LLM error: {e}")
            self.console.print(f"LLM error: {e}", style="red")
        except Exception as e:
            self.logger.error(f"Unexpected error generating response: {e}")
            self.console.print(f"Unexpected error: {e}", style="red")

    async def _generate_response(self) -> str:
        """
        Generate a response from the LLM using the configured backend.

        Returns
        -------
        str
            The generated response

        Raises
        ------
        LLMError
            If the LLM API call fails
        """
        # Prepare messages for LLM API
        api_messages = self.get_conversation_history()

        self.logger.debug(f"Sending {len(api_messages)} messages to LLM backend")

        # Show progress indicator for non-dummy mode
        if not self.dummy_mode:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                progress.add_task(description="Generating response...", total=None)

                try:
                    response = await self.llm_backend.generate_response(api_messages)
                except Exception as e:
                    self.logger.error(f"LLM backend error: {e}")
                    raise LLMError(f"Failed to generate response: {e}")
        else:
            # For dummy mode, just call the backend directly
            try:
                response = await self.llm_backend.generate_response(api_messages)
            except Exception as e:
                self.logger.error(f"Mock backend error: {e}")
                raise LLMError(f"Failed to generate mock response: {e}")

        self.logger.debug(f"Received response with {len(response)} characters")
        return response

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
                content: Union[Markdown, str] = Markdown(message.content)
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
            "• Configure your LLM settings in ocat.yaml",
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
        message_count = len(self.messages)
        system_messages = [msg for msg in self.messages if msg.role == "system"]
        self.messages = system_messages
        self.logger.info(
            f"Cleared conversation history ({message_count - len(system_messages)} messages removed)"
        )

    def _load_system_prompts(self, prompt_files: List[str]) -> str:
        """
        Load and concatenate system prompt files.

        Parameters
        ----------
        prompt_files : List[str]
            List of file paths to load system prompts from

        Returns
        -------
        str
            Concatenated system prompt content
        """
        system_prompts = []
        for file_path in prompt_files:
            try:
                with open(file_path, "r") as f:
                    system_prompts.append(f.read())
                self.logger.debug(f"Loaded system prompt from: {file_path}")
            except FileNotFoundError:
                self.logger.warning(f"System prompt file not found: {file_path}")
                continue
            except Exception as e:
                self.logger.error(f"Error loading system prompt from {file_path}: {e}")
                raise PromptError(f"Failed to load system prompt from {file_path}: {e}")

        return "\n\n".join(system_prompts)
