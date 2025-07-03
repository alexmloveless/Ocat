"""
Remember command for Ocat.

Implements the /remember command for storing user information in the vector store
with appropriate tagging and metadata for future retrieval.
"""

from typing import List, Any

from . import command, BaseCommand, CommandResult


@command(
    name="remember",
    description="Store information for later retrieval",
    usage="/remember <type> <text>",
    aliases=["rem", "r"],
)
class RememberCommand(BaseCommand):
    """
    Command to store information in the vector store for later retrieval.
    """

    # Valid remember types and their descriptions
    VALID_TYPES = {
        "fact": "General information that may be useful later",
        "preference": "User preferences that can help tailor responses",
        "critical": "Important information that should be prioritized in responses",
        "nudge": "Gentle reminders or suggestions for the user",
        "like": "Positive reinforcement for things the user enjoys",
        "opinion": "User's personal views or beliefs on various topics",
        "dislike": "Negative reinforcement for things the user dislikes",
    }

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the remember command.

        Parameters
        ----------
        args : List[str]
            Command arguments - type and text to remember
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        if len(args) < 2:
            return CommandResult.error(
                f"Usage: /remember <type> <text>\n"
                f"Valid types: {', '.join(self.VALID_TYPES.keys())}"
            )

        try:
            # Check if vector store is enabled
            if not context.config.vector_store.enabled:
                return CommandResult.error(
                    "Vector store is not enabled in configuration. "
                    "The remember command requires vector store functionality."
                )

            if not hasattr(context, "vector_store") or context.vector_store is None:
                return CommandResult.error("Vector store is not initialized.")

            # Parse arguments
            remember_type = args[0].lower()
            remember_text = " ".join(args[1:])

            # Validate type
            if remember_type not in self.VALID_TYPES:
                return CommandResult.error(
                    f"Invalid remember type '{remember_type}'. "
                    f"Valid types: {', '.join(self.VALID_TYPES.keys())}"
                )

            # Create tagged text for storage
            tagged_text = f"<{remember_type}>{remember_text}</{remember_type}>"

            # Add to vector store with only the tagged statement
            exchange_id = context.vector_store.add_exchange(
                user_prompt=tagged_text,
                assistant_response="",
                thread_id=getattr(context, "thread_id", "remember"),
                session_id=getattr(context, "session_id", "remember"),
                prior_exchange_ids=[],
            )

            context.console.print(
                f"✅ Remembered {remember_type}: {remember_text}", style="green"
            )
            context.console.print(f"   Stored with ID: {exchange_id}", style="dim")

            return CommandResult.ok(
                f"Stored {remember_type} information with ID: {exchange_id}"
            )

        except Exception as e:
            return CommandResult.error(f"Failed to store information: {e}")

    def get_help_text(self) -> str:
        """
        Get detailed help text for the remember command.

        Returns
        -------
        str
            Detailed help text including types and examples
        """
        help_text = [
            "Store information for later retrieval by the LLM.",
            "",
            "Usage: /remember <type> <text>",
            "Aliases: /rem, /r",
            "",
            "Valid types:",
        ]

        for type_name, description in self.VALID_TYPES.items():
            help_text.append(f"  {type_name:<10} - {description}")

        help_text.extend(
            [
                "",
                "Examples:",
                '  /remember fact "I have a brother called Bob"',
                '  /remember preference "I don\'t like eating fish much"',
                '  /remember critical "If I mention this again, it is very important to me"',
                "",
                "The text after the type does not need to be enclosed in quotes.",
                "Stored information will be tagged and retrievable in future conversations.",
            ]
        )

        return "\n".join(help_text)
