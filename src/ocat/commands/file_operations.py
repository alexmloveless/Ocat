"""
File operations command system for Ocat.

Implements the /file command with subcommands for comprehensive file management.
"""

import os
import fnmatch
import subprocess
from typing import List, Any, Optional
from pathlib import Path

from . import command, BaseCommand, CommandResult
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from ..utils.path_utils import resolve_path_with_aliases


class FileSubcommand:
    """Base class for file subcommands."""

    def __init__(self, name: str, description: str, usage: str):
        self.name = name
        self.description = description
        self.usage = usage

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        """Execute the subcommand."""
        raise NotImplementedError


class ReadSubcommand(FileSubcommand):
    """Read and display file contents."""

    def __init__(self):
        super().__init__("read", "Read and display file contents", "/file read <path>")

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        if not args:
            return CommandResult.error(
                "No file path specified. Usage: /file read <path>"
            )

        try:
            file_path = resolve_path_with_aliases(args[0], context.config.locations)

            # Handle working directory if path is relative
            if not file_path.is_absolute() and hasattr(context, "current_directory"):
                file_path = context.current_directory / file_path

            if not file_path.exists():
                return CommandResult.error(f"File not found: {args[0]}")

            if not file_path.is_file():
                return CommandResult.error(f"Not a file: {args[0]}")

            # Try to read as text
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Determine syntax highlighting based on file extension
                suffix = file_path.suffix.lower()
                lexer_map = {
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".html": "html",
                    ".css": "css",
                    ".json": "json",
                    ".yaml": "yaml",
                    ".yml": "yaml",
                    ".xml": "xml",
                    ".sql": "sql",
                    ".sh": "bash",
                    ".md": "markdown",
                    ".rs": "rust",
                    ".go": "go",
                    ".java": "java",
                    ".cpp": "cpp",
                    ".c": "c",
                    ".php": "php",
                }

                syntax_type = lexer_map.get(suffix, "text")

                # Display with syntax highlighting
                syntax = Syntax(
                    content, syntax_type, theme="monokai", line_numbers=True
                )

                context.console.print(
                    Panel(syntax, title=f"📄 {file_path.name}", border_style="blue")
                )

                return CommandResult.ok(f"File read successfully: {file_path}")

            except UnicodeDecodeError:
                return CommandResult.error(
                    f"Cannot read file as text (binary file?): {args[0]}"
                )
            except PermissionError:
                return CommandResult.error(f"Permission denied: {args[0]}")

        except ValueError as e:
            return CommandResult.error(str(e))
        except Exception as e:
            return CommandResult.error(f"Error reading file: {e}")


class WriteSubcommand(FileSubcommand):
    """Write content to a file."""

    def __init__(self):
        super().__init__(
            "write", "Write content to a file", "/file write <path> <content>"
        )

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        if len(args) < 2:
            return CommandResult.error("Usage: /file write <path> <content>")

        try:
            file_path = resolve_path_with_aliases(args[0], context.config.locations)

            # Handle working directory if path is relative
            if not file_path.is_absolute() and hasattr(context, "current_directory"):
                file_path = context.current_directory / file_path

            # Join remaining args as content
            content = " ".join(args[1:])

            # Strip surrounding quotes if present
            if (content.startswith('"') and content.endswith('"')) or (
                content.startswith("'") and content.endswith("'")
            ):
                content = content[1:-1]

            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            context.console.print(f"✅ Content written to: {file_path}", style="green")
            return CommandResult.ok(f"Content written to {file_path}")

        except ValueError as e:
            return CommandResult.error(str(e))
        except PermissionError:
            return CommandResult.error(f"Permission denied: {args[0]}")
        except Exception as e:
            return CommandResult.error(f"Error writing file: {e}")


class AppendSubcommand(FileSubcommand):
    """Append content to a file."""

    def __init__(self):
        super().__init__(
            "append", "Append content to a file", "/file append <path> <content>"
        )

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        if len(args) < 2:
            return CommandResult.error("Usage: /file append <path> <content>")

        try:
            file_path = resolve_path_with_aliases(args[0], context.config.locations)

            # Handle working directory if path is relative
            if not file_path.is_absolute() and hasattr(context, "current_directory"):
                file_path = context.current_directory / file_path

            # Join remaining args as content
            content = " ".join(args[1:])

            # Strip surrounding quotes if present
            if (content.startswith('"') and content.endswith('"')) or (
                content.startswith("'") and content.endswith("'")
            ):
                content = content[1:-1]

            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

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

            context.console.print(f"✅ Content appended to: {file_path}", style="green")
            return CommandResult.ok(f"Content appended to {file_path}")

        except ValueError as e:
            return CommandResult.error(str(e))
        except PermissionError:
            return CommandResult.error(f"Permission denied: {args[0]}")
        except Exception as e:
            return CommandResult.error(f"Error appending to file: {e}")


