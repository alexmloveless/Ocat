"""
Output formatters for productivity entities.

Provides consistent formatting for displaying productivity entities
in various formats (plain text, markdown, etc.).
"""

from datetime import datetime, timedelta
from typing import List, Optional
from .models import ProductivityEntity, Task, Event, Reminder, Memory, EntityType


def format_entity(entity: ProductivityEntity, format_type: str = "text") -> str:
    """
    Format a single entity for display.

    Parameters
    ----------
    entity : ProductivityEntity
        The entity to format
    format_type : str
        Output format: "text", "markdown", "json"

    Returns
    -------
    str
        Formatted entity string
    """
    if format_type == "markdown":
        return _format_entity_markdown(entity)
    elif format_type == "json":
        return entity.model_dump_json(indent=2)
    else:
        return _format_entity_text(entity)


def format_entity_list(
    entities: List[ProductivityEntity],
    format_type: str = "text",
    title: Optional[str] = None,
) -> str:
    """
    Format a list of entities for display.

    Parameters
    ----------
    entities : List[ProductivityEntity]
        List of entities to format
    format_type : str
        Output format: "text", "markdown", "csv"
    title : Optional[str]
        Optional title for the list

    Returns
    -------
    str
        Formatted entity list
    """
    if not entities:
        return "No entities found."

    if format_type == "markdown":
        return _format_entity_list_markdown(entities, title)
    elif format_type == "csv":
        return _format_entity_list_csv(entities)
    else:
        return _format_entity_list_text(entities, title)


def _format_entity_text(entity: ProductivityEntity) -> str:
    """Format entity as plain text."""
    lines = []

    # Header with ID and type
    lines.append(f"{entity.pseudo_id} ({entity.entity_type.value}): {entity.content}")

    # Status
    lines.append(f"  Status: {entity.status.value}")

    # Type-specific details
    if isinstance(entity, Task):
        if entity.due_date:
            lines.append(f"  Due: {_format_datetime(entity.due_date)}")
        if entity.category:
            lines.append(f"  Category: {entity.category}")
        if entity.priority:
            lines.append(f"  Priority: {entity.priority}")
        if entity.tags:
            lines.append(f"  Tags: {', '.join(entity.tags)}")

    elif isinstance(entity, Event):
        lines.append(f"  Start: {_format_datetime(entity.start_datetime)}")
        if entity.end_datetime:
            lines.append(f"  End: {_format_datetime(entity.end_datetime)}")
        if entity.all_day:
            lines.append("  All-day event")
        if entity.participants:
            lines.append(f"  Participants: {', '.join(entity.participants)}")
        if entity.location:
            lines.append(f"  Location: {entity.location}")

    elif isinstance(entity, Reminder):
        lines.append(f"  Trigger: {_format_datetime(entity.trigger_datetime)}")
        if entity.category:
            lines.append(f"  Category: {entity.category}")
        if entity.recurring:
            lines.append("  Recurring: Yes")

    elif isinstance(entity, Memory):
        if entity.category:
            lines.append(f"  Category: {entity.category}")
        if entity.tags:
            lines.append(f"  Tags: {', '.join(entity.tags)}")

    # Created/updated dates
    lines.append(f"  Created: {_format_datetime(entity.created_at)}")
    if entity.updated_at and entity.updated_at != entity.created_at:
        lines.append(f"  Updated: {_format_datetime(entity.updated_at)}")

    return "\n".join(lines)


