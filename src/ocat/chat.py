"""
Chat session module for Ocat.

Handles the core chat functionality, including message processing,
LLM interactions, and conversation management.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging
import asyncio
import uuid

from .utils.logging import setup_logger, LogLevel
from .exceptions import PromptError, LLMError, VectorStoreError
from .backends import LLMBackend, create_backend, MockLLMBackend
from .vector_store import ConversationVectorStore, Exchange
from .commands.parser import CommandParser
from .productivity.integration import (
    create_productivity_integration,
    ProductivityIntegration,
)
from .file_tools.integration import (
    create_file_integration_for_session,
    FileIntegration,
)
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

        # Initialize current working directory for file operations
        from pathlib import Path

        self.current_directory = Path.cwd()

        # Generate session and thread IDs for vector store
        self.session_id = str(uuid.uuid4())
        self.thread_id = str(uuid.uuid4())
        self.logger.debug(f"Session ID: {self.session_id}, Thread ID: {self.thread_id}")

        # Initialize vector store for conversation memory
        self.vector_store: Optional[ConversationVectorStore] = None
        try:
            if config.vector_store.enabled:
                self.vector_store = ConversationVectorStore(config)
                self.logger.info("Vector store initialized for conversation memory")
            else:
                self.logger.info("Vector store disabled in configuration")
        except VectorStoreError as e:
            self.logger.error(f"Failed to initialize vector store: {e}")
            # Continue without vector store

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

        # Initialize command parser for slash commands
        self.command_parser = CommandParser(config)
        self.logger.debug("Command parser initialized")

        # Initialize productivity integration
        self.productivity_integration: Optional[ProductivityIntegration] = None
        try:
            self.productivity_integration = create_productivity_integration(self)
        except Exception as e:
            self.logger.warning(f"Productivity integration disabled: {e}")
            # Continue without productivity features

        # Initialize file tools integration
        self.file_integration: Optional[FileIntegration] = None
        try:
            self.file_integration = create_file_integration_for_session(
                config, self.current_directory
            )
        except Exception as e:
            self.logger.warning(f"File tools integration disabled: {e}")
            # Continue without file tools

        # Warn user if base prompt is overridden
        if config.llm.override_base_prompt:
            self.console.print(
                "⚠️  Warning: Base prompt override is enabled. This may cause Ocat to behave unexpectedly.",
                style="yellow",
            )
            self.logger.warning(
                "Base prompt override enabled - may cause unexpected behavior"
            )

        # Load system prompts (base prompt + user-defined prompts)
        system_content = self._load_system_prompts(
            config.llm.base_prompt_file,
            config.llm.system_prompt_files,
            config.llm.override_base_prompt,
        )

        # Add productivity capabilities to system prompt if available
        if self.productivity_integration:
            system_content += self.productivity_integration.get_system_prompt_addition()

        # Add file tools capabilities to system prompt if available
        if self.file_integration:
            system_content += "\n\n## File Operations Available\n"
            system_content += "You can read, write, and explore files directly. When users ask to read files, "
            system_content += "summarize content, or work with the file system, you have access to these capabilities "
            system_content += (
                "through integrated tools. Use them naturally in conversation."
            )

        if system_content:
            self.messages.append(Message(role="system", content=system_content))
            prompt_count = len(config.llm.system_prompt_files)
            base_prompt_info = (
                "" if config.llm.override_base_prompt else " (including base prompt)"
            )
            productivity_info = (
                " with productivity features" if self.productivity_integration else ""
            )
            file_tools_info = " and file tools" if self.file_integration else ""
            self.logger.info(
                f"Loaded system prompt from {prompt_count} user file(s){base_prompt_info}{productivity_info}{file_tools_info}"
            )

    async def process_message(self, user_input: str) -> None:
        """
        Process a user message and generate a response.

        Parameters
        ----------
        user_input : str
            The user's input message
        """
        # Check if this is a slash command
        if self.command_parser.is_command(user_input):
            try:
                self.logger.debug(f"Processing slash command: {user_input}")
                result = await self.command_parser.execute_command(user_input, self)

                if not result.success:
                    self.console.print(
                        f"❌ Command error: {result.message}", style="red"
                    )
                elif result.message:
                    self.console.print(f"✅ {result.message}", style="green")

                return
            except Exception as e:
                self.logger.error(f"Unexpected error processing command: {e}")
                self.console.print(f"❌ Command error: {e}", style="red")
                return

        # Check if this is a productivity request
        if (
            self.productivity_integration
            and self.productivity_integration.should_use_productivity_agent(user_input)
        ):
            try:
                self.logger.debug(
                    f"Routing to productivity agent: {user_input[:50]}..."
                )

                # Process with productivity agent
                productivity_response = (
                    await self.productivity_integration.process_productivity_request(
                        user_input, self
                    )
                )

                if productivity_response:
                    # Add both user message and productivity response to conversation
                    user_message = Message(role="user", content=user_input)
                    self.messages.append(user_message)

                    assistant_message = Message(
                        role="assistant", content=productivity_response
                    )
                    self.messages.append(assistant_message)

                    # Display the response
                    self._display_message(assistant_message)

                    # Store exchange in vector store
                    if self.vector_store:
                        try:
                            exchange_id = self.vector_store.add_exchange(
                                user_prompt=user_input,
                                assistant_response=productivity_response,
                                thread_id=self.thread_id,
                                session_id=self.session_id,
                            )
                            self.logger.debug(
                                f"Stored productivity exchange {exchange_id} in vector store"
                            )
                        except VectorStoreError as e:
                            self.logger.warning(
                                f"Failed to store productivity exchange: {e}"
                            )

                    return
                else:
                    # Productivity agent failed, fall through to regular processing
                    self.logger.warning(
                        "Productivity agent returned no response, using regular LLM"
                    )
            except Exception as e:
                self.logger.error(f"Productivity agent error: {e}")
                # Fall through to regular processing

        # Check for file operation intent
        if self.file_integration and self.file_integration.detect_file_intent(
            user_input
        ):
            try:
                self.logger.debug(f"Routing to file agent: {user_input[:50]}...")

                # Update current directory in file integration
                self.file_integration.update_current_directory(self.current_directory)

                # Process with file agent
                file_response = await self.file_integration.handle_file_request(
                    user_input
                )

                if file_response:
                    # Add both user message and file response to conversation
                    user_message = Message(role="user", content=user_input)
                    self.messages.append(user_message)

                    assistant_message = Message(role="assistant", content=file_response)
                    self.messages.append(assistant_message)

                    # Display the response
                    self._display_message(assistant_message)

                    # Store exchange in vector store
                    if self.vector_store:
                        try:
                            exchange_id = self.vector_store.add_exchange(
                                user_prompt=user_input,
                                assistant_response=file_response,
                                thread_id=self.thread_id,
                                session_id=self.session_id,
                            )
                            self.logger.debug(
                                f"Stored file operation exchange {exchange_id} in vector store"
                            )
                        except VectorStoreError as e:
                            self.logger.warning(
                                f"Failed to store file operation exchange: {e}"
                            )

                    return
                else:
                    # File agent failed, fall through to regular processing
                    self.logger.warning(
                        "File agent returned no response, using regular LLM"
                    )
            except Exception as e:
                self.logger.error(f"File agent error: {e}")
                # Fall through to regular processing

        # Regular message processing
        # Add user message to conversation
        user_message = Message(role="user", content=user_input)
        self.messages.append(user_message)
        self.logger.debug(f"User message added to conversation history")

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

            # Store exchange in vector store for future context retrieval
            if self.vector_store:
                try:
                    exchange_id = self.vector_store.add_exchange(
                        user_prompt=user_input,
                        assistant_response=response,
                        thread_id=self.thread_id,
                        session_id=self.session_id,
                    )
                    self.logger.debug(f"Stored exchange {exchange_id} in vector store")
                except VectorStoreError as e:
                    self.logger.warning(
                        f"Failed to store exchange in vector store: {e}"
                    )
                    # Continue without storing - not critical for functionality

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
        # Get recent conversation for context search query
        # Include last n exchanges (both user and assistant) for better context matching
        search_window = self.config.vector_store.search_context_window
        recent_exchanges = []

        # Get the last n complete exchanges (user + assistant pairs)
        messages_for_search = [
            msg for msg in self.messages if msg.role in ["user", "assistant"]
        ]
        if len(messages_for_search) >= 2:
            # Take the last search_context_window * 2 messages to get complete exchanges
            recent_exchanges = messages_for_search[-(search_window * 2) :]
        elif messages_for_search:
            # If we have fewer messages, take what we have
            recent_exchanges = messages_for_search

        # Create enhanced query text including conversation flow
        if recent_exchanges:
            query_parts = []
            for i in range(0, len(recent_exchanges), 2):
                if i + 1 < len(recent_exchanges):
                    # Complete exchange (user + assistant)
                    user_msg = recent_exchanges[i].content
                    assistant_msg = recent_exchanges[i + 1].content
                    query_parts.append(f"User: {user_msg}")
                    query_parts.append(f"Assistant: {assistant_msg}")
                else:
                    # Incomplete exchange (just user message)
                    query_parts.append(f"User: {recent_exchanges[i].content}")

            query_text = " ".join(query_parts)
        else:
            # Fallback to empty query if no recent messages
            query_text = ""

        self.logger.debug(
            f"Context search query includes {len(recent_exchanges)} recent messages"
        )

        # Retrieve similar exchanges for context if vector store is enabled
        context_exchanges = await self._retrieve_context(query_text)

        # Prepare messages for LLM API, including context if available
        api_messages = self._prepare_messages_with_context(context_exchanges)

        self.logger.debug(f"Sending {len(api_messages)} messages to LLM backend")

        # Show progress indicator for non-dummy mode with better cancellation support
        if not self.dummy_mode:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}", style="cyan"),
                TextColumn("[dim](Press Ctrl+C to cancel)[/dim]"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    description="Generating response...", total=None
                )

                try:
                    # Add timeout and better error handling
                    response = await asyncio.wait_for(
                        self.llm_backend.generate_response(api_messages),
                        timeout=120.0,  # 2 minute timeout
                    )
                except asyncio.TimeoutError:
                    self.logger.error("LLM request timed out")
                    raise LLMError("Request timed out after 2 minutes")
                except asyncio.CancelledError:
                    self.logger.info("LLM request cancelled by user")
                    raise LLMError("Request cancelled by user")
                except Exception as e:
                    self.logger.error(f"LLM backend error: {e}")
                    raise LLMError(f"Failed to generate response: {e}")
        else:
            # For dummy mode, show a brief progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}", style="yellow"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    description="Generating mock response...", total=None
                )

                try:
                    # Add a small delay to simulate processing
                    await asyncio.sleep(0.5)
                    response = await self.llm_backend.generate_response(api_messages)
                except Exception as e:
                    self.logger.error(f"Mock backend error: {e}")
                    raise LLMError(f"Failed to generate mock response: {e}")

        self.logger.debug(f"Received response with {len(response)} characters")
        return response

    def _display_message(self, message: Message) -> None:
        """
        Display a message in the console with enhanced formatting.

        Parameters
        ----------
        message : Message
            The message to display
        """
        if message.role == "user":
            # Display user message with configurable formatting
            if self.config.display.response_on_new_line:
                # User label on its own line
                user_label = Text(
                    f"{self.config.display.user_label}:", style="bold bright_blue"
                )
                self.console.print(user_label)
                self.console.print(message.content, style="white")
            else:
                # User label on same line
                user_text = Text(
                    f"{self.config.display.user_label}: ", style="bold bright_blue"
                )
                user_text.append(message.content, style="white")
                self.console.print(user_text)

            # Add spacing for better readability
            self.console.print()

        elif message.role == "assistant":
            # Enhanced assistant message display with better spacing
            try:
                # Try to render as markdown for better formatting
                code_theme = (
                    "monokai" if self.config.display.high_contrast else "default"
                )
                content: Union[Markdown, str] = Markdown(
                    message.content, code_theme=code_theme
                )
            except Exception:
                # Fallback to plain text if markdown parsing fails
                content = message.content

            # Use configurable assistant label
            assistant_title = f"🤖 {self.config.display.assistant_label}"

            # Choose colors based on high contrast setting
            border_style = (
                "bright_green" if self.config.display.high_contrast else "green"
            )

            # Create panel with accessibility-friendly styling
            panel = Panel(
                content,
                title=assistant_title,
                border_style=border_style,
                padding=(1, 2),
                width=(
                    self.config.display.line_width
                    if self.config.display.line_width > 0
                    else None
                ),
            )

            if self.config.display.response_on_new_line:
                self.console.print()  # Extra line before response for clarity

            self.console.print(panel)

            # Add configurable exchange delimiter for visual separation
            delimiter_length = min(
                self.config.display.exchange_delimiter_length,
                self.config.display.line_width,
            )
            delimiter = self.config.display.exchange_delimiter * delimiter_length

            delimiter_style = (
                "dim bright_black" if self.config.display.high_contrast else "dim"
            )
            self.console.print(delimiter, style=delimiter_style)
            self.console.print()  # Extra spacing after each exchange

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

    async def _retrieve_context(self, query_text: str) -> List[Exchange]:
        """
        Retrieve relevant conversation context using enhanced LangGraph memory.

        Parameters
        ----------
        query_text : str
            The query text to retrieve context for

        Returns
        -------
        List[Exchange]
            List of similar exchanges based on context

        """
        if self.vector_store:
            try:
                similar_exchanges = self.vector_store.get_episodic_context(
                    query_text=query_text,
                    max_context_length=min(
                        2000, self.config.llm.max_tokens // 4
                    ),  # Estimate max length conservatively
                    relevance_threshold=self.config.vector_store.similarity_threshold,
                )
                self.logger.debug(
                    f"Retrieved {len(similar_exchanges)} similar exchanges"
                )
                return similar_exchanges
            except VectorStoreError as e:
                self.logger.warning(
                    f"Failed to retrieve context from vector store: {e}"
                )
        return []

    def _load_system_prompts(
        self, base_prompt_file: str, prompt_files: List[str], override_base_prompt: bool
    ) -> str:
        """
        Load and concatenate the base prompt and system prompt files.

        Parameters
        ----------
        base_prompt_file : str
            Path to the base prompt file
        prompt_files : List[str]
            List of file paths to load system prompts from
        override_base_prompt : bool
            Whether to ignore base prompt and use only user-defined prompts

        Returns
        -------
        str
            Concatenated system prompt content
        """
        from datetime import datetime
        import pytz

        system_prompts = []

        # Load base prompt unless overridden
        if not override_base_prompt:
            try:
                with open(base_prompt_file, "r") as f:
                    base_prompt_content = f.read()

                # Add current date and time to the base prompt
                utc_now = datetime.now(pytz.UTC)
                local_now = datetime.now()

                # Format timestamps for better readability
                utc_timestamp = utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
                local_timestamp = local_now.strftime("%Y-%m-%d %H:%M:%S %Z")

                # Add time context to the base prompt
                time_context = f"\n\n## Current Session Information\n\nSession started at: {local_timestamp}\nUTC time: {utc_timestamp}\n"

                # Append time information to the base prompt
                enhanced_base_prompt = base_prompt_content + time_context
                system_prompts.append(enhanced_base_prompt)

                self.logger.debug(
                    f"Loaded base prompt from: {base_prompt_file} with current timestamp"
                )
            except FileNotFoundError:
                self.logger.warning(f"Base prompt file not found: {base_prompt_file}")
            except Exception as e:
                self.logger.error(
                    f"Error loading base prompt from {base_prompt_file}: {e}"
                )
                raise PromptError(
                    f"Failed to load base prompt from {base_prompt_file}: {e}"
                )

        # Load user-defined system prompts
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

    def _prepare_messages_with_context(
        self, context_exchanges: List[Exchange]
    ) -> List[Dict[str, Any]]:
        """
        Prepare messages for LLM API including context from vector store.

        Parameters
        ----------
        context_exchanges : List[Exchange]
            Similar exchanges from vector store to use as context

        Returns
        -------
        List[Dict[str, Any]]
            Messages formatted for LLM API with context included
        """
        # Start with conversation history
        api_messages = self.get_conversation_history()

        # If we have context exchanges, inject them before the current conversation
        # Check the context display mode via the showcontext command
        context_mode = getattr(self, "context_mode", "off")  # Default to off
        if (
            context_exchanges
            and self.config.vector_store.enabled
            and context_mode == "on"
        ):
            # Create a context message with relevant exchanges
            context_content = (
                "Here are some relevant previous conversations for context:\n\n"
            )

            for i, exchange in enumerate(
                context_exchanges[: self.config.vector_store.context_results]
            ):
                context_content += f"Context {i+1}:\n"
                context_content += f"User: {exchange.user_prompt}\n"
                context_content += f"Assistant: {exchange.assistant_response}\n\n"

            context_content += (
                "Please use this context to inform your response when relevant.\n"
            )

            # Insert context after system messages but before conversation
            system_messages = [msg for msg in api_messages if msg["role"] == "system"]
            conversation_messages = [
                msg for msg in api_messages if msg["role"] != "system"
            ]

            # Build final message list
            final_messages = system_messages

            # Add context message if we have context
            if context_exchanges:
                final_messages.append({"role": "system", "content": context_content})
                self.logger.debug(
                    f"Added context from {len(context_exchanges)} exchanges"
                )

                # Visual indicator that context is being used with excerpts
                self.console.print(
                    f"🧠 Using context from {len(context_exchanges)} previous exchange(s):",
                    style="dim cyan",
                )

                # Show excerpts from each context exchange
                for i, exchange in enumerate(
                    context_exchanges[: self.config.vector_store.context_results], 1
                ):
                    # Truncate long exchanges for display
                    user_excerpt = (
                        exchange.user_prompt[:60] + "..."
                        if len(exchange.user_prompt) > 60
                        else exchange.user_prompt
                    )
                    assistant_excerpt = (
                        exchange.assistant_response[:80] + "..."
                        if len(exchange.assistant_response) > 80
                        else exchange.assistant_response
                    )

                    self.console.print(
                        f"   {i}. User: {user_excerpt}", style="dim blue"
                    )
                    self.console.print(
                        f"      Assistant: {assistant_excerpt}", style="dim green"
                    )

            final_messages.extend(conversation_messages)

            return final_messages
        elif (
            context_exchanges
            and self.config.vector_store.enabled
            and context_mode == "summary"
        ):
            self.logger.debug("Context exchanges available, showing summary mode")
            # Count total words in context
            total_words = sum(
                len(exchange.user_prompt.split())
                + len(exchange.assistant_response.split())
                for exchange in context_exchanges
            )

            # Visual indicator for summary mode
            self.console.print(
                f"💭 {len(context_exchanges)} context items included, totalling {total_words} words",
                style="dim cyan",
            )

            # Create context message for the LLM (same as 'on' mode)
            context_content = (
                "Here are some relevant previous conversations for context:\n\n"
            )

            for i, exchange in enumerate(
                context_exchanges[: self.config.vector_store.context_results]
            ):
                context_content += f"Context {i+1}:\n"
                context_content += f"User: {exchange.user_prompt}\n"
                context_content += f"Assistant: {exchange.assistant_response}\n\n"

            context_content += (
                "Please use this context to inform your response when relevant.\n"
            )

            # Insert context after system messages but before conversation
            system_messages = [msg for msg in api_messages if msg["role"] == "system"]
            conversation_messages = [
                msg for msg in api_messages if msg["role"] != "system"
            ]

            # Build final message list
            final_messages = system_messages

            # Add context message if we have context
            if context_exchanges:
                final_messages.append({"role": "system", "content": context_content})
                self.logger.debug(
                    f"Added context from {len(context_exchanges)} exchanges"
                )

            final_messages.extend(conversation_messages)

            return final_messages

        return api_messages

    def show_welcome(self) -> None:
        """
        Display the welcome message with current configuration.
        """
        profile_name = getattr(self.config, "profile_name", "Default")
        model_name = self.config.llm.model

        welcome_panel = Panel(
            f"Welcome to Ocat - Otherworldly Chats at (the) Terminal\n\n"
            f"Type your messages to chat with the LLM.\n"
            f"Type /help to see available commands.\n"
            f"Type /exit to quit the application.\n\n"
            f"Model: {model_name}\n"
            f"Profile: {profile_name}",
            title="🐱 Ocat",
            border_style="cyan",
            padding=(1, 2),
        )

        self.console.print(welcome_panel)
        self.console.print()
