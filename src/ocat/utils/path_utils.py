"""
Path utilities for Ocat.

Provides functions for resolving file paths including location alias expansion.
"""

from pathlib import Path
from typing import Dict, Optional


def resolve_path_with_aliases(path_str: str, locations: Dict[str, str]) -> Path:
    """
    Resolve a file path that may contain location aliases.
    
    Location aliases allow users to define shortcuts for commonly used directories.
    For example, if 'conv' is aliased to '~/conversations/', then 'conv:myfile.txt'
    would resolve to '~/conversations/myfile.txt'.
    
    Parameters
    ----------
    path_str : str
        The path string to resolve, which may contain a location alias
    locations : Dict[str, str]
        Dictionary of location aliases from the configuration
        
    Returns
    -------
    Path
        Resolved pathlib.Path object with ~ expansion applied
        
    Raises
    ------
    ValueError
        If the location alias is not found in the configuration
        
    Examples
    --------
    >>> locations = {"conv": "~/conversations/", "docs": "~/documents/"}
    >>> resolve_path_with_aliases("conv:myfile.txt", locations)
    PosixPath('/Users/user/conversations/myfile.txt')
    >>> resolve_path_with_aliases("~/regular/path.txt", locations)
    PosixPath('/Users/user/regular/path.txt')
    """
    # Check if the path contains an alias (format: alias:path)
    # Exclude Windows drive letters (e.g., C:) and paths starting with /, ~, or .
    if (":" in path_str and 
        not path_str.startswith(("/", "~", ".")) and 
        not (len(path_str) >= 2 and path_str[1] == ":" and path_str[0].isalpha())):
        # Split on the first colon only
        alias, relative_path = path_str.split(":", 1)
        
        if alias not in locations:
            raise ValueError(f"Location alias '{alias}' not found in configuration")
        
        # Get the base path for the alias and expand user home directory
        base_path = Path(locations[alias]).expanduser()
        
        # Combine with the relative path
        full_path = base_path / relative_path
    else:
        # Regular path without alias
        full_path = Path(path_str).expanduser()
    
    return full_path


def validate_location_aliases(locations: Dict[str, str]) -> Optional[str]:
    """
    Validate location aliases configuration.
    
    Checks that all location aliases point to valid directory paths.
    
    Parameters
    ----------
    locations : Dict[str, str]
        Dictionary of location aliases to validate
        
    Returns
    -------
    Optional[str]
        Error message if validation fails, None if all aliases are valid
    """
    for alias, path_str in locations.items():
        try:
            path = Path(path_str).expanduser()
            # Check for colons first (which would also fail isidentifier)
            if ":" in alias:
                return f"Location alias '{alias}' cannot contain colons"
            # Check if it's a valid identifier
            if not alias.isidentifier():
                return f"Location alias '{alias}' is not a valid identifier"
        except Exception as e:
            return f"Invalid path for alias '{alias}': {e}"
    
    return None
