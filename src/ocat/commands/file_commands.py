"""
File operation commands for Ocat.

Implements commands for file attachment and exporting conversation data.
"""

from typing import List, Any
import json
import re
from pathlib import Path

from . import command, BaseCommand, CommandResult
from rich.panel import Panel
from ..utils import resolve_path_with_aliases


@command(
    name="attach",
    description="Attach up to 5 text files as context",
    usage="/attach <file1> [file2] [file3] [file4] [file5]",
)
class AttachCommand(BaseCommand):
    """Command to attach text files as context."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the attach command.

        Parameters
        ----------
        args : List[str]
            List of file paths to attach
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No files specified. Usage: /attach <file1> [file2] ..."
            )

        if len(args) > 5:
            return CommandResult.error("Maximum 5 files can be attached at once.")

        try:
            attached_files = []
            total_content = []

            for file_path in args:
                try:
                    # Resolve path with location aliases
                    path = resolve_path_with_aliases(
                        file_path, context.config.locations
                    )
                except ValueError as e:
                    return CommandResult.error(str(e))

                try:
                    if not path.exists():
                        return CommandResult.error(f"File not found: {file_path}")

                    if not path.is_file():
                        return CommandResult.error(f"Not a file: {file_path}")

                    # Read file content
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Add file content with header
                    file_header = f"\n--- File: {path.name} ---\n"
                    total_content.append(file_header + content)
                    attached_files.append(str(path))

                except UnicodeDecodeError:
                    return CommandResult.error(
                        f"Unable to read file as text: {file_path}"
                    )
                except PermissionError:
                    return CommandResult.error(
                        f"Permission denied reading file: {file_path}"
                    )
                except Exception as e:
                    return CommandResult.error(f"Error reading file {file_path}: {e}")

            # Combine all file content
            combined_content = "\n".join(total_content)

            # Add as user message to the conversation
            from ..chat import Message

            file_message = Message(
                role="user", content=f"[Attached Files]\n{combined_content}"
            )
            context.messages.append(file_message)

            # Display confirmation
            files_list = "\n".join([f"  • {f}" for f in attached_files])
            context.console.print(
                Panel(
                    f"Files attached successfully:\n{files_list}",
                    title="Files Attached",
                    border_style="green",
                )
            )

            # Ask if user wants to add to vector store - skip in dummy mode
            if (
                hasattr(context, "vector_store")
                and context.vector_store
                and context.config.vector_store.enabled
                and not getattr(context, "dummy_mode", False)
            ):
                try:
                    # Ask user if they want to add to vector store
                    context.console.print(
                        "\n[yellow]Would you like to also add these files to the vector store for future reference? (y/n)[/yellow]"
                    )

                    # Get user response (this is a simplified approach - in real implementation
                    # you might want to use a proper input system)
                    response = input().lower().strip()

                    if response in ["y", "yes"]:
                        # Add files to vector store with chunking
                        total_chunks = 0
                        thread_id = getattr(context, "thread_id", "attach_session")
                        session_id = getattr(context, "session_id", "attach_session")

                        for file_path in attached_files:
                            try:
                                exchange_ids = context.vector_store.add_file(
                                    file_path=file_path,
                                    thread_id=thread_id,
                                    session_id=session_id,
                                    metadata={
                                        "source": "attach_command",
                                        "attached_in_session": session_id,
                                        "attached_in_thread": thread_id,
                                    },
                                )
                                total_chunks += len(exchange_ids)

                            except Exception as e:
                                context.console.print(
                                    f"[red]Warning: Could not add {file_path} to vector store: {e}[/red]"
                                )

                        if total_chunks > 0:
                            context.console.print(
                                f"[green]✅ Added {len(attached_files)} file(s) to vector store as {total_chunks} chunks[/green]"
                            )

                except KeyboardInterrupt:
                    context.console.print(
                        "\n[yellow]Skipped adding to vector store[/yellow]"
                    )
                except Exception as e:
                    context.console.print(
                        f"[red]Error with vector store prompt: {e}[/red]"
                    )

            return CommandResult.ok(
                f"Attached {len(attached_files)} file(s) to conversation."
            )

        except Exception as e:
            return CommandResult.error(f"Failed to attach files: {e}")


@command(
    name="writecode",
    description="Extract code from last response",
    usage="/writecode <filepath>",
)
class WriteCodeCommand(BaseCommand):
    """Command to extract and save code from the last assistant response."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the writecode command.

        Parameters
        ----------
        args : List[str]
            Command arguments - output file path
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No output file specified. Usage: /writecode <filepath>"
            )

        try:
            # Get the last assistant message
            assistant_messages = [
                msg for msg in context.messages if msg.role == "assistant"
            ]

            if not assistant_messages:
                return CommandResult.error("No assistant responses found.")

            last_response = assistant_messages[-1].content

            # Extract code blocks using regex
            code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", last_response, re.DOTALL)

            if not code_blocks:
                return CommandResult.error("No code blocks found in the last response.")

            # Combine all code blocks
            combined_code = "\n\n".join(code_blocks)

            # Resolve path with location aliases
            try:
                output_path = resolve_path_with_aliases(
                    args[0], context.config.locations
                )
            except ValueError as e:
                return CommandResult.error(f"Location alias error: {e}")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(combined_code)

            context.console.print(
                f"✅ Code extracted and saved to: {output_path}", style="green"
            )

            return CommandResult.ok(f"Code saved to {output_path}")

        except Exception as e:
            return CommandResult.error(f"Failed to extract code: {e}")