class ListSubcommand(FileSubcommand):
    """List directory contents."""

    def __init__(self):
        super().__init__("list", "List directory contents", "/file list [path]")

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        try:
            # Use provided path or current directory
            if args:
                dir_path = resolve_path_with_aliases(args[0], context.config.locations)
            else:
                dir_path = getattr(context, "current_directory", Path.cwd())

            # Handle working directory if path is relative
            if not dir_path.is_absolute() and hasattr(context, "current_directory"):
                dir_path = context.current_directory / dir_path

            if not dir_path.exists():
                return CommandResult.error(
                    f"Directory not found: {args[0] if args else 'current directory'}"
                )

            if not dir_path.is_dir():
                return CommandResult.error(
                    f"Not a directory: {args[0] if args else 'current directory'}"
                )

            # Create table for directory listing
            table = Table(title=f"📁 Directory: {dir_path}")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Type", style="magenta")
            table.add_column("Size", style="green", justify="right")
            table.add_column("Modified", style="yellow")

            # Get directory contents
            items = []
            try:
                for item in dir_path.iterdir():
                    if item.is_dir():
                        items.append(
                            (item.name + "/", "DIR", "-", self._format_mtime(item))
                        )
                    else:
                        size = self._format_size(item.stat().st_size)
                        items.append(
                            (item.name, "FILE", size, self._format_mtime(item))
                        )
            except PermissionError:
                return CommandResult.error(f"Permission denied: {dir_path}")

            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (x[1] != "DIR", x[0].lower()))

            # Add items to table
            for name, type_str, size, mtime in items:
                table.add_row(name, type_str, size, mtime)

            context.console.print(table)
            return CommandResult.ok(f"Listed {len(items)} items in {dir_path}")

        except ValueError as e:
            return CommandResult.error(str(e))
        except Exception as e:
            return CommandResult.error(f"Error listing directory: {e}")

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"

    def _format_mtime(self, path: Path) -> str:
        """Format modification time."""
        import datetime

        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
        return mtime.strftime("%Y-%m-%d %H:%M")


class SearchSubcommand(FileSubcommand):
    """Search for files or content."""

    def __init__(self):
        super().__init__(
            "search", "Search for files or content", "/file search <pattern> [path]"
        )

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        if not args:
            return CommandResult.error("Usage: /file search <pattern> [path]")

        pattern = args[0]

        try:
            # Use provided path or current directory
            if len(args) > 1:
                search_path = resolve_path_with_aliases(
                    args[1], context.config.locations
                )
            else:
                search_path = getattr(context, "current_directory", Path.cwd())

            # Handle working directory if path is relative
            if not search_path.is_absolute() and hasattr(context, "current_directory"):
                search_path = context.current_directory / search_path

            if not search_path.exists():
                return CommandResult.error(
                    f"Search path not found: {args[1] if len(args) > 1 else 'current directory'}"
                )

            results = []

            # Search for files by name pattern
            if search_path.is_dir():
                for item in search_path.rglob("*"):
                    if fnmatch.fnmatch(item.name.lower(), pattern.lower()):
                        relative_path = item.relative_to(search_path)
                        results.append((str(relative_path), "name", item.is_file()))

            # Search for content in text files (if pattern doesn't look like a file pattern)
            if not any(char in pattern for char in ["*", "?", "[", "]"]):
                try:
                    for item in search_path.rglob("*.txt"):
                        if item.is_file():
                            try:
                                with open(item, "r", encoding="utf-8") as f:
                                    content = f.read()
                                    if pattern.lower() in content.lower():
                                        relative_path = item.relative_to(search_path)
                                        results.append(
                                            (str(relative_path), "content", True)
                                        )
                            except (UnicodeDecodeError, PermissionError):
                                continue
                except Exception:
                    pass  # Continue with filename search only

            # Display results
            if not results:
                context.console.print(
                    f"No results found for pattern: {pattern}", style="yellow"
                )
                return CommandResult.ok("Search completed - no results found")

            table = Table(title=f"🔍 Search Results for: {pattern}")
            table.add_column("Path", style="cyan")
            table.add_column("Match Type", style="magenta")
            table.add_column("Type", style="green")

            for path, match_type, is_file in results:
                file_type = "FILE" if is_file else "DIR"
                table.add_row(path, match_type, file_type)

            context.console.print(table)
            return CommandResult.ok(f"Found {len(results)} result(s)")

        except ValueError as e:
            return CommandResult.error(str(e))
        except Exception as e:
            return CommandResult.error(f"Error during search: {e}")


