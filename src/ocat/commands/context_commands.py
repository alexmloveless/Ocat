"""
Context management commands for Ocat.

Implements commands for controlling context display and management.
"""

from typing import List, Any

from . import command, BaseCommand, CommandResult


@command(
    name="showcontext",
    description="Control context display in responses",
    usage="/showcontext [on|off|summary]",
)
class ShowContextCommand(BaseCommand):
    """Command to toggle context display in chat responses."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the showcontext command.

        Parameters
        ----------
        args : List[str]
            Command arguments - optional on/off toggle
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Initialize context_mode attribute if it doesn't exist
            if not hasattr(context, "context_mode"):
                context.context_mode = "off"  # Default to off (no context reporting)

            if not args:
                # Show current state
                context.console.print(
                    f"Context display is currently: {context.context_mode}"
                )
                return CommandResult.ok(f"Context display is {context.context_mode}")

            # Parse the mode argument
            mode_arg = args[0].lower()

            if mode_arg == "on":
                context.context_mode = "on"
                context.console.print("✅ Context display enabled", style="green")
                return CommandResult.ok("Context display enabled")
            elif mode_arg == "off":
                context.context_mode = "off"
                context.console.print("✅ Context display disabled", style="green")
                return CommandResult.ok("Context display disabled")
            elif mode_arg == "summary":
                context.context_mode = "summary"
                context.console.print("✅ Context summary mode enabled", style="green")
                return CommandResult.ok("Context summary mode enabled")
            else:
                return CommandResult.error(
                    "Invalid argument. Use 'on', 'off', or 'summary', or no argument to check current state."
                )

        except Exception as e:
            return CommandResult.error(f"Failed to toggle context display: {e}")
