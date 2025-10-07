"""
Tests for the /ct (CompleteTaskDirectCommand) command.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from ocat.commands.productivity_commands import CompleteTaskDirectCommand
from ocat.commands import CommandResult
from ocat.productivity.models import Task, EntityStatus, EntityType
from datetime import datetime


@pytest.fixture
def mock_context():
    """Create a mock context with productivity integration."""
    context = Mock()
    context.productivity_integration = Mock()
    context.productivity_integration.storage = Mock()
    context.console = Mock()
    context.console.print = Mock()
    return context


@pytest.fixture
def mock_task():
    """Create a mock task."""
    return Task(
        pseudo_id="T123",
        content="Test task content",
        category="work",
        priority="high",
        status=EntityStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestCompleteTaskDirectCommand:
    """Test the /ct command."""

    @pytest.mark.asyncio
    async def test_complete_task_success(self, mock_context, mock_task):
        """Test successful task completion."""
        # Setup
        mock_context.productivity_integration.storage.get_entity_by_pseudo_id.return_value = mock_task
        mock_context.productivity_integration.storage.update_entity.return_value = True
        
        command = CompleteTaskDirectCommand()
        
        # Execute
        result = await command.execute(["T123"], mock_context)
        
        # Verify
        assert result.success is True
        assert "Completed task T123" in result.message
        mock_context.productivity_integration.storage.update_entity.assert_called_once_with(
            "T123", {"status": EntityStatus.COMPLETED.value}
        )
        mock_context.console.print.assert_called()

    @pytest.mark.asyncio
    async def test_complete_task_no_args(self, mock_context):
        """Test /ct command with no arguments."""
        command = CompleteTaskDirectCommand()
        
        result = await command.execute([], mock_context)
        
        assert result.success is False
        assert "Usage: /ct <task_id>" in result.message

    @pytest.mark.asyncio
    async def test_complete_task_too_many_args(self, mock_context):
        """Test /ct command with too many arguments."""
        command = CompleteTaskDirectCommand()
        
        result = await command.execute(["T123", "extra"], mock_context)
        
        assert result.success is False
        assert "Usage: /ct <task_id>" in result.message

    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(self, mock_context):
        """Test completing a task that doesn't exist."""
        mock_context.productivity_integration.storage.get_entity_by_pseudo_id.return_value = None
        
        command = CompleteTaskDirectCommand()
        
        result = await command.execute(["T999"], mock_context)
        
        assert result.success is False
        assert "No entity found with ID 'T999'" in result.message

    @pytest.mark.asyncio
    async def test_complete_non_task_entity(self, mock_context):
        """Test completing an entity that is not a task."""
        mock_event = Mock()
        mock_event.__class__.__name__ = "Event"
        mock_context.productivity_integration.storage.get_entity_by_pseudo_id.return_value = mock_event
        
        command = CompleteTaskDirectCommand()
        
        result = await command.execute(["E123"], mock_context)
        
        assert result.success is False
        assert "E123 is not a task" in result.message

    @pytest.mark.asyncio
    async def test_complete_already_completed_task(self, mock_context, mock_task):
        """Test completing a task that is already completed."""
        mock_task.status = EntityStatus.COMPLETED
        mock_context.productivity_integration.storage.get_entity_by_pseudo_id.return_value = mock_task
        
        command = CompleteTaskDirectCommand()
        
        result = await command.execute(["T123"], mock_context)
        
        assert result.success is False
        assert "Task T123 is already completed" in result.message

    @pytest.mark.asyncio
    async def test_complete_task_update_fails(self, mock_context, mock_task):
        """Test when the database update fails."""
        mock_context.productivity_integration.storage.get_entity_by_pseudo_id.return_value = mock_task
        mock_context.productivity_integration.storage.update_entity.return_value = False
        
        command = CompleteTaskDirectCommand()
        
        result = await command.execute(["T123"], mock_context)
        
        assert result.success is False
        assert "Failed to complete task T123" in result.message

    @pytest.mark.asyncio
    async def test_complete_task_no_productivity_system(self):
        """Test /ct command when productivity system is not available."""
        context = Mock()
        context.productivity_integration = None
        
        command = CompleteTaskDirectCommand()
        
        result = await command.execute(["T123"], context)
        
        assert result.success is False
        assert "Productivity system not available" in result.message

    @pytest.mark.asyncio
    async def test_complete_task_storage_exception(self, mock_context, mock_task):
        """Test /ct command when storage raises an exception."""
        mock_context.productivity_integration.storage.get_entity_by_pseudo_id.return_value = mock_task
        mock_context.productivity_integration.storage.update_entity.side_effect = Exception("Database error")
        
        command = CompleteTaskDirectCommand()
        
        result = await command.execute(["T123"], mock_context)
        
        assert result.success is False
        assert "Failed to complete task: Database error" in result.message
