"""
Continue command for Ocat.

Implements the /continue command to resume an existing thread.
"""

from typing import List, Any

from . import command, BaseCommand, CommandResult


@command(
    name="continue",
    aliases=["cont"],
    description="Continue an existing thread by loading its history",
    usage="/continue <thread_id> | /cont <thread_id>",
)
class ContinueCommand(BaseCommand):
    """Command to continue an existing conversation thread."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the continue command.

        Parameters
        ----------
        args : List[str]
            Command arguments - thread ID to continue
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if not args:
            return CommandResult.error(
                "No thread ID specified. Usage: /continue <thread_id>"
            )

        try:
            # Check if vector store is enabled
            if not context.config.vector_store.enabled:
                return CommandResult.error(
                    "Vector store is not enabled in configuration."
                )

            if not hasattr(context, "vector_store") or context.vector_store is None:
                return CommandResult.error("Vector store is not initialized.")

            thread_id = args[0]

            # Continue the thread using ChatSession method
            context.continue_thread(thread_id)

            return CommandResult.ok(f"Continued thread: {thread_id}")

        except ValueError as e:
            return CommandResult.error(str(e))
        except Exception as e:
            return CommandResult.error(f"Failed to continue thread: {e}")
