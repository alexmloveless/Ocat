"""
Pydantic models for productivity entities.

Defines the data structures for tasks, events, reminders, and memories
with validation and serialization capabilities.
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import re
from dateutil import parser as date_parser

from pydantic import BaseModel, Field, field_validator, model_validator


class EntityType(str, Enum):
    """Types of productivity entities."""

    TASK = "task"
    EVENT = "event"
    REMINDER = "reminder"
    MEMORY = "memory"
    LIST_ITEM = "list_item"
    TIMELOG = "timelog"


class EntityStatus(str, Enum):
    """Status values for productivity entities."""

    ACTIVE = "active"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    DELETED = "deleted"
    ARCHIVED = "archived"


class BaseEntity(BaseModel):
    """
    Base model for all productivity entities.

    Contains common fields shared across all entity types.
    """

    pseudo_id: Optional[str] = Field(None, description="Human-readable ID like task001")
    entity_type: EntityType = Field(description="Type of entity")
    content: str = Field(description="Main text content describing the entity")
    status: Optional[EntityStatus] = Field(
        default=EntityStatus.ACTIVE, description="Current status (defaults to active)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("status")
    @classmethod
    def normalize_status(cls, v):
        """Normalize status values from natural language."""
        if isinstance(v, str):
            v = v.lower().strip()
            # Map common variations to standard values
            status_map = {
                "done": EntityStatus.COMPLETED,
                "finished": EntityStatus.COMPLETED,
                "complete": EntityStatus.COMPLETED,
                "completed": EntityStatus.COMPLETED,
                "active": EntityStatus.ACTIVE,
                "open": EntityStatus.ACTIVE,
                "new": EntityStatus.ACTIVE,
                "in_progress": EntityStatus.IN_PROGRESS,
                "in-progress": EntityStatus.IN_PROGRESS,
                "working": EntityStatus.IN_PROGRESS,
                "started": EntityStatus.IN_PROGRESS,
                "deleted": EntityStatus.DELETED,
                "removed": EntityStatus.DELETED,
                "cancelled": EntityStatus.DELETED,
            }
            return status_map.get(v, EntityStatus.ACTIVE)
        return v

    @model_validator(mode="before")
    @classmethod
    def set_updated_at(cls, values):
        """Set updated_at when entity is modified."""
        if isinstance(values, dict):
            if "updated_at" not in values or values["updated_at"] is None:
                values["updated_at"] = datetime.now()
        return values

    class Config:
        use_enum_values = True


class Task(BaseEntity):
    """
    Task entity with due dates, categories, and tags.
    """

    entity_type: Literal[EntityType.TASK] = EntityType.TASK
    due_date: Optional[datetime] = Field(None, description="When the task is due")
    category: Optional[str] = Field(None, description="Task category or project")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = Field(
        "medium", description="Task priority"
    )

    @field_validator("due_date", mode="before")
    @classmethod
    def parse_due_date(cls, v):
        """Parse due date from various string formats."""
        if v is None or isinstance(v, datetime):
            return v

        if isinstance(v, str):
            try:
                # Handle common relative dates
                v_lower = v.lower().strip()
                if v_lower in ["today", "tonight"]:
                    return datetime.now().replace(
                        hour=23, minute=59, second=59, microsecond=0
                    )
                elif v_lower in ["tomorrow"]:
                    tomorrow = datetime.now().replace(
                        hour=23, minute=59, second=59, microsecond=0
                    )
                    return tomorrow.replace(day=tomorrow.day + 1)
                elif v_lower.startswith("next "):
                    # Handle "next monday", "next week", etc.
                    return date_parser.parse(v, fuzzy=True)
                else:
                    return date_parser.parse(v, fuzzy=True)
            except (ValueError, TypeError):
                return None

        return v

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """Parse tags from string or list."""
        if isinstance(v, str):
            # Split on commas, semicolons, or spaces
            tags = re.split(r"[,;\s]+", v.strip())
            return [tag.strip() for tag in tags if tag.strip()]
        elif isinstance(v, list):
            return [str(tag).strip() for tag in v if str(tag).strip()]
        return v or []


class Event(BaseEntity):
    """
    Event/meeting entity with datetime, participants, and duration.
    """

    entity_type: Literal[EntityType.EVENT] = EntityType.EVENT
    start_datetime: datetime = Field(description="When the event starts")
    end_datetime: Optional[datetime] = Field(None, description="When the event ends")
    all_day: bool = Field(default=False, description="Whether this is an all-day event")
    participants: List[str] = Field(
        default_factory=list, description="Event participants"
    )
    location: Optional[str] = Field(None, description="Event location")

    @field_validator("start_datetime", mode="before")
    @classmethod
    def parse_start_datetime(cls, v):
        """Parse start datetime from various formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v, fuzzy=True)
            except (ValueError, TypeError):
                raise ValueError(f"Could not parse datetime: {v}")
        raise ValueError("start_datetime is required")

    @field_validator("end_datetime", mode="before")
    @classmethod
    def parse_end_datetime(cls, v):
        """Parse end datetime from various formats."""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v, fuzzy=True)
            except (ValueError, TypeError):
                return None
        return v

    @field_validator("participants", mode="before")
    @classmethod
    def parse_participants(cls, v):
        """Parse participants from string or list."""
        if isinstance(v, str):
            # Split on commas, semicolons, "and", or "with"
            participants = re.split(r"[,;]|\sand\s|\swith\s", v.strip())
            return [p.strip() for p in participants if p.strip()]
        elif isinstance(v, list):
            return [str(p).strip() for p in v if str(p).strip()]
        return v or []

    @model_validator(mode="after")
    def validate_datetime_range(self):
        """Ensure end_datetime is after start_datetime."""
        if (
            self.start_datetime
            and self.end_datetime
            and self.end_datetime <= self.start_datetime
        ):
            # If end is before start, assume duration and add 1 hour
            self.end_datetime = self.start_datetime.replace(
                hour=self.start_datetime.hour + 1
            )

        return self


