"""
Help command for Ocat.

Displays help information about available slash commands.
"""

from typing import List, Any

from . import command, BaseCommand, CommandResult, get_registry


@command(
    name="help", description="Show this help message", usage="/help", aliases=["h"]
)
class HelpCommand(BaseCommand):
    """
    Command to show help information.
    """

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the help command.

        Parameters
        ----------
        args : List[str]
            Command arguments (excluding the command name)
        context : Any
            Command execution context (usually a ChatSession instance)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        # Access the global command registry
        registry = get_registry()
        commands = registry.list_commands()

        help_text = "Available Commands:\n"
        for name, cmd in commands.items():
            aliases = ", ".join(registry.get_aliases(name))
            help_text += f"/{name} ({aliases}) - {cmd.description}\n"

        # Display help
        context.console.print(help_text)

        return CommandResult.success(message="Help displayed successfully.")
