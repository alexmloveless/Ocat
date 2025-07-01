"""
Tests for path utilities module.

Tests the location alias resolution and validation functionality.
"""

import pytest
from pathlib import Path
from ocat.utils.path_utils import resolve_path_with_aliases, validate_location_aliases


class TestResolvePathWithAliases:
    """Test cases for the resolve_path_with_aliases function."""

    def test_regular_path_without_alias(self):
        """Test that regular paths are handled correctly."""
        locations = {"conv": "~/conversations/", "docs": "~/documents/"}
        
        # Test absolute path
        result = resolve_path_with_aliases("/usr/local/file.txt", locations)
        assert result == Path("/usr/local/file.txt")
        
        # Test relative path
        result = resolve_path_with_aliases("./local/file.txt", locations)
        assert result == Path("./local/file.txt").expanduser()
        
        # Test home path
        result = resolve_path_with_aliases("~/file.txt", locations)
        assert result == Path("~/file.txt").expanduser()

    def test_alias_path_resolution(self):
        """Test that alias paths are resolved correctly."""
        locations = {"conv": "~/conversations/", "docs": "~/documents/"}
        
        # Test conv alias
        result = resolve_path_with_aliases("conv:myfile.txt", locations)
        expected = Path("~/conversations/myfile.txt").expanduser()
        assert result == expected
        
        # Test docs alias
        result = resolve_path_with_aliases("docs:subfolder/file.txt", locations)
        expected = Path("~/documents/subfolder/file.txt").expanduser()
        assert result == expected

    def test_alias_path_with_subdirectories(self):
        """Test alias resolution with subdirectories."""
        locations = {"proj": "/projects/"}
        
        result = resolve_path_with_aliases("proj:myproj/src/main.py", locations)
        expected = Path("/projects/myproj/src/main.py")
        assert result == expected

    def test_nonexistent_alias_raises_error(self):
        """Test that using a nonexistent alias raises ValueError."""
        locations = {"conv": "~/conversations/"}
        
        with pytest.raises(ValueError, match="Location alias 'docs' not found"):
            resolve_path_with_aliases("docs:file.txt", locations)

    def test_empty_locations_dict(self):
        """Test behavior with empty locations dictionary."""
        locations = {}
        
        # Regular path should work
        result = resolve_path_with_aliases("~/file.txt", locations)
        assert result == Path("~/file.txt").expanduser()
        
        # Alias should fail
        with pytest.raises(ValueError, match="Location alias 'conv' not found"):
            resolve_path_with_aliases("conv:file.txt", locations)

    def test_colon_in_regular_path(self):
        """Test that colons in regular paths (like Windows drives) are handled."""
        locations = {"conv": "~/conversations/"}
        
        # Test Windows-style path
        result = resolve_path_with_aliases("C:/Windows/file.txt", locations)
        assert result == Path("C:/Windows/file.txt")
        
        # Test path starting with dot
        result = resolve_path_with_aliases("./path:with:colons.txt", locations)
        assert result == Path("./path:with:colons.txt").expanduser()

    def test_alias_with_multiple_colons(self):
        """Test alias resolution when the filename contains colons."""
        locations = {"conv": "~/conversations/"}
        
        result = resolve_path_with_aliases("conv:file:with:colons.txt", locations)
        expected = Path("~/conversations/file:with:colons.txt").expanduser()
        assert result == expected


class TestValidateLocationAliases:
    """Test cases for the validate_location_aliases function."""

    def test_valid_aliases(self):
        """Test validation of valid location aliases."""
        locations = {
            "conv": "~/conversations/",
            "docs": "~/documents/",
            "proj": "/projects/"
        }
        
        result = validate_location_aliases(locations)
        assert result is None

    def test_empty_aliases(self):
        """Test validation of empty aliases dictionary."""
        locations = {}
        
        result = validate_location_aliases(locations)
        assert result is None

    def test_invalid_alias_names(self):
        """Test validation fails for invalid alias names."""
        # Test alias with colon
        locations = {"conv:bad": "~/conversations/"}
        result = validate_location_aliases(locations)
        assert "cannot contain colons" in result
        
        # Test alias that's not a valid identifier
        locations = {"123invalid": "~/conversations/"}
        result = validate_location_aliases(locations)
        assert "not a valid identifier" in result

    def test_alias_with_special_characters(self):
        """Test validation with special characters in alias names."""
        # Test valid alias names
        locations = {
            "conv_backup": "~/conversations/backup/",
            "my_docs": "~/documents/",
        }
        result = validate_location_aliases(locations)
        assert result is None
        
        # Test invalid alias names
        locations = {"conv-bad": "~/conversations/"}  # hyphen not allowed in identifier
        result = validate_location_aliases(locations)
        assert "not a valid identifier" in result
