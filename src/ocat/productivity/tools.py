"""
Pydantic-AI tool functions for productivity system.

Provides natural language interface to create, read, update, and delete
productivity entities (tasks, events, reminders, memories).
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry

from .storage import ProductivityStorage
from .models import (
    Task,
    Event,
    Reminder,
    Memory,
    ListItem,
    EntityType,
    EntityStatus,
    create_entity,
)
from .formatters import format_entity, format_entity_list


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""

    content: str = Field(description="Task description or title")
    due_date: Optional[str] = Field(
        None,
        description="When the task is due (e.g., 'tomorrow', 'next Friday', '2024-12-25')",
    )
    category: Optional[str] = Field(None, description="Task category or project name")
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    priority: Optional[str] = Field(
        None, description="Priority level: low, medium, high, urgent"
    )


class EventCreateRequest(BaseModel):
    """Request model for creating an event."""

    content: str = Field(description="Event title or description")
    start_datetime: str = Field(
        description="When the event starts (e.g., 'tomorrow at 2pm', 'next Friday at 9am')"
    )
    end_datetime: Optional[str] = Field(
        None, description="When the event ends (optional)"
    )
    participants: Optional[str] = Field(
        None, description="Comma-separated list of participants"
    )
    location: Optional[str] = Field(None, description="Event location")
    all_day: bool = Field(default=False, description="Whether this is an all-day event")


class ReminderCreateRequest(BaseModel):
    """Request model for creating a reminder."""

    content: str = Field(description="What to be reminded about")
    trigger_datetime: str = Field(
        description="When to trigger the reminder (e.g., 'tomorrow at 10am')"
    )
    category: Optional[str] = Field(None, description="Reminder category")
    recurring: bool = Field(default=False, description="Whether this reminder repeats")


class MemoryCreateRequest(BaseModel):
    """Request model for creating a memory."""

    content: str = Field(description="Information to remember")
    category: Optional[str] = Field(None, description="Memory category or topic")
    tags: Optional[str] = Field(None, description="Comma-separated tags")


class ListItemCreateRequest(BaseModel):
    """Request model for creating a list item."""

    content: str = Field(description="List item description")
    list_name: str = Field(description="Name of the list this item belongs to")
    category: Optional[str] = Field(None, description="Item category or classification")
    tags: Optional[str] = Field(None, description="Comma-separated tags")


class EntityUpdateRequest(BaseModel):
    """Request model for updating an entity."""

    pseudo_id: str = Field(description="Entity ID (e.g., 'task001', 'event005')")
    content: Optional[str] = Field(None, description="Updated content/description")
    status: Optional[str] = Field(
        None, description="Updated status: active, completed, in_progress, deleted"
    )
    due_date: Optional[str] = Field(None, description="Updated due date (tasks only)")
    start_datetime: Optional[str] = Field(
        None, description="Updated start time (events only)"
    )
    end_datetime: Optional[str] = Field(
        None, description="Updated end time (events only)"
    )
    trigger_datetime: Optional[str] = Field(
        None, description="Updated trigger time (reminders only)"
    )
    category: Optional[str] = Field(None, description="Updated category")
    tags: Optional[str] = Field(None, description="Updated tags")
    priority: Optional[str] = Field(None, description="Updated priority (tasks only)")
    participants: Optional[str] = Field(
        None, description="Updated participants (events only)"
    )
    location: Optional[str] = Field(None, description="Updated location (events only)")


class EntitySearchRequest(BaseModel):
    """Request model for searching entities."""

    query: Optional[str] = Field(
        None, description="Text to search for in entity content"
    )
    entity_types: Optional[List[str]] = Field(
        None, description="Filter by entity types: task, event, reminder, memory"
    )
    status: Optional[str] = Field(
        None, description="Filter by status: active, completed, in_progress, deleted"
    )
    limit: int = Field(default=10, description="Maximum number of results to return")


# Create productivity agent
productivity_agent: Agent[ProductivityStorage, str] = Agent(
    "openai:gpt-4o-mini",  # Use a fast, cost-effective model for tool calls
    deps_type=ProductivityStorage,
    system_prompt="""You are a productivity assistant that helps manage tasks, events, reminders, memories, and lists.

