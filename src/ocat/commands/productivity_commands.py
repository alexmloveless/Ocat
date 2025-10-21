"""
Productivity slash commands for Ocat.

Implements task management commands like /st for showing tasks.
"""

from typing import List, Any, Optional
from datetime import datetime, date, timedelta
import pandas as pd
from pathlib import Path
import json
import yaml

from . import command, BaseCommand, CommandResult
from ..productivity.storage import ProductivityStorage
from ..productivity.models import (
    EntityStatus,
    EntityType,
    Task,
    Event,
    Reminder,
    ListItem,
    TimelogEntry,
)
from ..productivity.formatters import _format_datetime_short
from rich.table import Table
import shlex


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


@command(
    name="timelog",
    description="Show timelog entries with grouping and export options",
    usage="/timelog [-p|--project=<project>] [-s|--start=<date>] [-e|--end=<date>] [-g|--group=<project|week|month>] [-o|--output=<csv|json|yaml>] [-f|--file=<filename>]",
    aliases=["tl", "time"],
)
class TimelogCommand(BaseCommand):
    """Command to show and export timelog entries."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the timelog command.

        Parameters
        ----------
        args : List[str]
            Command arguments with options
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
            project_filter: Optional[str] = None
            start_date: Optional[str] = None
            end_date: Optional[str] = None
            group_by: Optional[str] = None
            output_format: Optional[str] = None
            output_file: Optional[str] = None

            # Parse command line options
            i = 0
            while i < len(args):
                arg = args[i]

                # Handle long options
                if arg.startswith("--project="):
                    project_filter = arg.split("=", 1)[1]
                elif arg.startswith("--start="):
                    start_date = arg.split("=", 1)[1]
                elif arg.startswith("--end="):
                    end_date = arg.split("=", 1)[1]
                elif arg.startswith("--group="):
                    group_by = arg.split("=", 1)[1].lower()
                    if group_by not in ["project", "week", "month"]:
                        return CommandResult.error(
                            f"Invalid group option: {group_by}. Valid options: project, week, month"
                        )
                elif arg.startswith("--output="):
                    output_format = arg.split("=", 1)[1].lower()
                    if output_format not in ["csv", "json", "yaml"]:
                        return CommandResult.error(
                            f"Invalid output format: {output_format}. Valid options: csv, json, yaml"
                        )
                elif arg.startswith("--file="):
                    output_file = arg.split("=", 1)[1]

                # Handle short options
                elif arg == "-p" and i + 1 < len(args):
                    i += 1
                    project_filter = args[i]
                elif arg == "-s" and i + 1 < len(args):
                    i += 1
                    start_date = args[i]
                elif arg == "-e" and i + 1 < len(args):
                    i += 1
                    end_date = args[i]
                elif arg == "-g" and i + 1 < len(args):
                    i += 1
                    group_by = args[i].lower()
                    if group_by not in ["project", "week", "month"]:
                        return CommandResult.error(
                            f"Invalid group option: {group_by}. Valid options: project, week, month"
                        )
                elif arg == "-o" and i + 1 < len(args):
                    i += 1
                    output_format = args[i].lower()
                    if output_format not in ["csv", "json", "yaml"]:
                        return CommandResult.error(
                            f"Invalid output format: {output_format}. Valid options: csv, json, yaml"
                        )
                elif arg == "-f" and i + 1 < len(args):
                    i += 1
                    output_file = args[i]
                elif arg.startswith("-"):
                    return CommandResult.error(
                        f"Unknown option: {arg}. Use /help timelog for usage info"
                    )
                i += 1

            # Get timelog entries
            entries = storage.get_entities_by_type(
                EntityType.TIMELOG, status=None, limit=1000
            )

            if not entries:
                return CommandResult.error("No timelog entries found")

            # Filter by project if specified
            if project_filter:
                entries = [
                    entry
                    for entry in entries
                    if isinstance(entry, TimelogEntry)
                    and entry.project.lower() == project_filter.lower()
                ]

            # Filter by date range if specified
            if start_date or end_date:
                from dateutil import parser as date_parser

                if start_date:
                    try:
                        start_dt = date_parser.parse(start_date).date()
                        entries = [
                            entry
                            for entry in entries
                            if isinstance(entry, TimelogEntry) and entry.day >= start_dt
                        ]
                    except (ValueError, TypeError):
                        return CommandResult.error(f"Invalid start date: {start_date}")

                if end_date:
                    try:
                        end_dt = date_parser.parse(end_date).date()
                        entries = [
                            entry
                            for entry in entries
                            if isinstance(entry, TimelogEntry) and entry.day <= end_dt
                        ]
                    except (ValueError, TypeError):
                        return CommandResult.error(f"Invalid end date: {end_date}")

            if not entries:
                filter_desc = []
                if project_filter:
                    filter_desc.append(f"project '{project_filter}'")
                if start_date or end_date:
                    date_range = []
                    if start_date:
                        date_range.append(f"from {start_date}")
                    if end_date:
                        date_range.append(f"to {end_date}")
                    filter_desc.append(" ".join(date_range))

                filter_text = (
                    " with " + " and ".join(filter_desc) if filter_desc else ""
                )
                message = f"No timelog entries found{filter_text}"
                context.console.print(message, style="yellow")
                return CommandResult.ok(message)

            # Create DataFrame for processing
            data = []
            for entry in entries:
                if isinstance(entry, TimelogEntry):
                    data.append(
                        {
                            "pseudo_id": entry.pseudo_id,
                            "day": entry.day,
                            "project": entry.project,
                            "hours": entry.hours,
                            "notes": entry.notes or "",
                            "content": entry.content,
                        }
                    )

            df = pd.DataFrame(data)
            df["day"] = pd.to_datetime(df["day"])

            # Handle export to file
            if output_format and output_file:
                try:
                    # Create export data
                    export_df = df.copy()
                    export_df["day"] = export_df["day"].dt.strftime("%Y-%m-%d")

                    file_path = Path(output_file)
                    if output_format == "csv":
                        export_df.to_csv(file_path, index=False)
                    elif output_format == "json":
                        export_df.to_json(file_path, orient="records", indent=2)
                    elif output_format == "yaml":
                        with open(file_path, "w") as f:
                            yaml.dump(
                                export_df.to_dict("records"),
                                f,
                                default_flow_style=False,
                            )

                    return CommandResult.ok(
                        f"Exported {len(export_df)} entries to {file_path}"
                    )
                except Exception as e:
                    return CommandResult.error(f"Failed to export: {e}")

            # Group by if specified
            if group_by:
                if group_by == "project":
                    grouped = df.groupby("project")["hours"].sum().reset_index()
                    grouped = grouped.sort_values("hours", ascending=False)

                    # Create Rich table for project grouping
                    table = Table(
                        title=f"Time by Project ({grouped['hours'].sum():.1f} total hours)"
                    )
                    table.add_column("Project", style="bright_cyan")
                    table.add_column("Hours", style="white", justify="right")
                    table.add_column("Percentage", style="dim", justify="right")

                    total_hours = grouped["hours"].sum()
                    for _, row in grouped.iterrows():
                        percentage = (row["hours"] / total_hours) * 100
                        table.add_row(
                            row["project"], f"{row['hours']:.1f}", f"{percentage:.1f}%"
                        )

                elif group_by == "week":
                    df["week"] = df["day"].dt.to_period("W").astype(str)
                    grouped = df.groupby("week")["hours"].sum().reset_index()
                    grouped = grouped.sort_values("week")

                    # Create Rich table for week grouping
                    table = Table(
                        title=f"Time by Week ({grouped['hours'].sum():.1f} total hours)"
                    )
                    table.add_column("Week", style="bright_cyan")
                    table.add_column("Hours", style="white", justify="right")

                    for _, row in grouped.iterrows():
                        table.add_row(row["week"], f"{row['hours']:.1f}")

                elif group_by == "month":
                    df["month"] = df["day"].dt.to_period("M").astype(str)
                    grouped = df.groupby("month")["hours"].sum().reset_index()
                    grouped = grouped.sort_values("month")

                    # Create Rich table for month grouping
                    table = Table(
                        title=f"Time by Month ({grouped['hours'].sum():.1f} total hours)"
                    )
                    table.add_column("Month", style="bright_cyan")
                    table.add_column("Hours", style="white", justify="right")

                    for _, row in grouped.iterrows():
                        table.add_row(row["month"], f"{row['hours']:.1f}")

                context.console.print(table)
                return CommandResult.ok(f"Displayed grouped timelog data")

            else:
                # Show detailed entries table
                # Sort by date (most recent first)
                df = df.sort_values("day", ascending=False)

                # Create Rich table for detailed view
                title_parts = ["Timelog Entries"]
                if project_filter:
                    title_parts.append(f"for {project_filter}")
                if start_date or end_date:
                    date_parts = []
                    if start_date:
                        date_parts.append(f"from {start_date}")
                    if end_date:
                        date_parts.append(f"to {end_date}")
                    title_parts.append(" ".join(date_parts))

                total_hours = df["hours"].sum()
                title = f"{' '.join(title_parts)} ({len(df)} entries, {total_hours:.1f} hours)"

                table = Table(title=title)
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Date", style="white", no_wrap=True)
                table.add_column("Project", style="bright_cyan", no_wrap=True)
                table.add_column("Hours", style="white", no_wrap=True, justify="right")
                table.add_column("Notes", style="dim")

                for _, row in df.iterrows():
                    date_str = row["day"].strftime("%m/%d")
                    hours_str = f"{row['hours']:.1f}"
                    if row["hours"] == 8.0:
                        hours_str = "8.0 (full)"
                    elif row["hours"] == 4.0:
                        hours_str = "4.0 (half)"

                    table.add_row(
                        row["pseudo_id"],
                        date_str,
                        row["project"],
                        hours_str,
                        (
                            row["notes"][:50] + "..."
                            if len(row["notes"]) > 50
                            else row["notes"]
                        ),
                    )

                context.console.print(table)
                return CommandResult.ok(f"Displayed {len(df)} timelog entries")

        except Exception as e:
            return CommandResult.error(f"Failed to show timelog: {e}")


@command(
    name="at",
    description="Add a task directly without LLM - /at <category> <priority> <task text>",
    usage='/at <category> <priority> "<task text>"',
    aliases=["add-task"],
)
class AddTaskDirectCommand(BaseCommand):
    """Command to add a task directly without engaging the LLM."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the add task command.

        Parameters
        ----------
        args : List[str]
            Command arguments: <category> <priority> "<task text>"
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

            # Parse arguments: category priority "task text"
            if len(args) < 3:
                return CommandResult.error(
                    'Usage: /at <category> <priority> "<task text>". Example: /at chores high "do something boring"'
                )

            # Join all args and use shlex to properly handle quoted strings
            args_str = " ".join(args)
            try:
                parsed_args = shlex.split(args_str)
            except ValueError as e:
                return CommandResult.error(
                    f"Error parsing arguments: {e}. Make sure to quote the task text properly."
                )

            if len(parsed_args) < 3:
                return CommandResult.error(
                    'Usage: /at <category> <priority> "<task text>". Example: /at chores high "do something boring"'
                )

            category = parsed_args[0]
            priority = parsed_args[1].lower()
            task_text = " ".join(parsed_args[2:])

            # Validate priority
            valid_priorities = ["low", "medium", "high", "urgent"]
            if priority not in valid_priorities:
                return CommandResult.error(
                    f"Invalid priority '{priority}'. Valid priorities: {', '.join(valid_priorities)}"
                )

            # Create the task directly
            task = Task(
                content=task_text,
                category=category,
                priority=priority,  # type: ignore[arg-type]
                status=EntityStatus.ACTIVE,
            )

            # Store the task
            pseudo_id = storage.create_entity(task)

            # Show success message
            context.console.print(
                f"✅ Created task {pseudo_id}: {task_text}", style="green"
            )
            context.console.print(
                f"   Category: {category}, Priority: {priority.title()}", style="dim"
            )

            # Now show the task list using the same logic as ShowTasksCommand
            # Get open tasks (active and in-progress)
            active_tasks = storage.get_entities_by_type(
                EntityType.TASK, status=EntityStatus.ACTIVE, limit=100
            )
            in_progress_tasks = storage.get_entities_by_type(
                EntityType.TASK, status=EntityStatus.IN_PROGRESS, limit=100
            )
            tasks = active_tasks + in_progress_tasks

            # Sort by created date (newest first)
            tasks.sort(key=lambda x: x.created_at, reverse=True)

            if not tasks:
                context.console.print("No open tasks found", style="yellow")
                return CommandResult.ok(f"Created task {pseudo_id}")

            # Create Rich table matching the /st command format
            title = f"Open Tasks (sorted by created ↓) ({len(tasks)})"

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
                category_display = ""
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
                    category_display = f"[{color}]{task.category}[/{color}]"

                # Due date column
                due_date = ""
                if isinstance(task, Task) and task.due_date:
                    due_date = _format_datetime_short(task.due_date)
                elif isinstance(task, Event):
                    due_date = _format_datetime_short(task.start_datetime)
                elif isinstance(task, Reminder):
                    due_date = _format_datetime_short(task.trigger_datetime)

                table.add_row(
                    status_emoji,
                    priority_text,
                    category_display,
                    task_id,
                    task_desc,
                    due_date,
                )

            # Display table
            context.console.print("")
            context.console.print(table)

            return CommandResult.ok(
                f"Created task {pseudo_id} and displayed {len(tasks)} open tasks"
            )

        except Exception as e:
            return CommandResult.error(f"Failed to add task: {e}")


