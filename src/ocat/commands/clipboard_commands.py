"""
Clipboard commands for Ocat.

Implements commands for copying content to the system clipboard.
"""

import subprocess
import sys
from typing import List, Any
import re

from . import command, BaseCommand, CommandResult


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard using cross-platform approach.

    Parameters
    ----------
    text : str
        Text to copy to clipboard

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        elif sys.platform == "win32":  # Windows
            subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
        else:  # Linux and other Unix-like systems
            # Try xclip first, fall back to xsel
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=True,
                )
            except FileNotFoundError:
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode("utf-8"),
                    check=True,
                )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def strip_markdown_formatting(text: str) -> str:
    """
    Strip markdown formatting from text to get plain text.

    Parameters
    ----------
    text : str
        Text with markdown formatting

    Returns
    -------
    str
        Plain text without markdown formatting
    """
    # Remove code blocks
    text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # Remove bold and italic
    text = re.sub(r"\*\*([^*]*)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]*)\*", r"\1", text)
    text = re.sub(r"__([^_]*)__", r"\1", text)
    text = re.sub(r"_([^_]*)_", r"\1", text)

    # Remove headers
    text = re.sub(r"^#+\s*(.*)$", r"\1", text, flags=re.MULTILINE)

    # Remove links
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)

    # Remove horizontal rules
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)

    # Clean up extra whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()

    return text


@command(
    name="copy",
    description="Copy the last assistant response to clipboard",
    usage="/copy",
    aliases=["cp"],
)
class CopyCommand(BaseCommand):
    """Command to copy the last assistant response to clipboard."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the copy command.

        Parameters
        ----------
        args : List[str]
            Command arguments
        context : Any
            Command execution context (ChatSession instance)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        # Get the last assistant message from conversation history
        assistant_messages = [
            msg for msg in context.messages if msg.role == "assistant"
        ]

        if not assistant_messages:
            return CommandResult.error("No assistant responses to copy")

        # Get the last assistant message
        last_response = assistant_messages[-1].content

        # Strip markdown formatting to get plain text
        plain_text = strip_markdown_formatting(last_response)

        # Copy to clipboard
        if copy_to_clipboard(plain_text):
            return CommandResult.ok(
                f"Copied last response to clipboard ({len(plain_text)} characters)"
            )
        else:
            return CommandResult.error(
                "Failed to copy to clipboard. Make sure you have clipboard utilities installed "
                "(xclip or xsel on Linux, pbcopy on macOS, clip on Windows)"
            )