class TreeSubcommand(FileSubcommand):
    """Show directory tree structure."""

    def __init__(self):
        super().__init__(
            "tree", "Show directory tree structure", "/file tree [path] [depth]"
        )

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        try:
            # Parse arguments
            if args:
                dir_path = resolve_path_with_aliases(args[0], context.config.locations)
            else:
                dir_path = getattr(context, "current_directory", Path.cwd())

            max_depth = 3  # Default depth
            if len(args) > 1:
                try:
                    max_depth = int(args[1])
                    if max_depth < 1:
                        max_depth = 1
                except ValueError:
                    return CommandResult.error("Depth must be a positive integer")

            # Handle working directory if path is relative
            if not dir_path.is_absolute() and hasattr(context, "current_directory"):
                dir_path = context.current_directory / dir_path

            if not dir_path.exists():
                return CommandResult.error(
                    f"Directory not found: {args[0] if args else 'current directory'}"
                )

            if not dir_path.is_dir():
                return CommandResult.error(
                    f"Not a directory: {args[0] if args else 'current directory'}"
                )

            # Create tree structure
            tree = Tree(f"📁 {dir_path.name if dir_path.name else str(dir_path)}")
            self._build_tree(tree, dir_path, max_depth, 0)

            context.console.print(tree)
            return CommandResult.ok(f"Tree view of {dir_path} (depth: {max_depth})")

        except ValueError as e:
            return CommandResult.error(str(e))
        except Exception as e:
            return CommandResult.error(f"Error building tree: {e}")

    def _build_tree(self, tree_node, path: Path, max_depth: int, current_depth: int):
        """Recursively build tree structure."""
        if current_depth >= max_depth:
            return

        try:
            items = list(path.iterdir())
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))

            for item in items:
                if item.name.startswith("."):
                    continue  # Skip hidden files

                if item.is_dir():
                    branch = tree_node.add(f"📁 {item.name}")
                    self._build_tree(branch, item, max_depth, current_depth + 1)
                else:
                    # Add file with appropriate icon
                    icon = self._get_file_icon(item.suffix)
                    tree_node.add(f"{icon} {item.name}")
        except PermissionError:
            tree_node.add("❌ [Permission Denied]")

    def _get_file_icon(self, suffix: str) -> str:
        """Get emoji icon for file type."""
        icon_map = {
            ".py": "🐍",
            ".js": "📄",
            ".ts": "📄",
            ".html": "🌐",
            ".css": "🎨",
            ".json": "📋",
            ".yaml": "⚙️",
            ".yml": "⚙️",
            ".md": "📝",
            ".txt": "📄",
            ".pdf": "📕",
            ".png": "🖼️",
            ".jpg": "🖼️",
            ".jpeg": "🖼️",
            ".gif": "🖼️",
            ".svg": "🖼️",
            ".mp4": "🎬",
            ".mp3": "🎵",
            ".zip": "📦",
            ".tar": "📦",
            ".gz": "📦",
            ".sql": "🗃️",
            ".log": "📊",
        }
        return icon_map.get(suffix.lower(), "📄")


