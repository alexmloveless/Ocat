"""Tests for the marker-based productivity routing system."""

import pytest
from unittest.mock import Mock
from ocat.productivity.integration import ProductivityIntegration


class TestProductivityRouting:
    """Test cases for marker-based productivity routing."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock the storage dependency
        mock_storage = Mock()
        self.integration = ProductivityIntegration(mock_storage)

    def test_should_use_productivity_agent_with_default_marker(self):
        """Test routing with default % marker."""
        # Should route with marker
        assert self.integration.should_use_productivity_agent("% add task to review docs")
        assert self.integration.should_use_productivity_agent("%create meeting tomorrow")
        assert self.integration.should_use_productivity_agent("% show my tasks")
        
        # Should not route without marker
        assert not self.integration.should_use_productivity_agent("add task to review docs")
        assert not self.integration.should_use_productivity_agent("create meeting tomorrow")
        assert not self.integration.should_use_productivity_agent("show my tasks")
        
    def test_should_use_productivity_agent_with_custom_marker(self):
        """Test routing with custom marker."""
        # Should route with custom marker
        assert self.integration.should_use_productivity_agent("! add task", "!")
        assert self.integration.should_use_productivity_agent("@ create meeting", "@")
        assert self.integration.should_use_productivity_agent("# show tasks", "#")
        
        # Should not route with different marker
        assert not self.integration.should_use_productivity_agent("% add task", "!")
        assert not self.integration.should_use_productivity_agent("@ create meeting", "%")
        
    def test_should_use_productivity_agent_with_whitespace(self):
        """Test routing handles whitespace correctly."""
        # Should work with leading/trailing whitespace
        assert self.integration.should_use_productivity_agent("  % add task  ")
        assert self.integration.should_use_productivity_agent("\t% create meeting\n")
        
        # Should not match if marker is not at start after stripping
        assert not self.integration.should_use_productivity_agent("add % task")
        assert not self.integration.should_use_productivity_agent("this % is not at start")

    def test_should_use_productivity_agent_empty_input(self):
        """Test routing with empty or whitespace-only input."""
        assert not self.integration.should_use_productivity_agent("")
        assert not self.integration.should_use_productivity_agent("   ")
        assert not self.integration.should_use_productivity_agent("\t\n")

    def test_should_use_productivity_agent_marker_only(self):
        """Test routing with marker-only input."""
        assert self.integration.should_use_productivity_agent("%")
        assert self.integration.should_use_productivity_agent("% ")
        assert self.integration.should_use_productivity_agent("! ", "!")

    def test_should_use_productivity_agent_multi_character_marker(self):
        """Test routing with multi-character markers."""
        # Should work with multi-character markers
        assert self.integration.should_use_productivity_agent(">> add task", ">>")
        assert self.integration.should_use_productivity_agent("todo: create meeting", "todo:")
        
        # Should not partially match
        assert not self.integration.should_use_productivity_agent("> add task", ">>")
        assert not self.integration.should_use_productivity_agent("tod create meeting", "todo:")

    def test_should_use_productivity_agent_case_sensitivity(self):
        """Test that marker matching is case sensitive."""
        # Should be case sensitive with letter-based markers
        assert self.integration.should_use_productivity_agent("a add task", "a")
        assert not self.integration.should_use_productivity_agent("a add task", "A")
        
        # Custom markers are also case sensitive
        assert self.integration.should_use_productivity_agent("TODO: add task", "TODO:")
        assert not self.integration.should_use_productivity_agent("TODO: add task", "todo:")
