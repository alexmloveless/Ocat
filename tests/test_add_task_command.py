"""
Tests for the /at (AddTaskDirectCommand) command.

Tests the direct task addition functionality without LLM engagement.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.ocat.commands.productivity_commands import AddTaskDirectCommand
from src.ocat.commands import CommandResult
from src.ocat.productivity.models import Task, EntityType, EntityStatus
from src.ocat.productivity.storage import ProductivityStorage


@pytest.fixture
def mock_context():
    """Create a mock context with productivity integration."""
    context = Mock()
    context.console = Mock()
    context.console.print = Mock()

    # Mock productivity integration
    context.productivity_integration = Mock()
    context.productivity_integration.storage = Mock(spec=ProductivityStorage)

    return context


@pytest.fixture
def add_task_command():
    """Create an AddTaskDirectCommand instance."""
    return AddTaskDirectCommand()


@pytest.mark.asyncio
async def test_at_command_basic_usage(add_task_command, mock_context):
    """Test basic /at command usage with quoted task text."""
    # Setup mock storage
    mock_storage = mock_context.productivity_integration.storage
    mock_storage.create_entity.return_value = "task001"
    mock_storage.get_entities_by_type.return_value = []

    # Execute command
    args = ["chores", "high", "do something boring"]
    result = await add_task_command.execute(args, mock_context)

    # Verify success
    assert result.success is True
    assert "task001" in result.message

    # Verify storage was called correctly
    mock_storage.create_entity.assert_called_once()
    created_task = mock_storage.create_entity.call_args[0][0]
    assert isinstance(created_task, Task)
    assert created_task.content == "do something boring"
    assert created_task.category == "chores"
    assert created_task.priority == "high"
    assert created_task.status == EntityStatus.ACTIVE


@pytest.mark.asyncio
async def test_at_command_quoted_task_text(add_task_command, mock_context):
    """Test /at command with properly quoted task text."""
    # Setup mock storage
    mock_storage = mock_context.productivity_integration.storage
    mock_storage.create_entity.return_value = "task002"
    mock_storage.get_entities_by_type.return_value = []

    # Execute command with quoted text containing spaces
    args = ["work", "urgent", '"finish the important report by Friday"']
    result = await add_task_command.execute(args, mock_context)

    # Verify success
    assert result.success is True

    # Verify task was created with correct content
    created_task = mock_storage.create_entity.call_args[0][0]
    assert created_task.content == "finish the important report by Friday"
    assert created_task.category == "work"
    assert created_task.priority == "urgent"


@pytest.mark.asyncio
async def test_at_command_insufficient_args(add_task_command, mock_context):
    """Test /at command with insufficient arguments."""
    # Execute command with too few arguments
    args = ["chores", "high"]  # Missing task text
    result = await add_task_command.execute(args, mock_context)

    # Verify failure
    assert result.success is False
    assert "Usage:" in result.message
    assert "Example:" in result.message


@pytest.mark.asyncio
async def test_at_command_invalid_priority(add_task_command, mock_context):
    """Test /at command with invalid priority."""
    # Setup mock storage
    mock_storage = mock_context.productivity_integration.storage
    mock_storage.create_entity.return_value = "task003"
    mock_storage.get_entities_by_type.return_value = []

    # Execute command with invalid priority
    args = ["chores", "super-high", "do something"]
    result = await add_task_command.execute(args, mock_context)

    # Verify failure
    assert result.success is False
    assert "Invalid priority" in result.message
    assert "Valid priorities:" in result.message


@pytest.mark.asyncio
async def test_at_command_no_productivity_system(add_task_command):
    """Test /at command when productivity system is not available."""
    # Create context without productivity integration
    context = Mock()
    context.productivity_integration = None

    # Execute command
    args = ["chores", "high", "do something"]
    result = await add_task_command.execute(args, context)

    # Verify failure
    assert result.success is False
    assert "Productivity system not available" in result.message


@pytest.mark.asyncio
async def test_at_command_displays_task_list(add_task_command, mock_context):
    """Test that /at command displays the task list after creation."""
    # Setup mock storage with existing tasks
    mock_storage = mock_context.productivity_integration.storage
    mock_storage.create_entity.return_value = "task004"

    # Create mock existing tasks
    existing_task1 = Mock()
    existing_task1.pseudo_id = "task001"
    existing_task1.content = "Existing task 1"
    existing_task1.category = "work"
    existing_task1.priority = "medium"
    existing_task1.status = Mock()
    existing_task1.status.value = "active"
    existing_task1.created_at = datetime.now()
    existing_task1.due_date = None

    existing_task2 = Mock()
    existing_task2.pseudo_id = "task002"
    existing_task2.content = "Existing task 2"
    existing_task2.category = "personal"
    existing_task2.priority = "low"
    existing_task2.status = Mock()
    existing_task2.status.value = "active"
    existing_task2.created_at = datetime.now()
    existing_task2.due_date = None

    # Mock get_entities_by_type to return existing tasks
    def mock_get_entities_by_type(entity_type, status, limit):
        if status == EntityStatus.ACTIVE:
            return [existing_task1, existing_task2]
        return []

    mock_storage.get_entities_by_type.side_effect = mock_get_entities_by_type

    # Execute command
    args = ["chores", "high", "new task"]
    result = await add_task_command.execute(args, mock_context)

    # Verify success
    assert result.success is True

    # Verify console.print was called (for both success message and table)
    assert mock_context.console.print.call_count >= 2

    # Verify get_entities_by_type was called to fetch tasks for display
    assert mock_storage.get_entities_by_type.call_count >= 2


@pytest.mark.asyncio
async def test_at_command_all_valid_priorities(add_task_command, mock_context):
    """Test /at command with all valid priority levels."""
    mock_storage = mock_context.productivity_integration.storage
    mock_storage.get_entities_by_type.return_value = []

    valid_priorities = ["low", "medium", "high", "urgent"]

    for i, priority in enumerate(valid_priorities):
        # Reset mock
        mock_storage.reset_mock()
        mock_storage.create_entity.return_value = f"task{i+1:03d}"

        # Execute command with this priority
        args = ["test", priority, f"task with {priority} priority"]
        result = await add_task_command.execute(args, mock_context)

        # Verify success
        assert result.success is True, f"Failed for priority: {priority}"

        # Verify task was created with correct priority
        created_task = mock_storage.create_entity.call_args[0][0]
        assert created_task.priority == priority


@pytest.mark.asyncio
async def test_at_command_case_insensitive_priority(add_task_command, mock_context):
    """Test /at command handles case-insensitive priorities."""
    mock_storage = mock_context.productivity_integration.storage
    mock_storage.create_entity.return_value = "task001"
    mock_storage.get_entities_by_type.return_value = []

    # Test various case combinations
    priority_cases = ["HIGH", "High", "hIgH", "URGENT", "Urgent"]

    for priority in priority_cases:
        # Reset mock
        mock_storage.reset_mock()
        mock_storage.create_entity.return_value = "task001"

        # Execute command
        args = ["test", priority, "test task"]
        result = await add_task_command.execute(args, mock_context)

        # Verify success
        assert result.success is True

        # Verify priority was normalized to lowercase
        created_task = mock_storage.create_entity.call_args[0][0]
        assert created_task.priority == priority.lower()


@pytest.mark.asyncio
async def test_at_command_storage_exception(add_task_command, mock_context):
    """Test /at command handles storage exceptions gracefully."""
    # Setup mock storage to raise exception
    mock_storage = mock_context.productivity_integration.storage
    mock_storage.create_entity.side_effect = Exception("Storage error")

    # Execute command
    args = ["chores", "high", "test task"]
    result = await add_task_command.execute(args, mock_context)

    # Verify failure
    assert result.success is False
    assert "Failed to add task" in result.message
    assert "Storage error" in result.message
