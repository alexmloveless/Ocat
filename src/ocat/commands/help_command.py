"""
Enhanced help command for Ocat.

Displays organized, markdown-formatted help with section refinement capabilities.
"""

from typing import List, Any
from rich.markdown import Markdown

from . import command, BaseCommand, CommandResult
from .help_system import get_help_content


@command(
    name="help", 
    description="Show help information. Use /help <section> for specific topics.", 
    usage="/help [section]", 
    aliases=["h"]
)
class HelpCommand(BaseCommand):
    """
    Enhanced command to show organized help information.
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
        # Determine which section to show
        section = args[0] if args else None
        
        # Get help content
        help_content = get_help_content(section)
        
        # Display as formatted markdown
        markdown = Markdown(help_content)
        context.console.print(markdown)

        # Return appropriate message
        if section:
            return CommandResult.ok(message=f"Help for '{section}' displayed successfully.")
        else:
            return CommandResult.ok(message="Help overview displayed successfully.")