class Reminder(BaseEntity):
    """
    Reminder entity with trigger datetime and categories.
    """

    entity_type: Literal[EntityType.REMINDER] = EntityType.REMINDER
    trigger_datetime: datetime = Field(description="When to trigger the reminder")
    category: Optional[str] = Field(None, description="Reminder category")
    recurring: bool = Field(default=False, description="Whether this reminder repeats")

    @field_validator("trigger_datetime", mode="before")
    @classmethod
    def parse_trigger_datetime(cls, v):
        """Parse trigger datetime from various formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return date_parser.parse(v, fuzzy=True)
            except (ValueError, TypeError):
                raise ValueError(f"Could not parse datetime: {v}")
        raise ValueError("trigger_datetime is required")


class Memory(BaseEntity):
    """
    Memory entity for storing general information and notes.
    """

    entity_type: Literal[EntityType.MEMORY] = EntityType.MEMORY
    category: Optional[str] = Field(None, description="Memory category or topic")
    tags: List[str] = Field(default_factory=list, description="Memory tags")

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """Parse tags from string or list."""
        if isinstance(v, str):
            tags = re.split(r"[,;\s]+", v.strip())
            return [tag.strip() for tag in tags if tag.strip()]
        elif isinstance(v, list):
            return [str(tag).strip() for tag in v if str(tag).strip()]
        return v or []


class ListItem(BaseEntity):
    """
    List item entity for managing categorized lists of items.
    """

    entity_type: Literal[EntityType.LIST_ITEM] = EntityType.LIST_ITEM
    list_name: str = Field(description="Name of the list this item belongs to")
    category: Optional[str] = Field(None, description="Item category or classification")
    tags: List[str] = Field(default_factory=list, description="Item tags")

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """Parse tags from string or list."""
        if isinstance(v, str):
            tags = re.split(r"[,;\s]+", v.strip())
            return [tag.strip() for tag in tags if tag.strip()]
        elif isinstance(v, list):
            return [str(tag).strip() for tag in v if str(tag).strip()]
        return v or []


class TimelogEntry(BaseEntity):
    """
    Timelog entry for tracking time spent on projects.
    """

    entity_type: Literal[EntityType.TIMELOG] = EntityType.TIMELOG
    day: date = Field(description="Date when time was logged")
    project: str = Field(description="Project name or identifier")
    hours: float = Field(description="Number of hours worked", gt=0, le=24)
    notes: Optional[str] = Field(None, description="Optional notes about the work")

    @field_validator("day", mode="before")
    @classmethod
    def parse_day(cls, v):
        """Parse day from various string formats."""
        if v is None:
            return date.today()

        if isinstance(v, date):
            return v

        if isinstance(v, datetime):
            return v.date()

        if isinstance(v, str):
            try:
                v_lower = v.lower().strip()
                if v_lower in ["today"]:
                    return date.today()
                elif v_lower in ["yesterday"]:
                    from datetime import timedelta

                    return date.today() - timedelta(days=1)
                else:
                    # Use dateutil parser to handle various date formats
                    parsed_date = date_parser.parse(v, fuzzy=True)
                    return parsed_date.date()
            except (ValueError, TypeError):
                return date.today()

        return v

    @field_validator("hours", mode="before")
    @classmethod
    def parse_hours(cls, v):
        """Parse hours from various formats including aliases."""
        if isinstance(v, (int, float)):
            return float(v)

        if isinstance(v, str):
            v_lower = v.lower().strip()

            # Handle aliases
            if v_lower in [
                "full day",
                "full-day",
                "fullday",
                "all day",
                "all-day",
                "allday",
            ]:
                return 8.0
            elif v_lower in ["half day", "half-day", "halfday", "half"]:
                return 4.0
            elif v_lower in ["quarter day", "quarter-day", "quarterday", "quarter"]:
                return 2.0

            # Try to parse as number (with optional units)
            try:
                # Handle common hour formats: "2h", "4hrs", "3.5hours", "2 hours", etc.
                import re

                # Remove common hour suffixes and extract number
                v_clean = re.sub(r"\s*(h|hr|hrs|hour|hours)\s*$", "", v_lower)
                return float(v_clean)
            except ValueError:
                raise ValueError(f"Could not parse hours: {v}")

        raise ValueError("Hours is required")


# Union type for all entity types
ProductivityEntity = Task | Event | Reminder | Memory | ListItem | TimelogEntry


def create_entity(entity_type: EntityType, **kwargs) -> ProductivityEntity:
    """
    Factory function to create the appropriate entity type.

    Parameters
    ----------
    entity_type : EntityType
        The type of entity to create
    **kwargs
        Fields for the entity

    Returns
    -------
    ProductivityEntity
        The created entity instance
    """
    entity_classes = {
        EntityType.TASK: Task,
        EntityType.EVENT: Event,
        EntityType.REMINDER: Reminder,
        EntityType.MEMORY: Memory,
        EntityType.LIST_ITEM: ListItem,
        EntityType.TIMELOG: TimelogEntry,
    }

    entity_class = entity_classes.get(entity_type)
    if not entity_class:
        raise ValueError(f"Unknown entity type: {entity_type}")

    return entity_class(**kwargs)
