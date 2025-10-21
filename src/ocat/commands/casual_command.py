"""
Casual mode command for Ocat.

Implements the /casual command to toggle casual chat mode, which modifies
the system prompt to enable more informal, conversational interactions.
"""

from typing import List, Any
import os
from pathlib import Path

from . import command, BaseCommand, CommandResult, CommandError
from ..messages import Message


@command(
    name="casual",
    description="Toggle casual chat mode for informal conversations",
    usage="/casual [on|off]",
    aliases=["chitchat"],
)
class CasualCommand(BaseCommand):
    """Command to toggle casual chat mode."""

    def __init__(self, *args, **kwargs):
        """Initialize the casual command."""
        super().__init__(*args, **kwargs)
        self._casual_prompt_content = None

    def _load_casual_prompt(self) -> str:
        """Load the casual mode prompt from file."""
        if self._casual_prompt_content is None:
            try:
                # Get the path to the casual mode prompt file
                current_dir = Path(__file__).parent.parent
                prompt_file = current_dir / "prompts" / "casual_mode_prompt.md"

                with open(prompt_file, "r", encoding="utf-8") as f:
                    self._casual_prompt_content = f.read()
            except FileNotFoundError:
                raise CommandError(
                    "Casual mode prompt file not found. Please check installation."
                )
            except Exception as e:
                raise CommandError(f"Failed to load casual mode prompt: {e}")

        return self._casual_prompt_content

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the casual command.

        Parameters
        ----------
        args : List[str]
            Command arguments - can be empty, 'on', or 'off'
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Check if casual mode is currently enabled
            current_casual_mode = getattr(context, "_casual_mode", False)

            # Determine new state
            if not args:
                # Toggle mode
                new_state = not current_casual_mode
            elif args[0].lower() in ["on", "enable", "true", "1"]:
                new_state = True
            elif args[0].lower() in ["off", "disable", "false", "0"]:
                new_state = False
            else:
                return CommandResult.error(
                    f"Invalid argument: '{args[0]}'. Use 'on', 'off', or no argument to toggle."
                )

            # Set the casual mode state
            context._casual_mode = new_state

            if new_state:
                # Enable casual mode - add the casual prompt to system messages
                if not self._has_casual_prompt(context):
                    casual_prompt = self._load_casual_prompt()
                    casual_message = Message(role="system", content=casual_prompt)
                    context.messages.append(casual_message)

                return CommandResult.ok(
                    "🎉 Casual mode enabled! Ready for some laid-back chatting."
                )
            else:
                # Disable casual mode - remove casual prompt from system messages
                self._remove_casual_prompt(context)

                return CommandResult.ok(
                    "🤖 Casual mode disabled. Back to regular assistant mode."
                )

        except Exception as e:
            return CommandResult.error(f"Failed to toggle casual mode: {e}")

    def _has_casual_prompt(self, context: Any) -> bool:
        """Check if casual mode prompt is already in system messages."""
        for message in context.messages:
            if message.role == "system" and "CASUAL MODE ENABLED" in message.content:
                return True
        return False

    def _remove_casual_prompt(self, context: Any) -> None:
        """Remove casual mode prompt from system messages."""
        context.messages = [
            msg
            for msg in context.messages
            if not (msg.role == "system" and "CASUAL MODE ENABLED" in msg.content)
        ]
