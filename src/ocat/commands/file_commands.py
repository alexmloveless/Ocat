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
            return CommandResult.error("No files specified. Usage: /attach <file1> [file2] ...")

        if len(args) > 5:
            return CommandResult.error("Maximum 5 files can be attached at once.")

        try:
            attached_files = []
            total_content = []

            for file_path in args:
                try:
                    path = Path(file_path).expanduser()
                    
                    if not path.exists():
                        return CommandResult.error(f"File not found: {file_path}")
                    
                    if not path.is_file():
                        return CommandResult.error(f"Not a file: {file_path}")
                    
                    # Read file content
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add file content with header
                    file_header = f"\n--- File: {path.name} ---\n"
                    total_content.append(file_header + content)
                    attached_files.append(str(path))
                    
                except UnicodeDecodeError:
                    return CommandResult.error(f"Unable to read file as text: {file_path}")
                except PermissionError:
                    return CommandResult.error(f"Permission denied reading file: {file_path}")
                except Exception as e:
                    return CommandResult.error(f"Error reading file {file_path}: {e}")

            # Combine all file content
            combined_content = "\n".join(total_content)
            
            # Add as user message to the conversation
            from ..chat import Message
            file_message = Message(
                role="user",
                content=f"[Attached Files]\n{combined_content}"
            )
            context.messages.append(file_message)

            # Display confirmation
            files_list = "\n".join([f"  • {f}" for f in attached_files])
            context.console.print(
                Panel(
                    f"Files attached successfully:\n{files_list}",
                    title="Files Attached",
                    border_style="green"
                )
            )

            return CommandResult.success(f"Attached {len(attached_files)} file(s) to conversation.")

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
            return CommandResult.error("No output file specified. Usage: /writecode <filepath>")

        try:
            # Get the last assistant message
            assistant_messages = [msg for msg in context.messages if msg.role == "assistant"]
            
            if not assistant_messages:
                return CommandResult.error("No assistant responses found.")

            last_response = assistant_messages[-1].content

            # Extract code blocks using regex
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', last_response, re.DOTALL)
            
            if not code_blocks:
                return CommandResult.error("No code blocks found in the last response.")

            # Combine all code blocks
            combined_code = "\n\n".join(code_blocks)

            # Write to file
            output_path = Path(args[0]).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(combined_code)

            context.console.print(
                f"✅ Code extracted and saved to: {output_path}",
                style="green"
            )

            return CommandResult.success(f"Code saved to {output_path}")

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
            return CommandResult.error("No output file specified. Usage: /writejson <filepath>")

        try:
            # Convert messages to serializable format
            conversation_data = {
                "conversation": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": getattr(msg, 'timestamp', None)
                    }
                    for msg in context.messages
                ],
                "config": {
                    "model": context.config.llm.model,
                    "temperature": context.config.llm.temperature,
                    "max_tokens": context.config.llm.max_tokens
                }
            }

            # Write to file
            output_path = Path(args[0]).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            context.console.print(
                f"✅ Conversation exported to: {output_path}",
                style="green"
            )

            return CommandResult.success(f"Conversation exported to {output_path}")

        except Exception as e:
            return CommandResult.error(f"Failed to export conversation: {e}")


@command(
    name="writemd",
    description="Export conversation to Markdown",
    usage="/writemd <filepath>",
)
class WriteMarkdownCommand(BaseCommand):
    """Command to export conversation history to Markdown format."""

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
            return CommandResult.error("No output file specified. Usage: /writemd <filepath>")

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

            # Write to file
            output_path = Path(args[0]).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(md_content))

            context.console.print(
                f"✅ Conversation exported to: {output_path}",
                style="green"
            )

            return CommandResult.success(f"Conversation exported to {output_path}")

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
            return CommandResult.error("No output file specified. Usage: /writeresp <filepath> [format=md|json]")

        try:
            # Get format (default to markdown)
            format_type = "md"
            if len(args) > 1:
                format_type = args[1].lower()
                if format_type not in ["md", "json"]:
                    return CommandResult.error("Invalid format. Use 'md' or 'json'.")

            # Get the last user and assistant messages
            user_messages = [msg for msg in context.messages if msg.role == "user"]
            assistant_messages = [msg for msg in context.messages if msg.role == "assistant"]
            
            if not user_messages or not assistant_messages:
                return CommandResult.error("No complete exchange found.")

            last_user = user_messages[-1]
            last_assistant = assistant_messages[-1]

            output_path = Path(args[0]).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format_type == "json":
                # JSON format
                exchange_data = {
                    "exchange": {
                        "user": {
                            "role": last_user.role,
                            "content": last_user.content
                        },
                        "assistant": {
                            "role": last_assistant.role,
                            "content": last_assistant.content
                        }
                    },
                    "model": context.config.llm.model
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
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
                    ""
                ]
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(md_content))

            context.console.print(
                f"✅ Last exchange saved to: {output_path}",
                style="green"
            )

            return CommandResult.success(f"Last exchange saved to {output_path}")

        except Exception as e:
            return CommandResult.error(f"Failed to save exchange: {e}")