You have access to tools for creating, reading, updating, and deleting productivity entities. Use these tools when users ask to:
- Create tasks, events, reminders, memories, or list items
- Show, list, or find existing entities  
- Update or modify entities
- Mark tasks as complete, archive list items, or delete entities
- Search through their productivity data
- Manage categorized lists of items

For list management specifically:
- Use create_list_item to add items to named lists with optional categories
- Use list_items to show items in a specific list or all items
- Use get_list_summary to show all available lists with counts
- Use archive_list_item to archive items (don't delete them)

When users provide natural language requests like "remind me to call mom tomorrow at 3pm", "add a meeting with the team on Friday", or "add milk to shopping list", 
use the appropriate creation tools with the parsed information.

Always be helpful and confirm what actions you've taken. If information is missing or unclear, ask for clarification rather than guessing.
""",
)


@productivity_agent.tool
async def create_task(
    ctx: RunContext[ProductivityStorage], request: TaskCreateRequest
) -> str:
    """Create a new task with optional due date, category, tags, and priority."""
    try:
        # Create task entity with explicit parameters
        task = Task(  # type: ignore[call-arg]
            content=request.content,
            due_date=request.due_date,  # type: ignore[arg-type]
            category=request.category,
            tags=request.tags,  # type: ignore[arg-type]
            priority=request.priority,  # type: ignore[arg-type]
        )
        pseudo_id = ctx.deps.create_entity(task)

        return f"Created task {pseudo_id}: {task.content}" + (
            f" (due: {task.due_date})" if task.due_date else ""
        )

    except Exception as e:
        raise ModelRetry(
            f"Failed to create task: {str(e)}. Please check the task details and try again."
        )


@productivity_agent.tool
async def create_event(
    ctx: RunContext[ProductivityStorage], request: EventCreateRequest
) -> str:
    """Create a new event/meeting with date, time, and optional participants."""
    try:
        # Create event entity with explicit parameters
        event = Event(  # type: ignore[call-arg]
            content=request.content,
            start_datetime=request.start_datetime,  # type: ignore[arg-type]
            end_datetime=request.end_datetime,  # type: ignore[arg-type]
            all_day=request.all_day,
            participants=request.participants,  # type: ignore[arg-type]
            location=request.location,
        )
        pseudo_id = ctx.deps.create_entity(event)

        participants_text = (
            f" with {', '.join(event.participants)}" if event.participants else ""
        )
        location_text = f" at {event.location}" if event.location else ""

        return f"Created event {pseudo_id}: {event.content} on {event.start_datetime}{participants_text}{location_text}"

    except Exception as e:
        raise ModelRetry(
            f"Failed to create event: {str(e)}. Please check the date/time format and try again."
        )


@productivity_agent.tool
async def create_reminder(
    ctx: RunContext[ProductivityStorage], request: ReminderCreateRequest
) -> str:
    """Create a new reminder with trigger date and time."""
    try:
        # Create reminder entity with explicit parameters
        reminder = Reminder(  # type: ignore[call-arg]
            content=request.content,
            trigger_datetime=request.trigger_datetime,  # type: ignore[arg-type]
            category=request.category,
            recurring=request.recurring,
        )
        pseudo_id = ctx.deps.create_entity(reminder)

        recurring_text = " (recurring)" if reminder.recurring else ""

        return f"Created reminder {pseudo_id}: {reminder.content} for {reminder.trigger_datetime}{recurring_text}"

    except Exception as e:
        raise ModelRetry(
            f"Failed to create reminder: {str(e)}. Please check the date/time format and try again."
        )


@productivity_agent.tool
async def create_memory(
    ctx: RunContext[ProductivityStorage], request: MemoryCreateRequest
) -> str:
    """Create a new memory to store information for later retrieval."""
    try:
        # Create memory entity with explicit parameters
        memory = Memory(  # type: ignore[call-arg]
            content=request.content,
            category=request.category,
            tags=request.tags,  # type: ignore[arg-type]
        )
        pseudo_id = ctx.deps.create_entity(memory)

        category_text = f" in category '{memory.category}'" if memory.category else ""

        return f"Saved memory {pseudo_id}: {memory.content}{category_text}"

    except Exception as e:
        raise ModelRetry(f"Failed to create memory: {str(e)}. Please try again.")


@productivity_agent.tool
async def get_entity_by_id(ctx: RunContext[ProductivityStorage], entity_id: str) -> str:
    """Get a specific entity by its ID (e.g., 'task001', 'event005')."""
    try:
        entity = ctx.deps.get_entity_by_pseudo_id(entity_id)

        if not entity:
            return f"No entity found with ID '{entity_id}'. Please check the ID and try again."

        return format_entity(entity)

    except Exception as e:
        raise ModelRetry(
            f"Failed to retrieve entity: {str(e)}. Please check the ID format."
        )


@productivity_agent.tool
async def update_entity(
    ctx: RunContext[ProductivityStorage], request: EntityUpdateRequest
) -> str:
    """Update an existing entity (task, event, reminder, memory, or list item) by its ID. Can update status, content, category, tags, and entity-specific fields."""
    try:
        # Get the existing entity first
        entity = ctx.deps.get_entity_by_pseudo_id(request.pseudo_id)
        if not entity:
            return f"No entity found with ID '{request.pseudo_id}'. Please check the ID and try again."

        # Build update dictionary with only provided fields
        updates = {}

        # Common fields
        if request.content is not None:
            updates["content"] = request.content
        if request.status is not None:
            updates["status"] = request.status
        if request.category is not None:
            updates["category"] = request.category
        if request.tags is not None:
            updates["tags"] = request.tags

        # Entity-specific fields
        if isinstance(entity, Task):
            if request.due_date is not None:
                updates["due_date"] = request.due_date
            if request.priority is not None:
                updates["priority"] = request.priority
        elif isinstance(entity, Event):
            if request.start_datetime is not None:
                updates["start_datetime"] = request.start_datetime
            if request.end_datetime is not None:
                updates["end_datetime"] = request.end_datetime
            if request.participants is not None:
                updates["participants"] = request.participants
            if request.location is not None:
                updates["location"] = request.location
        elif isinstance(entity, Reminder):
            if request.trigger_datetime is not None:
                updates["trigger_datetime"] = request.trigger_datetime

        if not updates:
            return f"No updates provided for {request.pseudo_id}. Please specify what you'd like to change."

        # Perform update
        success = ctx.deps.update_entity(request.pseudo_id, updates)

        if success:
            # Get updated entity to show result
            updated_entity = ctx.deps.get_entity_by_pseudo_id(request.pseudo_id)
            if updated_entity:
                return f"Updated {request.pseudo_id}:\n{format_entity(updated_entity)}"
            else:
                return f"Successfully updated {request.pseudo_id}"
        else:
            return f"Failed to update {request.pseudo_id}. Please check the ID and try again."

    except Exception as e:
        raise ModelRetry(
            f"Failed to update entity: {str(e)}. Please check your input and try again."
        )


@productivity_agent.tool
async def delete_entity(ctx: RunContext[ProductivityStorage], entity_id: str) -> str:
    """Delete an entity by marking it as deleted (soft delete)."""
    try:
        # Check if entity exists first
        entity = ctx.deps.get_entity_by_pseudo_id(entity_id)
        if not entity:
            return f"No entity found with ID '{entity_id}'. Please check the ID and try again."

        # Soft delete by updating status
        success = ctx.deps.delete_entity(entity_id)

        if success:
            return f"Deleted {entity_id}: {entity.content}"
        else:
            return f"Failed to delete {entity_id}. Please try again."

    except Exception as e:
        raise ModelRetry(
            f"Failed to delete entity: {str(e)}. Please check the ID and try again."
        )


@productivity_agent.tool
async def search_entities(
    ctx: RunContext[ProductivityStorage], request: EntitySearchRequest
) -> str:
    """Search for entities by text, type, or status."""
    try:
        # Convert entity type strings to EntityType enums
        entity_types = None
        if request.entity_types:
            entity_types = []
            for et_str in request.entity_types:
                try:
                    entity_types.append(EntityType(et_str.lower()))
                except ValueError:
                    continue

        # Convert status string to EntityStatus enum
        status = None
        if request.status:
            try:
                status = EntityStatus(request.status.lower())
            except ValueError:
                pass

        # Perform search
        entities = ctx.deps.search_entities(
            query=request.query or "",
            entity_types=entity_types,
            status=status,
            limit=request.limit,
        )

        if not entities:
            search_desc = []
            if request.query:
                search_desc.append(f"text '{request.query}'")
            if request.entity_types:
                search_desc.append(f"types {', '.join(request.entity_types)}")
            if request.status:
                search_desc.append(f"status '{request.status}'")

            search_text = " with " + " and ".join(search_desc) if search_desc else ""
            return f"No entities found{search_text}."

        return format_entity_list(entities, format_type="markdown")

    except Exception as e:
        raise ModelRetry(
            f"Failed to search entities: {str(e)}. Please check your search criteria."
        )


@productivity_agent.tool
async def list_tasks(
    ctx: RunContext[ProductivityStorage], status: Optional[str] = None, limit: int = 20
) -> str:
    """List all tasks, optionally filtered by status."""
    try:
        # Convert status to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = EntityStatus(status.lower())
            except ValueError:
                status_enum = EntityStatus.ACTIVE  # Default to active if invalid status
        else:
            status_enum = EntityStatus.ACTIVE  # Default to active tasks

        tasks = ctx.deps.get_entities_by_type(
            EntityType.TASK, status=status_enum, limit=limit
        )

        if not tasks:
            status_text = f" with status '{status}'" if status else ""
            return f"No tasks found{status_text}."

        return format_entity_list(
            tasks, format_type="markdown", title=f"Tasks ({status_enum.value})"
        )

    except Exception as e:
        raise ModelRetry(f"Failed to list tasks: {str(e)}. Please try again.")


@productivity_agent.tool
async def list_events(ctx: RunContext[ProductivityStorage], limit: int = 20) -> str:
    """List all upcoming events."""
    try:
        events = ctx.deps.get_entities_by_type(
            EntityType.EVENT, status=EntityStatus.ACTIVE, limit=limit
        )

        if not events:
            return "No upcoming events found."

        return format_entity_list(events, title="Upcoming Events")

    except Exception as e:
        raise ModelRetry(f"Failed to list events: {str(e)}. Please try again.")


@productivity_agent.tool
async def list_reminders(ctx: RunContext[ProductivityStorage], limit: int = 20) -> str:
    """List all active reminders."""
    try:
        reminders = ctx.deps.get_entities_by_type(
            EntityType.REMINDER, status=EntityStatus.ACTIVE, limit=limit
        )

        if not reminders:
            return "No active reminders found."

        return format_entity_list(reminders, title="Active Reminders")

    except Exception as e:
        raise ModelRetry(f"Failed to list reminders: {str(e)}. Please try again.")


@productivity_agent.tool
async def mark_task_complete(ctx: RunContext[ProductivityStorage], task_id: str) -> str:
    """Mark a specific task as completed."""
    try:
        # Check if it's a task
        entity = ctx.deps.get_entity_by_pseudo_id(task_id)
        if not entity:
            return f"No entity found with ID '{task_id}'."

        if not isinstance(entity, Task):
            return f"{task_id} is not a task. Only tasks can be marked as complete."

        # Update to completed status
        success = ctx.deps.update_entity(
            task_id, {"status": EntityStatus.COMPLETED.value}
        )

        if success:
            return f"Marked task {task_id} as completed: {entity.content}"
        else:
            return f"Failed to mark task {task_id} as completed. Please try again."

    except Exception as e:
        raise ModelRetry(
            f"Failed to mark task complete: {str(e)}. Please check the task ID."
        )


@productivity_agent.tool
async def create_list_item(
    ctx: RunContext[ProductivityStorage], request: ListItemCreateRequest
) -> str:
    """Create a new list item."""
    try:
        list_item = create_entity(
            EntityType.LIST_ITEM,
            content=request.content,
            list_name=request.list_name,
            category=request.category,
            tags=request.tags.split(",") if request.tags else [],
        )

        # Store the list item
        pseudo_id = ctx.deps.create_entity(list_item)

        return (
            f"Created list item {pseudo_id} in '{request.list_name}': {request.content}"
        )

    except Exception as e:
        raise ModelRetry(f"Failed to create list item: {str(e)}. Please try again.")


@productivity_agent.tool
async def list_items(
    ctx: RunContext[ProductivityStorage],
    list_name: Optional[str] = None,
    limit: int = 20,
) -> str:
    """List all list items, optionally filtered by list name."""
    try:
        items = ctx.deps.get_entities_by_type(
            EntityType.LIST_ITEM, status=None, limit=limit
        )

        # Filter by list name if specified
        if list_name:
            items = [
                item for item in items if item.list_name.lower() == list_name.lower()
            ]

        if not items:
            if list_name:
                return f"No items found in list '{list_name}'."
            else:
                return "No list items found."

        if list_name:
            return format_entity_list(items, title=f"List: {list_name}")
        else:
            return format_entity_list(items, title="All List Items")

    except Exception as e:
        raise ModelRetry(f"Failed to list items: {str(e)}. Please try again.")


@productivity_agent.tool
async def update_list_item_status(
    ctx: RunContext[ProductivityStorage], item_id: str, status: str
) -> str:
    """Update the status of a specific list item (active, completed, in_progress, archived, deleted)."""
    try:
        # Check if it's a list item
        entity = ctx.deps.get_entity_by_pseudo_id(item_id)
        if not entity:
            return f"No entity found with ID '{item_id}'."

        if not isinstance(entity, ListItem):
            return f"{item_id} is not a list item. Only list items can have their status updated."

        # Update status - debug what's happening
        update_data = {"status": status}
        success = ctx.deps.update_entity(item_id, update_data)

        if success:
            # Get the updated entity to verify the change
            updated_entity = ctx.deps.get_entity_by_pseudo_id(item_id)
            if updated_entity:
                actual_status = (
                    updated_entity.status.value if updated_entity.status else "None"
                )
                return f"Updated list item {item_id} status from '{entity.status.value if entity.status else 'None'}' to '{actual_status}': {entity.content}"
            else:
                return f"Updated list item {item_id} status to '{status}': {entity.content}"
        else:
            return f"Failed to update list item {item_id} status to '{status}'. Please try again."

    except Exception as e:
        raise ModelRetry(f"Failed to update list item status: {str(e)}")


@productivity_agent.tool
async def archive_list_item(ctx: RunContext[ProductivityStorage], item_id: str) -> str:
    """Archive a specific list item."""
    try:
        # Check if it's a list item
        entity = ctx.deps.get_entity_by_pseudo_id(item_id)
        if not entity:
            return f"No entity found with ID '{item_id}'."

        if not isinstance(entity, ListItem):
            return f"{item_id} is not a list item. Only list items can be archived."

        # Update to archived status
        success = ctx.deps.update_entity(
            item_id, {"status": EntityStatus.ARCHIVED.value}
        )

        if success:
            return f"Archived list item {item_id}: {entity.content}"
        else:
            return f"Failed to archive list item {item_id}. Please try again."

    except Exception as e:
        raise ModelRetry(
            f"Failed to archive list item: {str(e)}. Please check the item ID."
        )


@productivity_agent.tool
async def get_list_summary(ctx: RunContext[ProductivityStorage]) -> str:
    """Get a summary of all lists with item counts."""
    try:
        items = ctx.deps.get_entities_by_type(
            EntityType.LIST_ITEM, status=None, limit=1000
        )

        if not items:
            return "No lists found."

        # Group by list name
        list_counts = {}
        for item in items:
            list_name = item.list_name
            if list_name not in list_counts:
                list_counts[list_name] = 0
            list_counts[list_name] += 1

        # Format the summary
        summary_lines = ["# Available Lists", ""]
        for list_name, count in sorted(list_counts.items()):
            summary_lines.append(f"- **{list_name}**: {count} items")

        return "\n".join(summary_lines)

    except Exception as e:
        raise ModelRetry(f"Failed to get list summary: {str(e)}. Please try again.")
