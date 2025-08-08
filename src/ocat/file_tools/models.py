"""
Pydantic models for file operation tool requests.
"""

from typing import Optional
from pydantic import BaseModel, Field


class FileReadRequest(BaseModel):
    """Request model for reading a file."""

    path: str = Field(
        description="File path to read (supports location aliases like 'docs:readme.md')"
    )
    show_line_numbers: bool = Field(
        default=False, description="Whether to include line numbers in the output"
    )


class FileWriteRequest(BaseModel):
    """Request model for writing to a file."""

    path: str = Field(description="File path to write to (supports location aliases)")
    content: str = Field(description="Content to write to the file")
    mode: str = Field(
        default="write",
        description="Write mode: 'write' (overwrite) or 'append' (add to end)",
    )


class FileListRequest(BaseModel):
    """Request model for listing directory contents."""

    path: Optional[str] = Field(
        default=None,
        description="Directory path to list (defaults to current directory, supports location aliases)",
    )
    show_hidden: bool = Field(
        default=False, description="Whether to show hidden files and directories"
    )


class FileSearchRequest(BaseModel):
    """Request model for searching files."""

    pattern: str = Field(
        description="Search pattern (filename pattern or text content)"
    )
    path: Optional[str] = Field(
        default=None,
        description="Directory to search in (defaults to current directory, supports location aliases)",
    )
    search_content: bool = Field(
        default=False,
        description="Whether to search file contents (True) or just filenames (False)",
    )


class FileTreeRequest(BaseModel):
    """Request model for showing directory tree."""

    path: Optional[str] = Field(
        default=None,
        description="Directory path for tree view (defaults to current directory, supports location aliases)",
    )
    max_depth: int = Field(
        default=3, description="Maximum depth to show in tree (1-10)"
    )