@command(
    name="writejson",
    description="Export conversation to JSON",
    usage="/writejson <filepath>",
)
class WriteJsonCommand(BaseCommand):
    """Command to export conversation history to JSON format."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the writejson command.

        Parameters
        ----------
        args : List[str]
            Command arguments - output file path
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No output file specified. Usage: /writejson <filepath>"
            )

        try:
            # Convert messages to serializable format
            conversation_data = {
                "conversation": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": getattr(msg, "timestamp", None),
                    }
                    for msg in context.messages
                ],
                "config": {
                    "model": context.config.llm.model,
                    "temperature": context.config.llm.temperature,
                    "max_tokens": context.config.llm.max_tokens,
                },
            }

            # Resolve path with location aliases
            try:
                output_path = resolve_path_with_aliases(
                    args[0], context.config.locations
                )
            except ValueError as e:
                return CommandResult.error(f"Location alias error: {e}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            context.console.print(
                f"✅ Conversation exported to: {output_path}", style="green"
            )

            return CommandResult.ok(f"Conversation exported to {output_path}")

        except Exception as e:
            return CommandResult.error(f"Failed to export conversation: {e}")


@command(
    name="writemd",
    aliases=["w"],
    description="Export thread to Markdown (without system prompt)",
    usage="/writemd <filepath> (alias: /w)",
)
class WriteMarkdownCommand(BaseCommand):
    """Command to export conversation thread to Markdown format."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the writemd command.

        Parameters
        ----------
        args : List[str]
            Command arguments - output file path
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No output file specified. Usage: /writemd <filepath>"
            )

        try:
            # Generate markdown content (excluding system messages)
            md_content = []
            md_content.append("# Thread Export")
            md_content.append("")
            md_content.append(f"**Model:** {context.config.llm.model}")
            md_content.append(f"**Temperature:** {context.config.llm.temperature}")
            md_content.append("")
            md_content.append("---")
            md_content.append("")

            for msg in context.messages:
                if msg.role == "system":
                    # Skip system messages for thread export
                    continue
                elif msg.role == "user":
                    md_content.append(f"## {context.config.display.user_label}")
                    md_content.append("")
                    md_content.append(msg.content)
                elif msg.role == "assistant":
                    md_content.append(f"## {context.config.display.assistant_label}")
                    md_content.append("")
                    md_content.append(msg.content)

                md_content.append("")
                md_content.append("---")
                md_content.append("")

            # Resolve path with location aliases
            try:
                output_path = resolve_path_with_aliases(
                    args[0], context.config.locations
                )
            except ValueError as e:
                return CommandResult.error(f"Location alias error: {e}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))

            context.console.print(
                f"✅ Thread exported to: {output_path}", style="green"
            )

            return CommandResult.ok(f"Thread exported to {output_path}")

        except Exception as e:
            return CommandResult.error(f"Failed to export thread: {e}")


@command(
    name="writemdall",
    description="Export full conversation to Markdown (with system prompt)",
    usage="/writemdall <filepath>",
)
class WriteMarkdownAllCommand(BaseCommand):
    """Command to export full conversation history to Markdown format."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the writemdall command.

        Parameters
        ----------
        args : List[str]
            Command arguments - output file path
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No output file specified. Usage: /writemdall <filepath>"
            )

        try:
            # Generate markdown content
            md_content = []
            md_content.append("# Conversation Export")
            md_content.append("")
            md_content.append(f"**Model:** {context.config.llm.model}")
            md_content.append(f"**Temperature:** {context.config.llm.temperature}")
            md_content.append("")
            md_content.append("---")
            md_content.append("")

            for msg in context.messages:
                if msg.role == "system":
                    md_content.append("## System Prompt")
                    md_content.append("")
                    md_content.append(msg.content)
                elif msg.role == "user":
                    md_content.append(f"## {context.config.display.user_label}")
                    md_content.append("")
                    md_content.append(msg.content)
                elif msg.role == "assistant":
                    md_content.append(f"## {context.config.display.assistant_label}")
                    md_content.append("")
                    md_content.append(msg.content)

                md_content.append("")
                md_content.append("---")
                md_content.append("")

            # Resolve path with location aliases
            try:
                output_path = resolve_path_with_aliases(
                    args[0], context.config.locations
                )
            except ValueError as e:
                return CommandResult.error(f"Location alias error: {e}")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md_content))

            context.console.print(
                f"✅ Conversation exported to: {output_path}", style="green"
            )

            return CommandResult.ok(f"Conversation exported to {output_path}")

        except Exception as e:
            return CommandResult.error(f"Failed to export conversation: {e}")


@command(
    name="writeresp",
    description="Export last exchange",
    usage="/writeresp <filepath> [format=md|json]",
)
class WriteResponseCommand(BaseCommand):
    """Command to export the last exchange to a file."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the writeresp command.

        Parameters
        ----------
        args : List[str]
            Command arguments - output file path and optional format
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No output file specified. Usage: /writeresp <filepath> [format=md|json]"
            )

        try:
            # Get format (default to markdown)
            format_type = "md"
            if len(args) > 1:
                format_type = args[1].lower()
                if format_type not in ["md", "json"]:
                    return CommandResult.error("Invalid format. Use 'md' or 'json'.")

            # Get the last user and assistant messages
            user_messages = [msg for msg in context.messages if msg.role == "user"]
            assistant_messages = [
                msg for msg in context.messages if msg.role == "assistant"
            ]

            if not user_messages or not assistant_messages:
                return CommandResult.error("No complete exchange found.")

            last_user = user_messages[-1]
            last_assistant = assistant_messages[-1]

            # Resolve path with location aliases
            try:
                output_path = resolve_path_with_aliases(
                    args[0], context.config.locations
                )
            except ValueError as e:
                return CommandResult.error(f"Location alias error: {e}")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format_type == "json":
                # JSON format
                exchange_data = {
                    "exchange": {
                        "user": {"role": last_user.role, "content": last_user.content},
                        "assistant": {
                            "role": last_assistant.role,
                            "content": last_assistant.content,
                        },
                    },
                    "model": context.config.llm.model,
                }

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(exchange_data, f, indent=2, ensure_ascii=False)
            else:
                # Markdown format
                md_content = [
                    "# Last Exchange",
                    "",
                    f"**Model:** {context.config.llm.model}",
                    "",
                    "---",
                    "",
                    f"## {context.config.display.user_label}",
                    "",
                    last_user.content,
                    "",
                    f"## {context.config.display.assistant_label}",
                    "",
                    last_assistant.content,
                    "",
                ]

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(md_content))

            context.console.print(
                f"✅ Last exchange saved to: {output_path}", style="green"
            )

            return CommandResult.ok(f"Last exchange saved to {output_path}")

        except Exception as e:
            return CommandResult.error(f"Failed to save exchange: {e}")