def _format_entity_markdown(entity: ProductivityEntity) -> str:
    """Format entity as markdown."""
    lines = []

    # Header with ID and type
    emoji = {
        EntityType.TASK: "✅",
        EntityType.EVENT: "📅",
        EntityType.REMINDER: "⏰",
        EntityType.MEMORY: "💾",
    }.get(entity.entity_type, "📋")

    status_indicator = {
        "active": "🔵",
        "completed": "✅",
        "in_progress": "🟡",
        "deleted": "🗑️",
    }.get(entity.status.value, "🔵")

    lines.append(f"## {emoji} {entity.pseudo_id}: {entity.content}")
    lines.append(f"**Status:** {status_indicator} {entity.status.value.title()}")
    lines.append("")

    # Type-specific details
    if isinstance(entity, Task):
        if entity.due_date:
            lines.append(f"**Due:** {_format_datetime(entity.due_date)}")
        if entity.category:
            lines.append(f"**Category:** {entity.category}")
        if entity.priority:
            lines.append(f"**Priority:** {entity.priority.title()}")
        if entity.tags:
            tag_list = " ".join([f"`{tag}`" for tag in entity.tags])
            lines.append(f"**Tags:** {tag_list}")

    elif isinstance(entity, Event):
        lines.append(f"**Start:** {_format_datetime(entity.start_datetime)}")
        if entity.end_datetime:
            lines.append(f"**End:** {_format_datetime(entity.end_datetime)}")
        if entity.all_day:
            lines.append("**Type:** All-day event")
        if entity.participants:
            lines.append(f"**Participants:** {', '.join(entity.participants)}")
        if entity.location:
            lines.append(f"**Location:** {entity.location}")

    elif isinstance(entity, Reminder):
        lines.append(f"**Trigger:** {_format_datetime(entity.trigger_datetime)}")
        if entity.category:
            lines.append(f"**Category:** {entity.category}")
        if entity.recurring:
            lines.append("**Recurring:** Yes")

    elif isinstance(entity, Memory):
        if entity.category:
            lines.append(f"**Category:** {entity.category}")
        if entity.tags:
            tag_list = " ".join([f"`{tag}`" for tag in entity.tags])
            lines.append(f"**Tags:** {tag_list}")

    lines.append("")
    lines.append(f"*Created: {_format_datetime(entity.created_at)}*")
    if entity.updated_at and entity.updated_at != entity.created_at:
        lines.append(f"*Updated: {_format_datetime(entity.updated_at)}*")

    return "\n".join(lines)


def _format_entity_list_text(
    entities: List[ProductivityEntity], title: Optional[str] = None
) -> str:
    """Format entity list as plain text."""
    lines = []

    if title:
        lines.append(f"{title} ({len(entities)} items)")
        lines.append("=" * len(lines[0]))
        lines.append("")

    for i, entity in enumerate(entities):
        if i > 0:
            lines.append("")

        # Compact format for lists
        status_icon = {
            "active": "●",
            "completed": "✓",
            "in_progress": "◐",
            "deleted": "✗",
        }.get(entity.status.value, "●")

        type_icon = {
            EntityType.TASK: "[T]",
            EntityType.EVENT: "[E]",
            EntityType.REMINDER: "[R]",
            EntityType.MEMORY: "[M]",
        }.get(entity.entity_type, "[?]")

        # Main line with ID, type, status, and content
        main_line = f"{status_icon} {type_icon} {entity.pseudo_id}: {entity.content}"
        lines.append(main_line)

        # Add key details on second line
        details = []
        if isinstance(entity, Task) and entity.due_date:
            details.append(f"Due: {_format_datetime_short(entity.due_date)}")
        elif isinstance(entity, Event):
            details.append(f"Start: {_format_datetime_short(entity.start_datetime)}")
        elif isinstance(entity, Reminder):
            details.append(
                f"Trigger: {_format_datetime_short(entity.trigger_datetime)}"
            )

        if isinstance(entity, (Task, Memory)) and entity.category:
            details.append(f"Category: {entity.category}")
        elif isinstance(entity, Event) and entity.location:
            details.append(f"Location: {entity.location}")

        if details:
            lines.append(f"    {' | '.join(details)}")

    return "\n".join(lines)


