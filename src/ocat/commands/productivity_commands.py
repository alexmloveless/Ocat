"""
Productivity slash commands for Ocat.

Implements task management commands like /st for showing tasks.
"""

from typing import List, Any, Optional
from datetime import datetime

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
    description="Show open tasks with sorting and filtering options",
    usage="/st [-s|--sort=<field>] [-o|--order=<asc|desc>] [-p|--priority=<priority>] [-c|--category=<category>] [-S|--status=<status>]",
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
            Command arguments with options (--sort, --order, --priority, etc.)
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

            # Parse options from arguments
            sort_field = "created"  # default sort field
            sort_order = "desc"  # default order for created
            category_filter: Optional[str] = None
            priority_filter: Optional[str] = None
            status_filter: Optional[str] = None

            # Parse command line options
            remaining_args = []
            i = 0
            while i < len(args):
                arg = args[i]

                # Handle long options
                if arg.startswith("--sort="):
                    sort_field = arg.split("=", 1)[1].lower()
                    if sort_field not in [
                        "created",
                        "priority",
                        "category",
                        "due",
                        "id",
                        "status",
                    ]:
                        return CommandResult.error(
                            f"Invalid sort field: {sort_field}. Valid options: created, priority, category, due, id, status"
                        )
                    # Adjust default order based on sort field
                    if sort_field == "created":
                        sort_order = "desc"  # newest first
                    else:
                        sort_order = "asc"  # alphabetical/chronological for others
                elif arg.startswith("--order="):
                    sort_order = arg.split("=", 1)[1].lower()
                    if sort_order not in ["asc", "desc"]:
                        return CommandResult.error("Invalid order. Use 'asc' or 'desc'")
                elif arg.startswith("--priority="):
                    priority_filter = arg.split("=", 1)[1].lower()
                elif arg.startswith("--category="):
                    category_filter = arg.split("=", 1)[1]
                elif arg.startswith("--status="):
                    status_filter = arg.split("=", 1)[1].lower()

                # Handle short options
                elif arg == "-s" and i + 1 < len(args):
                    i += 1
                    sort_field = args[i].lower()
                    if sort_field not in [
                        "created",
                        "priority",
                        "category",
                        "due",
                        "id",
                        "status",
                    ]:
                        return CommandResult.error(
                            f"Invalid sort field: {sort_field}. Valid options: created, priority, category, due, id, status"
                        )
                    # Adjust default order based on sort field
                    if sort_field == "created":
                        sort_order = "desc"  # newest first
                    else:
                        sort_order = "asc"  # alphabetical/chronological for others
                elif arg == "-o" and i + 1 < len(args):
                    i += 1
                    sort_order = args[i].lower()
                    if sort_order not in ["asc", "desc"]:
                        return CommandResult.error("Invalid order. Use 'asc' or 'desc'")
                elif arg == "-p" and i + 1 < len(args):
                    i += 1
                    priority_filter = args[i].lower()
                elif arg == "-c" and i + 1 < len(args):
                    i += 1
                    category_filter = args[i]
                elif arg == "-S" and i + 1 < len(args):
                    i += 1
                    status_filter = args[i].lower()
                elif arg.startswith("-"):
                    return CommandResult.error(
                        f"Unknown option: {arg}. Use /help st for usage info"
                    )
                else:
                    # For backward compatibility, treat non-option args as category filter
                    remaining_args.append(arg)
                i += 1

            # Handle legacy syntax (non-option arguments)
            if remaining_args:
                arg_str = " ".join(remaining_args)
                if arg_str.startswith("priority:"):
                    priority_filter = arg_str.split(":", 1)[1].lower()
                else:
                    category_filter = arg_str

            # Get tasks based on status filter
            if status_filter:
                if status_filter == "active":
                    tasks = storage.get_entities_by_type(
                        EntityType.TASK, status=EntityStatus.ACTIVE, limit=100
                    )
                elif status_filter == "in_progress":
                    tasks = storage.get_entities_by_type(
                        EntityType.TASK, status=EntityStatus.IN_PROGRESS, limit=100
                    )
                elif status_filter == "completed":
                    tasks = storage.get_entities_by_type(
                        EntityType.TASK, status=EntityStatus.COMPLETED, limit=100
                    )
                else:
                    return CommandResult.error(
                        f"Invalid status filter: {status_filter}. Valid options: active, in_progress, completed"
                    )
            else:
                # Default: show open tasks (active and in-progress)
                active_tasks = storage.get_entities_by_type(
                    EntityType.TASK, status=EntityStatus.ACTIVE, limit=100
                )
                in_progress_tasks = storage.get_entities_by_type(
                    EntityType.TASK, status=EntityStatus.IN_PROGRESS, limit=100
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

            # Sort tasks
            def get_sort_key(task):
                if sort_field == "created":
                    return task.created_at
                elif sort_field == "priority":
                    # Priority order: urgent > high > medium > low > none
                    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
                    return priority_order.get(
                        task.priority.lower() if task.priority else "", 4
                    )
                elif sort_field == "category":
                    return task.category.lower() if task.category else ""
                elif sort_field == "due":
                    return (
                        task.due_date
                        if hasattr(task, "due_date") and task.due_date
                        else datetime.max
                    )
                elif sort_field == "id":
                    return task.pseudo_id
                elif sort_field == "status":
                    return task.status.value if task.status else ""
                else:
                    return task.created_at

            tasks.sort(key=get_sort_key, reverse=(sort_order == "desc"))

            if not tasks:
                if category_filter:
                    message = f"No open tasks found in category '{category_filter}'"
                elif priority_filter:
                    message = f"No open tasks found with priority '{priority_filter}'"
                else:
                    message = "No open tasks found"
                context.console.print(message, style="yellow")
                return CommandResult.ok(message)

            # Create Rich table with dynamic title
            title_parts = []
            if status_filter:
                title_parts.append(f"{status_filter.title()} Tasks")
            else:
                title_parts.append("Open Tasks")

            if category_filter:
                title_parts.append(f"in {category_filter}")
            if priority_filter:
                title_parts.append(f"{priority_filter.title()} Priority")

            # Add sort info to title
            sort_info = f"sorted by {sort_field}"
            if sort_order == "desc":
                sort_info += " ↓"
            else:
                sort_info += " ↑"
            title_parts.append(sort_info)

            title = f"{' '.join(title_parts)} ({len(tasks)})"

            table = Table(title=title)
            table.add_column("S", style="white", no_wrap=True, width=3)
            table.add_column("Priority", style="white", no_wrap=True)
            table.add_column("Category", style="white", no_wrap=True)
            table.add_column("ID", style="cyan", no_wrap=True)
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
                    status_emoji, priority_text, category, task_id, task_desc, due_date
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