@command(
    name="append",
    description="Append text or last exchange to a file",
    usage='/append <path> ["text"]',
)
class AppendCommand(BaseCommand):
    """Command to append text or last exchange to a file."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the append command.

        Parameters
        ----------
        args : List[str]
            Command arguments - file path and optional text to append
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        # Step 3: Parse and validate arguments

        # Require first arg - target path
        if not args:
            return CommandResult.error(
                'No file path specified. Usage: /append <path> ["text"]'
            )

        target_path = args[0]
        need_last_exchange = False
        text_to_append: str = ""

        # Treat remaining args as the string to append (join with space, strip surrounding quotes)
        if len(args) > 1:
            # Join remaining arguments with space
            joined_text = " ".join(args[1:])
            # Strip surrounding quotes if present
            if (joined_text.startswith('"') and joined_text.endswith('"')) or (
                joined_text.startswith("'") and joined_text.endswith("'")
            ):
                text_to_append = joined_text[1:-1]
            else:
                text_to_append = joined_text
        else:
            # If no second arg, flag that we need to fetch last exchange
            need_last_exchange = True

        try:
            # Resolve path with location aliases
            try:
                file_path = resolve_path_with_aliases(
                    target_path, context.config.locations
                )
            except ValueError as e:
                return CommandResult.error(str(e))

            # Determine what to append based on parsing results
            if need_last_exchange:
                # Append last exchange
                user_messages = [msg for msg in context.messages if msg.role == "user"]
                assistant_messages = [
                    msg for msg in context.messages if msg.role == "assistant"
                ]

                if not user_messages or not assistant_messages:
                    return CommandResult.error("No complete exchange found to append.")

                last_user = user_messages[-1]
                last_assistant = assistant_messages[-1]

                # Format as markdown-style exchange
                text_to_append = (
                    f"\n## {context.config.display.user_label}\n\n"
                    f"{last_user.content}\n\n"
                    f"## {context.config.display.assistant_label}\n\n"
                    f"{last_assistant.content}\n\n"
                    "---\n"
                )

            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists and doesn't end with newline
            needs_newline = False
            if file_path.exists() and file_path.stat().st_size > 0:
                with open(file_path, "rb") as f:
                    f.seek(-1, 2)  # Go to last byte
                    last_byte = f.read(1)
                    if last_byte != b"\n":
                        needs_newline = True

            # Append to file
            with open(file_path, "a", encoding="utf-8") as f:
                if needs_newline:
                    f.write("\n")
                f.write(text_to_append)
                if not text_to_append.endswith("\n"):
                    f.write("\n")

            if len(args) > 1:
                context.console.print(
                    f"✅ Text appended to: {file_path}", style="green"
                )
                return CommandResult.ok(f"Text appended to {file_path}")
            else:
                context.console.print(
                    f"✅ Last exchange appended to: {file_path}", style="green"
                )
                return CommandResult.ok(f"Last exchange appended to {file_path}")

        except PermissionError:
            return CommandResult.error(f"Permission denied writing to file: {args[0]}")
        except Exception as e:
            return CommandResult.error(f"Failed to append to file: {e}")


@command(
    name="locations",
    description="Show available location aliases",
    usage="/locations",
)
class LocationsCommand(BaseCommand):
    """Command to show configured location aliases."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the locations command.

        Parameters
        ----------
        args : List[str]
            Command arguments (unused)
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            locations = context.config.locations

            if not locations:
                context.console.print(
                    Panel(
                        "No location aliases are configured.\n\n"
                        "Add location aliases to your config file:\n\n"
                        "locations:\n"
                        '  conv: "~/conversations/"\n'
                        '  docs: "~/documents/"',
                        title="Location Aliases",
                        border_style="blue",
                    )
                )
                return CommandResult.ok("No location aliases configured.")

            # Format the location aliases for display
            alias_list = []
            for alias, path in locations.items():
                expanded_path = str(Path(path).expanduser())
                alias_list.append(f"  {alias}: {path}")
                if expanded_path != path:
                    alias_list.append(f"      → {expanded_path}")

            alias_text = "\n".join(alias_list)

            context.console.print(
                Panel(
                    f"Available location aliases:\n\n{alias_text}\n\n"
                    "Usage: alias:filename (e.g., conv:myfile.txt)",
                    title="Location Aliases",
                    border_style="blue",
                )
            )

            return CommandResult.ok(f"Found {len(locations)} location alias(es).")

        except Exception as e:
            return CommandResult.error(f"Failed to show location aliases: {e}")