def _format_entity_list_markdown(
    entities: List[ProductivityEntity], title: Optional[str] = None
) -> str:
    """Format entity list as markdown table."""
    lines = []

    if title:
        lines.append(f"## {title}")
        lines.append(f"*{len(entities)} items*")
        lines.append("")

    # Create simplified table with 3 columns
    lines.append("| ID | Status | Task |")
    lines.append("|---|---|---|")

    for entity in entities:
        type_emoji = {
            EntityType.TASK: "✅",
            EntityType.EVENT: "📅",
            EntityType.REMINDER: "⏰",
            EntityType.MEMORY: "💾",
            EntityType.LIST_ITEM: "📝",
        }.get(entity.entity_type, "📋")

        # Only show status emoji if status is set
        status_emoji = ""
        if entity.status:
            status_map = {
                "active": "🔵",
                "completed": "✅",
                "in_progress": "🟡",
                "deleted": "🗑️",
                "archived": "📦",
            }
            status_emoji = status_map.get(entity.status.value, "")

        # Build task description with category and due date inline
        task_desc = entity.content

        # Add category if present
        if hasattr(entity, "category") and entity.category:
            task_desc += f" `[{entity.category}]`"

        # Add due date if present
        if isinstance(entity, Task) and entity.due_date:
            task_desc += f" 📅 {_format_datetime_short(entity.due_date)}"
        elif isinstance(entity, Event):
            task_desc += f" 📅 {_format_datetime_short(entity.start_datetime)}"
        elif isinstance(entity, Reminder):
            task_desc += f" ⏰ {_format_datetime_short(entity.trigger_datetime)}"

        lines.append(
            f"| `{entity.pseudo_id}` | {status_emoji} | {type_emoji} {task_desc} |"
        )

    return "\n".join(lines)


def _format_entity_list_csv(entities: List[ProductivityEntity]) -> str:
    """Format entity list as CSV."""
    lines = []

    # Header
    lines.append("ID,Type,Status,Content,Created,Updated,Details")

    for entity in entities:
        # Escape commas and quotes in content
        content = entity.content.replace('"', '""')
        if "," in content:
            content = f'"{content}"'

        created = entity.created_at.strftime("%Y-%m-%d %H:%M")
        updated = (
            entity.updated_at.strftime("%Y-%m-%d %H:%M") if entity.updated_at else ""
        )

        # Build details based on entity type
        details = []
        if isinstance(entity, Task):
            if entity.due_date:
                details.append(f"Due: {entity.due_date.strftime('%Y-%m-%d %H:%M')}")
            if entity.category:
                details.append(f"Category: {entity.category}")
        elif isinstance(entity, Event):
            details.append(f"Start: {entity.start_datetime.strftime('%Y-%m-%d %H:%M')}")
            if entity.location:
                details.append(f"Location: {entity.location}")
        elif isinstance(entity, Reminder):
            details.append(
                f"Trigger: {entity.trigger_datetime.strftime('%Y-%m-%d %H:%M')}"
            )

        details_text = "; ".join(details)
        if "," in details_text:
            details_text = f'"{details_text}"'

        lines.append(
            f"{entity.pseudo_id},{entity.entity_type.value},{entity.status.value},{content},{created},{updated},{details_text}"
        )

    return "\n".join(lines)


def _format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    now = datetime.now()

    # If it's today, show time only
    if dt.date() == now.date():
        return f"Today at {dt.strftime('%I:%M %p')}"

    # If it's tomorrow
    elif dt.date() == (
        now.date().replace(day=now.day + 1) if now.day < 28 else now.date()
    ):
        return f"Tomorrow at {dt.strftime('%I:%M %p')}"

    # If it's this week
    elif (dt - now).days < 7 and dt > now:
        return dt.strftime("%A at %I:%M %p")

    # Otherwise, full date
    return dt.strftime("%B %d, %Y at %I:%M %p")


def _format_datetime_short(dt: datetime) -> str:
    """Format datetime in short form for lists with relative dates."""
    now = datetime.now()
    today = now.date()
    dt_date = dt.date()

    # If it's today
    if dt_date == today:
        return "today"

    # If it's tomorrow
    elif dt_date == today + timedelta(days=1):
        return "tomorrow"

    # If it's yesterday
    elif dt_date == today - timedelta(days=1):
        return "yesterday"

    # If it's this year
    elif dt.year == now.year:
        return dt.strftime("%d-%b")

    # Otherwise include year
    return dt.strftime("%d-%b-%y")
