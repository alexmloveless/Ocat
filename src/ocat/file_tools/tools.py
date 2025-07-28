"""
Pydantic-AI tool functions for file operations.

Provides natural language interface for reading, writing, and exploring files.
"""

import json
from typing import Optional
from pydantic_ai import Agent, RunContext, ModelRetry

from .storage import FileStorage, FileOperationContext
from .models import (
    FileReadRequest,
    FileWriteRequest, 
    FileListRequest,
    FileSearchRequest,
    FileTreeRequest
)


# Create file operations agent
file_agent: Agent[FileStorage, str] = Agent(
    "openai:gpt-4o-mini",  # Use cost-effective model for file operations
    deps_type=FileStorage,
    system_prompt="""You are a file system assistant that helps users read, write, and explore files and directories.

You have access to tools for:
- Reading file contents (with optional line numbers)
- Writing and appending to files
- Listing directory contents
- Searching for files by name or content
- Showing directory tree structures

When users ask to:
- "read", "show", "display", or "open" files → use file_read_tool
- "write", "save", or "create" files → use file_write_tool  
- "list", "show contents", or "what's in" directories → use file_list_tool
- "search", "find", or "look for" files → use file_search_tool
- "tree", "structure", or "hierarchy" of directories → use file_tree_tool

Support location aliases (e.g., "docs:readme.md") and relative paths. Always provide helpful context about what you found or did.

Be concise but informative. If a file is large, summarize key points rather than repeating everything.
""",
)


@file_agent.tool
async def file_read_tool(
    ctx: RunContext[FileStorage], request: FileReadRequest
) -> str:
    """Read and return the contents of a file."""
    try:
        content = ctx.deps.read_file(request.path, request.show_line_numbers)
        
        # Add metadata about the file
        file_path = ctx.deps.resolve_path(request.path)
        file_size = len(content.encode('utf-8'))
        line_count = content.count('\n') + 1 if content else 0
        
        # Return content with metadata
        metadata = f"File: {file_path.name} ({file_size:,} bytes, {line_count} lines)"
        
        if file_size > 10000:  # Large file warning
            metadata += "\n[Large file - consider asking for a summary instead of the full content]"
            
        return f"{metadata}\n\n{content}"
        
    except ValueError as e:
        raise ModelRetry(f"Cannot read file: {e}")


@file_agent.tool
async def file_write_tool(
    ctx: RunContext[FileStorage], request: FileWriteRequest
) -> str:
    """Write content to a file (create new or overwrite existing)."""
    try:
        if request.mode not in ["write", "append"]:
            raise ModelRetry("Mode must be 'write' or 'append'")
            
        result = ctx.deps.write_file(request.path, request.content, request.mode)
        
        # Add some context about what was written
        content_size = len(request.content.encode('utf-8'))
        line_count = request.content.count('\n') + 1 if request.content else 0
        
        return f"{result} ({content_size:,} bytes, {line_count} lines)"
        
    except ValueError as e:
        raise ModelRetry(f"Cannot write file: {e}")


@file_agent.tool  
async def file_list_tool(
    ctx: RunContext[FileStorage], request: FileListRequest
) -> str:
    """List the contents of a directory."""
    try:
        items = ctx.deps.list_directory(request.path, request.show_hidden)
        
        if not items:
            return f"Directory is empty: {request.path or 'current directory'}"
        
        # Format the listing
        result_lines = []
        dir_path = ctx.deps.resolve_path(request.path) if request.path else ctx.deps.context.current_directory
        result_lines.append(f"Contents of {dir_path}:")
        result_lines.append("")
        
        # Group by type
        directories = [item for item in items if item["type"] == "directory"]
        files = [item for item in items if item["type"] == "file"]
        
        if directories:
            result_lines.append("Directories:")
            for item in directories:
                result_lines.append(f"  📁 {item['name']}/")
            result_lines.append("")
        
        if files:
            result_lines.append("Files:")
            for item in files:
                size_str = f" ({item['size']:,} bytes)" if 'size' in item else ""
                result_lines.append(f"  📄 {item['name']}{size_str}")
        
        result_lines.append(f"\nTotal: {len(directories)} directories, {len(files)} files")
        
        return "\n".join(result_lines)
        
    except ValueError as e:
        raise ModelRetry(f"Cannot list directory: {e}")