@command(
    name="file",
    description="File operations (read, write, append, list, search, tree)",
    usage="/file <subcommand> [args...]",
)
class FileCommand(BaseCommand):
    """Main file operations command with subcommands."""

    def __init__(self, name: str = "", description: str = "", usage: str = ""):
        super().__init__(name, description, usage)
        self.subcommands = {
            "read": ReadSubcommand(),
            "write": WriteSubcommand(),
            "append": AppendSubcommand(),
            "list": ListSubcommand(),
            "search": SearchSubcommand(),
            "tree": TreeSubcommand(),
        }

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        if not args:
            return self._show_help(context)

        subcommand_name = args[0].lower()

        if subcommand_name in self.subcommands:
            subcommand = self.subcommands[subcommand_name]
            return await subcommand.execute(args[1:], context)
        else:
            return CommandResult.error(
                f"Unknown subcommand: {subcommand_name}. "
                f"Available: {', '.join(self.subcommands.keys())}"
            )

    def _show_help(self, context: Any) -> CommandResult:
        """Show help for file command."""
        table = Table(title="📁 File Operations")
        table.add_column("Subcommand", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Usage", style="green")

        for name, subcmd in self.subcommands.items():
            table.add_row(name, subcmd.description, subcmd.usage)

        context.console.print(table)
        return CommandResult.ok("File command help displayed.")


# Working directory management
@command(
    name="pwd",
    description="Show current working directory",
    usage="/pwd",
)
class PwdCommand(BaseCommand):
    """Show current working directory."""

    def __init__(self, name: str = "", description: str = "", usage: str = ""):
        super().__init__(name, description, usage)

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        current_dir = getattr(context, "current_directory", Path.cwd())
        context.console.print(f"📁 Current directory: {current_dir}", style="cyan")
        return CommandResult.ok(f"Current directory: {current_dir}")


@command(
    name="cd",
    description="Change current working directory",
    usage="/cd <path>",
)
class CdCommand(BaseCommand):
    """Change current working directory."""

    def __init__(self, name: str = "", description: str = "", usage: str = ""):
        super().__init__(name, description, usage)

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        if not args:
            # Change to home directory
            new_dir = Path.home()
        else:
            try:
                new_dir = resolve_path_with_aliases(args[0], context.config.locations)

                # Handle working directory if path is relative
                if not new_dir.is_absolute() and hasattr(context, "current_directory"):
                    new_dir = context.current_directory / new_dir

            except ValueError as e:
                return CommandResult.error(str(e))

        # Resolve to absolute path
        new_dir = new_dir.resolve()

        if not new_dir.exists():
            return CommandResult.error(
                f"Directory not found: {args[0] if args else 'home'}"
            )

        if not new_dir.is_dir():
            return CommandResult.error(
                f"Not a directory: {args[0] if args else 'home'}"
            )

        # Set current directory on context
        context.current_directory = new_dir

        context.console.print(f"📁 Changed to: {new_dir}", style="green")
        return CommandResult.ok(f"Changed directory to {new_dir}")


# Filesystem aliases
@command(
    name="ls",
    description="List directory contents",
    usage="/ls [path]",
    aliases=["dir"],
)
class LsCommand(BaseCommand):
    """Alias for /file list."""

    def __init__(self, name: str = "", description: str = "", usage: str = ""):
        super().__init__(name, description, usage)

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        list_cmd = ListSubcommand()
        return await list_cmd.execute(args, context)


@command(name="cat", description="Display file contents", usage="/cat <path>")
class CatCommand(BaseCommand):
    """Alias for /file read."""

    def __init__(self, name: str = "", description: str = "", usage: str = ""):
        super().__init__(name, description, usage)

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        read_cmd = ReadSubcommand()
        return await read_cmd.execute(args, context)


@command(name="mkdir", description="Create directory", usage="/mkdir <path>")
class MkdirCommand(BaseCommand):
    """Create directory."""

    def __init__(self, name: str = "", description: str = "", usage: str = ""):
        super().__init__(name, description, usage)

    async def execute(self, args: List[str], context: Any) -> CommandResult:
        if not args:
            return CommandResult.error(
                "No directory path specified. Usage: /mkdir <path>"
            )

        try:
            dir_path = resolve_path_with_aliases(args[0], context.config.locations)

            # Handle working directory if path is relative
            if not dir_path.is_absolute() and hasattr(context, "current_directory"):
                dir_path = context.current_directory / dir_path

            dir_path.mkdir(parents=True, exist_ok=True)

            context.console.print(f"✅ Directory created: {dir_path}", style="green")
            return CommandResult.ok(f"Directory created: {dir_path}")

        except ValueError as e:
            return CommandResult.error(str(e))
        except PermissionError:
            return CommandResult.error(f"Permission denied: {args[0]}")
        except Exception as e:
            return CommandResult.error(f"Error creating directory: {e}")
