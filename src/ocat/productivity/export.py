"""
Export functionality for productivity data.

Provides generic export capabilities for tasks, timelog entries, and other
productivity entities to various formats (CSV, JSON, YAML).
"""

import json
import yaml
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date

from .models import (
    ProductivityEntity,
    TimelogEntry,
    Task,
    Event,
    Reminder,
    Memory,
    ListItem,
)


def entities_to_dataframe(entities: List[ProductivityEntity]) -> pd.DataFrame:
    """
    Convert a list of productivity entities to a pandas DataFrame.

    Parameters
    ----------
    entities : List[ProductivityEntity]
        List of productivity entities to convert

    Returns
    -------
    pd.DataFrame
        DataFrame with entity data
    """
    data = []

    for entity in entities:
        # Base entity data
        row = {
            "pseudo_id": entity.pseudo_id,
            "entity_type": entity.entity_type.value,
            "content": entity.content,
            "status": entity.status.value if entity.status else None,
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        }

        # Add entity-specific fields
        if isinstance(entity, TimelogEntry):
            row.update(
                {
                    "day": entity.day.isoformat() if entity.day else None,
                    "project": entity.project,
                    "hours": entity.hours,
                    "notes": entity.notes,
                }
            )
        elif isinstance(entity, Task):
            row.update(
                {
                    "due_date": (
                        entity.due_date.isoformat() if entity.due_date else None
                    ),
                    "category": entity.category,
                    "priority": entity.priority,
                    "tags": ",".join(entity.tags) if entity.tags else "",
                }
            )
        elif isinstance(entity, Event):
            row.update(
                {
                    "start_datetime": (
                        entity.start_datetime.isoformat()
                        if entity.start_datetime
                        else None
                    ),
                    "end_datetime": (
                        entity.end_datetime.isoformat() if entity.end_datetime else None
                    ),
                    "all_day": entity.all_day,
                    "participants": (
                        ",".join(entity.participants) if entity.participants else ""
                    ),
                    "location": entity.location,
                }
            )
        elif isinstance(entity, Reminder):
            row.update(
                {
                    "trigger_datetime": (
                        entity.trigger_datetime.isoformat()
                        if entity.trigger_datetime
                        else None
                    ),
                    "category": entity.category,
                    "recurring": entity.recurring,
                }
            )
        elif isinstance(entity, Memory):
            row.update(
                {
                    "category": entity.category,
                    "tags": ",".join(entity.tags) if entity.tags else "",
                }
            )
        elif isinstance(entity, ListItem):
            row.update(
                {
                    "list_name": entity.list_name,
                    "category": entity.category,
                    "tags": ",".join(entity.tags) if entity.tags else "",
                }
            )

        data.append(row)

    return pd.DataFrame(data)


def export_entities(
    entities: List[ProductivityEntity],
    output_file: Union[str, Path],
    format: str = "csv",
    include_metadata: bool = True,
) -> bool:
    """
    Export productivity entities to a file in the specified format.

    Parameters
    ----------
    entities : List[ProductivityEntity]
        List of entities to export
    output_file : Union[str, Path]
        Output file path
    format : str
        Export format: 'csv', 'json', or 'yaml'
    include_metadata : bool
        Whether to include metadata fields (created_at, updated_at, etc.)

    Returns
    -------
    bool
        True if export was successful, False otherwise
    """
    try:
        file_path = Path(output_file)
        df = entities_to_dataframe(entities)

        if df.empty:
            return False

        # Remove metadata fields if requested
        if not include_metadata:
            metadata_columns = ["created_at", "updated_at", "pseudo_id"]
            df = df.drop(columns=[col for col in metadata_columns if col in df.columns])

        if format.lower() == "csv":
            df.to_csv(file_path, index=False)
        elif format.lower() == "json":
            # Convert DataFrame to dict and then to JSON for better control
            data = df.to_dict("records")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        elif format.lower() == "yaml":
            # Convert DataFrame to dict and then to YAML
            data = df.to_dict("records")
            with open(file_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return True

    except Exception as e:
        print(f"Export failed: {e}")
        return False


def export_timelog_summary(
    timelog_entries: List[TimelogEntry],
    output_file: Union[str, Path],
    format: str = "csv",
    group_by: Optional[str] = None,
) -> bool:
    """
    Export a summary of timelog entries grouped by project, week, or month.

    Parameters
    ----------
    timelog_entries : List[TimelogEntry]
        List of timelog entries to summarize
    output_file : Union[str, Path]
        Output file path
    format : str
        Export format: 'csv', 'json', or 'yaml'
    group_by : Optional[str]
        Grouping option: 'project', 'week', 'month', or None for detailed export

    Returns
    -------
    bool
        True if export was successful, False otherwise
    """
    try:
        if not timelog_entries:
            return False

        df = entities_to_dataframe(timelog_entries)
        df["day"] = pd.to_datetime(df["day"])

        if group_by == "project":
            summary_df = (
                df.groupby("project")
                .agg({"hours": "sum", "day": ["min", "max"], "pseudo_id": "count"})
                .round(2)
            )
            summary_df.columns = [
                "total_hours",
                "first_entry",
                "last_entry",
                "entry_count",
            ]
            summary_df = summary_df.reset_index()

        elif group_by == "week":
            df["week"] = df["day"].dt.to_period("W").astype(str)
            summary_df = df.groupby(["week", "project"])["hours"].sum().reset_index()
            summary_df = summary_df.pivot(
                index="week", columns="project", values="hours"
            ).fillna(0)
            summary_df["total_hours"] = summary_df.sum(axis=1)
            summary_df = summary_df.reset_index()

        elif group_by == "month":
            df["month"] = df["day"].dt.to_period("M").astype(str)
            summary_df = df.groupby(["month", "project"])["hours"].sum().reset_index()
            summary_df = summary_df.pivot(
                index="month", columns="project", values="hours"
            ).fillna(0)
            summary_df["total_hours"] = summary_df.sum(axis=1)
            summary_df = summary_df.reset_index()

        else:
            # No grouping, just format the data nicely
            summary_df = df[["day", "project", "hours", "notes"]].copy()
            summary_df["day"] = summary_df["day"].dt.strftime("%Y-%m-%d")

        file_path = Path(output_file)

        if format.lower() == "csv":
            summary_df.to_csv(file_path, index=False)
        elif format.lower() == "json":
            summary_df.to_json(file_path, orient="records", indent=2)
        elif format.lower() == "yaml":
            with open(file_path, "w") as f:
                yaml.dump(summary_df.to_dict("records"), f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return True

    except Exception as e:
        print(f"Export failed: {e}")
        return False


def get_export_filename(
    entity_type: str,
    project: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = "csv",
) -> str:
    """
    Generate a suggested filename for export based on parameters.

    Parameters
    ----------
    entity_type : str
        Type of entity being exported (timelog, tasks, etc.)
    project : Optional[str]
        Project name filter
    start_date : Optional[date]
        Start date filter
    end_date : Optional[date]
        End date filter
    format : str
        Export format

    Returns
    -------
    str
        Suggested filename
    """
    parts = [entity_type]

    if project:
        parts.append(project.replace(" ", "_").lower())

    if start_date and end_date:
        parts.append(f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}")
    elif start_date:
        parts.append(f"from_{start_date.strftime('%Y%m%d')}")
    elif end_date:
        parts.append(f"until_{end_date.strftime('%Y%m%d')}")
    else:
        parts.append(datetime.now().strftime("%Y%m%d"))

    return f"{'_'.join(parts)}.{format}"
