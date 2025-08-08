"""
File operation storage context for Pydantic-AI tools.

Provides access to file system operations with proper path resolution
and location alias support.
"""

import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ..utils.path_utils import resolve_path_with_aliases


@dataclass
class FileOperationContext:
    """Context for file operations containing configuration and current state."""

    locations: Dict[str, str]  # Location aliases from config
    current_directory: Path  # Current working directory
    max_file_size: int = 1024 * 1024  # 1MB default max file size for reading


class FileStorage:
    """Storage interface for file operations with location alias support."""

    def __init__(self, context: FileOperationContext):
        self.context = context

    def resolve_path(self, path_str: str) -> Path:
        """
        Resolve a path string with location aliases and current directory.

        Parameters
        ----------
        path_str : str
            Path string that may contain location aliases

        Returns
        -------
        Path
            Resolved pathlib.Path object
        """
        try:
            resolved_path = resolve_path_with_aliases(path_str, self.context.locations)

            # Handle relative paths from current directory
            if not resolved_path.is_absolute():
                resolved_path = self.context.current_directory / resolved_path

            return resolved_path.resolve()

        except ValueError as e:
            raise ValueError(f"Path resolution error: {e}")

    def read_file(self, path_str: str, show_line_numbers: bool = False) -> str:
        """
        Read file contents safely with size limits.

        Parameters
        ----------
        path_str : str
            Path to the file to read
        show_line_numbers : bool
            Whether to include line numbers

        Returns
        -------
        str
            File contents

        Raises
        ------
        ValueError
            If file doesn't exist, is too large, or can't be read
        """
        file_path = self.resolve_path(path_str)

        if not file_path.exists():
            raise ValueError(f"File not found: {path_str}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {path_str}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.context.max_file_size:
            raise ValueError(
                f"File too large ({file_size:,} bytes). "
                f"Maximum allowed: {self.context.max_file_size:,} bytes"
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if show_line_numbers:
                lines = content.split("\n")
                numbered_lines = [f"{i+1:4d}: {line}" for i, line in enumerate(lines)]
                content = "\n".join(numbered_lines)

            return content

        except UnicodeDecodeError:
            raise ValueError(f"File is not valid UTF-8 text: {path_str}")
        except PermissionError:
            raise ValueError(f"Permission denied reading file: {path_str}")

    def write_file(self, path_str: str, content: str, mode: str = "write") -> str:
        """
        Write content to a file.

        Parameters
        ----------
        path_str : str
            Path to write to
        content : str
            Content to write
        mode : str
            Write mode: 'write' or 'append'

        Returns
        -------
        str
            Success message
        """
        file_path = self.resolve_path(path_str)

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if mode == "append":
                # Check if file exists and needs newline
                needs_newline = False
                if file_path.exists() and file_path.stat().st_size > 0:
                    with open(file_path, "rb") as f:
                        f.seek(-1, 2)  # Go to last byte
                        last_byte = f.read(1)
                        if last_byte != b"\n":
                            needs_newline = True

                with open(file_path, "a", encoding="utf-8") as f:
                    if needs_newline:
                        f.write("\n")
                    f.write(content)
                    if not content.endswith("\n"):
                        f.write("\n")

                return f"Content appended to {file_path}"
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return f"Content written to {file_path}"

        except PermissionError:
            raise ValueError(f"Permission denied writing to: {path_str}")

    def list_directory(
        self, path_str: Optional[str] = None, show_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List directory contents.

        Parameters
        ----------
        path_str : Optional[str]
            Directory path (defaults to current directory)
        show_hidden : bool
            Whether to show hidden files

        Returns
        -------
        List[Dict[str, Any]]
            List of file/directory information
        """
        if path_str:
            dir_path = self.resolve_path(path_str)
        else:
            dir_path = self.context.current_directory

        if not dir_path.exists():
            raise ValueError(f"Directory not found: {path_str or 'current directory'}")

        if not dir_path.is_dir():
            raise ValueError(
                f"Path is not a directory: {path_str or 'current directory'}"
            )

        try:
            items = []
            for item in dir_path.iterdir():
                if not show_hidden and item.name.startswith("."):
                    continue

                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "path": str(item.relative_to(dir_path)),
                }

                if item.is_file():
                    item_info["size"] = item.stat().st_size

                items.append(item_info)

            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            return items

        except PermissionError:
            raise ValueError(
                f"Permission denied listing directory: {path_str or 'current directory'}"
            )

    def search_files(
        self, pattern: str, path_str: Optional[str] = None, search_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for files by name or content.

        Parameters
        ----------
        pattern : str
            Search pattern
        path_str : Optional[str]
            Directory to search in
        search_content : bool
            Whether to search file contents

        Returns
        -------
        List[Dict[str, Any]]
            List of search results
        """
        if path_str:
            search_path = self.resolve_path(path_str)
        else:
            search_path = self.context.current_directory

        if not search_path.exists():
            raise ValueError(
                f"Search path not found: {path_str or 'current directory'}"
            )

        results = []

        try:
            # Search by filename
            for item in search_path.rglob("*"):
                if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
                    relative_path = item.relative_to(search_path)
                    results.append(
                        {
                            "path": str(relative_path),
                            "type": "directory" if item.is_dir() else "file",
                            "match_type": "filename",
                        }
                    )

            # Search file contents if requested
            if search_content and not any(
                char in pattern for char in ["*", "?", "[", "]"]
            ):
                for item in search_path.rglob("*.txt"):
                    if (
                        item.is_file()
                        and item.stat().st_size <= self.context.max_file_size
                    ):
                        try:
                            with open(item, "r", encoding="utf-8") as f:
                                content = f.read()
                                if pattern.lower() in content.lower():
                                    relative_path = item.relative_to(search_path)
                                    # Check if we already found this file by name
                                    if not any(
                                        r["path"] == str(relative_path) for r in results
                                    ):
                                        results.append(
                                            {
                                                "path": str(relative_path),
                                                "type": "file",
                                                "match_type": "content",
                                            }
                                        )
                        except (UnicodeDecodeError, PermissionError):
                            continue

            return results

        except Exception as e:
            raise ValueError(f"Search error: {e}")

    def get_directory_tree(
        self, path_str: Optional[str] = None, max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get directory tree structure.

        Parameters
        ----------
        path_str : Optional[str]
            Directory path
        max_depth : int
            Maximum depth to traverse

        Returns
        -------
        Dict[str, Any]
            Tree structure
        """
        if path_str:
            dir_path = self.resolve_path(path_str)
        else:
            dir_path = self.context.current_directory

        if not dir_path.exists():
            raise ValueError(f"Directory not found: {path_str or 'current directory'}")

        if not dir_path.is_dir():
            raise ValueError(
                f"Path is not a directory: {path_str or 'current directory'}"
            )

        def build_tree(path: Path, current_depth: int) -> Dict[str, Any]:
            """Recursively build tree structure."""
            tree = {"name": path.name or str(path), "type": "directory", "children": []}

            if current_depth >= max_depth:
                return tree

            try:
                items = list(path.iterdir())
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))

                for item in items:
                    if item.name.startswith("."):
                        continue

                    if item.is_dir():
                        tree["children"].append(build_tree(item, current_depth + 1))
                    else:
                        tree["children"].append(
                            {
                                "name": item.name,
                                "type": "file",
                                "size": item.stat().st_size,
                            }
                        )

            except PermissionError:
                tree["children"].append(
                    {"name": "[Permission Denied]", "type": "error"}
                )

            return tree

        return build_tree(dir_path, 0)