@command(
    name="ct",
    description="Complete a task directly without LLM - /ct <task_id>",
    usage="/ct <task_id>",
    aliases=["complete-task"],
)
class CompleteTaskDirectCommand(BaseCommand):
    """Command to complete a task directly without engaging the LLM."""

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """
        Execute the complete task command.

        Parameters
        ----------
        args : List[str]
            Command arguments: <task_id>
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

            # Parse arguments: task_id
            if len(args) != 1:
                return CommandResult.error("Usage: /ct <task_id>. Example: /ct T123")

            task_id = args[0]

            # Check if the task exists
            entity = storage.get_entity_by_pseudo_id(task_id)
            if not entity:
                return CommandResult.error(f"No entity found with ID '{task_id}'")

            if not isinstance(entity, Task):
                return CommandResult.error(
                    f"{task_id} is not a task. Only tasks can be completed."
                )

            # Check if already completed
            if entity.status == EntityStatus.COMPLETED:
                return CommandResult.error(f"Task {task_id} is already completed")

            # Update to completed status
            success = storage.update_entity(
                task_id, {"status": EntityStatus.COMPLETED.value}
            )

            if not success:
                return CommandResult.error(
                    f"Failed to complete task {task_id}. Please try again."
                )

            # Show success message
            context.console.print(
                f"✅ Completed task {task_id}: {entity.content}", style="green"
            )
            context.console.print(
                f"   Category: {entity.category}, Priority: {entity.priority.title() if entity.priority else 'None'}",
                style="dim",
            )

            return CommandResult.ok(f"Completed task {task_id}")

        except Exception as e:
            return CommandResult.error(f"Failed to complete task: {e}")
