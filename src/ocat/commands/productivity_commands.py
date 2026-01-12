"""
Productivity slash commands for Ocat.

Implements task management commands like /st for showing tasks.
"""

from typing import List, Any, Optional

from . import command, BaseCommand, CommandResult
from ..productivity.storage import ProductivityStorage
from ..productivity.models import (
    EntityStatus,
    EntityType,
    Task,
    Event,
    Reminder,
    ListItem,
)
from ..productivity.formatters import _format_datetime_short
from rich.table import Table


@command(
    name="st",
    description="Show open tasks (active & in-progress) - /st for all open tasks, /st <category> for tasks in category, /st priority:<priority> for tasks by priority",
    usage="/st [category|priority:<high|medium|low|urgent>]",
    aliases=["show-tasks", "tasks"],
)
class ShowTasksCommand(BaseCommand):
    """Command to show tasks, optionally filtered by category."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the show tasks command.

        Parameters
        ----------
        args : List[str]
            Command arguments - optional category filter
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Get productivity storage from context
            if (
                not hasattr(context, "productivity_integration")
                or context.productivity_integration is None
            ):
                return CommandResult.error("Productivity system not available")

            storage: ProductivityStorage = context.productivity_integration.storage

            # Parse filters from arguments
            category_filter: Optional[str] = None
            priority_filter: Optional[str] = None

            if args:
                arg_str = " ".join(args)
                if arg_str.startswith("priority:"):
                    priority_filter = arg_str.split(":", 1)[1].lower()
                else:
                    category_filter = arg_str

            # Get open tasks (both active and in-progress)
            active_tasks = storage.get_entities_by_type(
                EntityType.TASK, status=EntityStatus.ACTIVE, limit=50
            )
            in_progress_tasks = storage.get_entities_by_type(
                EntityType.TASK, status=EntityStatus.IN_PROGRESS, limit=50
            )
            tasks = active_tasks + in_progress_tasks

            # Filter by category if specified
            if category_filter:
                filtered_tasks = [
                    task
                    for task in tasks
                    if task.category
                    and task.category.lower() == category_filter.lower()
                ]
                tasks = filtered_tasks

            # Filter by priority if specified
            if priority_filter:
                filtered_tasks = [
                    task
                    for task in tasks
                    if task.priority and task.priority.lower() == priority_filter
                ]
                tasks = filtered_tasks

            if not tasks:
                if category_filter:
                    message = f"No open tasks found in category '{category_filter}'"
                elif priority_filter:
                    message = f"No open tasks found with priority '{priority_filter}'"
                else:
                    message = "No open tasks found"
                context.console.print(message, style="yellow")
                return CommandResult.ok(message)

            # Create Rich table
            title = f"Open Tasks ({len(tasks)})"
            if category_filter:
                title = f"Open Tasks - {category_filter} ({len(tasks)})"
            elif priority_filter:
                title = (
                    f"Open Tasks - {priority_filter.title()} Priority ({len(tasks)})"
                )

            table = Table(title=title)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("S", style="white", no_wrap=True, width=3)
            table.add_column("Priority", style="white", no_wrap=True)
            table.add_column("Category", style="white", no_wrap=True)
            table.add_column("Task", style="white")
            table.add_column("Due", style="dim yellow", no_wrap=True)

            # Add rows
            for task in tasks:
                # Task ID - make it brighter for high priority tasks
                task_id = task.pseudo_id
                if hasattr(task, "priority") and task.priority:
                    if task.priority.lower() == "urgent":
                        task_id = f"[bold bright_red]{task.pseudo_id}[/bold bright_red]"
                    elif task.priority.lower() == "high":
                        task_id = (
                            f"[bold bright_yellow]{task.pseudo_id}[/bold bright_yellow]"
                        )

                # Status emoji
                status_emoji = {
                    "active": "🔵",
                    "completed": "✅",
                    "in_progress": "🟡",
                    "deleted": "🗑️",
                }.get(task.status.value, "🔵")

                # Priority column with visual emphasis for high priority
                priority_text = ""
                if hasattr(task, "priority") and task.priority:
                    priority_map = {
                        "urgent": "[bold red]🔥 URGENT[/bold red]",
                        "high": "[bold yellow]⚡ HIGH[/bold yellow]",
                        "medium": "[dim white]● MED[/dim white]",
                        "low": "[dim]○ LOW[/dim]",
                    }
                    priority_text = priority_map.get(
                        task.priority.lower(), task.priority.upper()
                    )

                # Task description - make high priority tasks bright and visible
                task_desc = task.content
                if hasattr(task, "priority") and task.priority:
                    if task.priority.lower() == "urgent":
                        task_desc = f"[bold bright_red]{task.content}[/bold bright_red]"
                    elif task.priority.lower() == "high":
                        task_desc = (
                            f"[bold bright_yellow]{task.content}[/bold bright_yellow]"
                        )

                # Category column with color coding
                category = ""
                if hasattr(task, "category") and task.category:
                    # Color map for categories (using simple hash-based assignment)
                    category_colors = [
                        "bright_cyan",
                        "bright_magenta",
                        "bright_green",
                        "bright_blue",
                        "magenta",
                        "green",
                        "blue",
                        "cyan",
                    ]
                    # Use hash of category name to consistently assign color
                    color_index = hash(task.category.lower()) % len(category_colors)
                    color = category_colors[color_index]
                    category = f"[{color}]{task.category}[/{color}]"

                # Due date column
                due_date = ""
                if isinstance(task, Task) and task.due_date:
                    due_date = _format_datetime_short(task.due_date)
                elif isinstance(task, Event):
                    due_date = _format_datetime_short(task.start_datetime)
                elif isinstance(task, Reminder):
                    due_date = _format_datetime_short(task.trigger_datetime)

                table.add_row(
                    task_id, status_emoji, priority_text, category, task_desc, due_date
                )

            # Display table
            context.console.print(table)

            return CommandResult.ok(f"Displayed {len(tasks)} tasks")

        except Exception as e:
            return CommandResult.error(f"Failed to show tasks: {e}")


@command(
    name="list",
    description="Show lists - /list for all lists with counts, /list <listname> for items in specific list",
    usage="/list [listname]",
    aliases=["lists", "show-lists"],
)
class ShowListsCommand(BaseCommand):
    """Command to show lists and list items."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the show lists command.

        Parameters
        ----------
        args : List[str]
            Command arguments - optional list name
        context : Any
            Command execution context (ChatSession)

        Returns
        -------
        CommandResult
            Result of command execution
        """
        try:
            # Get productivity storage from context
            if (
                not hasattr(context, "productivity_integration")
                or context.productivity_integration is None
            ):
                return CommandResult.error("Productivity system not available")

            storage: ProductivityStorage = context.productivity_integration.storage

            # Parse list name from arguments
            list_name: Optional[str] = None
            if args:
                list_name = " ".join(args)

            if list_name:
                # Show items in specific list
                items = storage.get_entities_by_type(
                    EntityType.LIST_ITEM, status=None, limit=100
                )

                # Filter by list name
                filtered_items = [
                    item
                    for item in items
                    if item.list_name.lower() == list_name.lower()
                ]

                if not filtered_items:
                    message = f"No items found in list '{list_name}'"
                    context.console.print(message, style="yellow")
                    return CommandResult.ok(message)

                # Create Rich table for list items
                title = f"List: {list_name} ({len(filtered_items)} items)"
                table = Table(title=title)
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("S", style="white", no_wrap=True, width=3)
                table.add_column("Category", style="white", no_wrap=True)
                table.add_column("Item", style="white")
                table.add_column("Added", style="dim yellow", no_wrap=True)

                # Add rows
                for item in filtered_items:
                    # Status emoji
                    status_map = {
                        "active": "🔵",
                        "archived": "📦",
                        "completed": "✅",
                        "in_progress": "🟡",
                        "deleted": "🗑️",
                    }
                    if item.status:
                        status_emoji = status_map.get(item.status.value, "⚪")
                    else:
                        # Default emoji for items with no status
                        status_emoji = "⚪"

                    # Category with color coding
                    category = ""
                    if hasattr(item, "category") and item.category:
                        category_colors = [
                            "bright_cyan",
                            "bright_magenta",
                            "bright_green",
                            "bright_blue",
                            "magenta",
                            "green",
                            "blue",
                            "cyan",
                        ]
                        color_index = hash(item.category.lower()) % len(category_colors)
                        color = category_colors[color_index]
                        category = f"[{color}]{item.category}[/{color}]"

                    # Format date added
                    date_added = item.created_at.strftime("%m/%d")

                    table.add_row(
                        item.pseudo_id, status_emoji, category, item.content, date_added
                    )

                # Display table
                context.console.print(table)

                return CommandResult.ok(
                    f"Displayed {len(filtered_items)} items from '{list_name}'"
                )

            else:
                # Show all lists with counts
                items = storage.get_entities_by_type(
                    EntityType.LIST_ITEM, status=None, limit=1000
                )

                if not items:
                    message = "No lists found"
                    context.console.print(message, style="yellow")
                    return CommandResult.ok(message)

                # Group by list name
                list_counts = {}
                for item in items:
                    list_name = item.list_name
                    if list_name not in list_counts:
                        list_counts[list_name] = 0
                    list_counts[list_name] += 1

                # Create Rich table for list summary
                table = Table(title=f"Available Lists ({len(list_counts)} lists)")
                table.add_column("List Name", style="bright_cyan")
                table.add_column("Items", style="white", justify="right")

                # Add rows
                for list_name, count in sorted(list_counts.items()):
                    table.add_row(list_name, str(count))

                # Display table
                context.console.print(table)

                return CommandResult.ok(f"Displayed {len(list_counts)} lists")

        except Exception as e:
            return CommandResult.error(f"Failed to show lists: {e}")