@file_agent.tool
async def file_search_tool(
    ctx: RunContext[FileStorage], request: FileSearchRequest
) -> str:
    """Search for files by name pattern or content."""
    try:
        results = ctx.deps.search_files(
            request.pattern, 
            request.path, 
            request.search_content
        )
        
        if not results:
            search_location = request.path or "current directory"
            search_type = "names and content" if request.search_content else "names"
            return f"No files found matching '{request.pattern}' in {search_location} (searched {search_type})"
        
        # Format results
        result_lines = []
        search_location = request.path or "current directory"
        search_type = "names and content" if request.search_content else "names only"
        
        result_lines.append(f"Search results for '{request.pattern}' in {search_location} ({search_type}):")
        result_lines.append("")
        
        # Group by match type
        name_matches = [r for r in results if r["match_type"] == "filename"]
        content_matches = [r for r in results if r["match_type"] == "content"]
        
        if name_matches:
            result_lines.append("Filename matches:")
            for result in name_matches:
                icon = "📁" if result["type"] == "directory" else "📄"
                result_lines.append(f"  {icon} {result['path']}")
            result_lines.append("")
        
        if content_matches:
            result_lines.append("Content matches:")
            for result in content_matches:
                result_lines.append(f"  📄 {result['path']}")
            result_lines.append("")
        
        result_lines.append(f"Found {len(results)} total matches")
        
        return "\n".join(result_lines)
        
    except ValueError as e:
        raise ModelRetry(f"Search failed: {e}")


@file_agent.tool
async def file_tree_tool(
    ctx: RunContext[FileStorage], request: FileTreeRequest
) -> str:
    """Show directory tree structure."""
    try:
        if request.max_depth < 1 or request.max_depth > 10:
            raise ModelRetry("max_depth must be between 1 and 10")
            
        tree = ctx.deps.get_directory_tree(request.path, request.max_depth)
        
        def format_tree(node, prefix="", is_last=True):
            """Format tree node recursively."""
            lines = []
            
            # Current node
            icon = "📁" if node["type"] == "directory" else "📄" if node["type"] == "file" else "❌"
            connector = "└── " if is_last else "├── "
            
            name = node["name"]
            if node["type"] == "file" and "size" in node:
                name += f" ({node['size']:,} bytes)"
            elif node["type"] == "error":
                name = f"❌ {name}"
                
            lines.append(f"{prefix}{connector}{icon} {name}")
            
            # Children
            if "children" in node and node["children"]:
                extension = "    " if is_last else "│   "
                children = node["children"]
                for i, child in enumerate(children):
                    child_is_last = i == len(children) - 1
                    lines.extend(format_tree(child, prefix + extension, child_is_last))
            
            return lines
        
        tree_lines = format_tree(tree)
        result = "\n".join(tree_lines)
        
        # Add summary
        dir_path = ctx.deps.resolve_path(request.path) if request.path else ctx.deps.context.current_directory
        result += f"\n\nDirectory tree for {dir_path} (max depth: {request.max_depth})"
        
        return result
        
    except ValueError as e:
        raise ModelRetry(f"Cannot show tree: {e}")


def create_file_integration(config, current_directory):
    """
    Create a FileStorage instance configured for the current session.
    
    Parameters
    ----------
    config : Config
        Ocat configuration object
    current_directory : Path
        Current working directory
        
    Returns
    -------
    FileStorage
        Configured file storage instance
    """
    context = FileOperationContext(
        locations=config.locations or {},
        current_directory=current_directory,
        max_file_size=1024 * 1024  # 1MB limit
    )
    
    return FileStorage(context)
