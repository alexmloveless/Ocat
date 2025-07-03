"""
Context management commands for Ocat.

Implements commands for controlling context display and management.
"""

from typing import List, Any

from . import command, BaseCommand, CommandResult


@command(
    name="showcontext",
    description="Toggle output of context in responses",
    usage="/showcontext [on|off]",
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
            # Initialize show_context attribute if it doesn't exist
            if not hasattr(context, "show_context"):
                context.show_context = True  # Default to enabled

            if not args:
                # Show current state
                current_state = "on" if context.show_context else "off"
                context.console.print(f"Context display is currently: {current_state}")
                return CommandResult.ok(f"Context display is {current_state}")

            # Parse the toggle argument
            toggle_arg = args[0].lower()

            if toggle_arg == "on":
                context.show_context = True
                context.console.print("✅ Context display enabled", style="green")
                return CommandResult.ok("Context display enabled")
            elif toggle_arg == "off":
                context.show_context = False
                context.console.print("✅ Context display disabled", style="green")
                return CommandResult.ok("Context display disabled")
            else:
                return CommandResult.error(
                    "Invalid argument. Use 'on' or 'off', or no argument to check current state."
                )

        except Exception as e:
            return CommandResult.error(f"Failed to toggle context display: {e}")
