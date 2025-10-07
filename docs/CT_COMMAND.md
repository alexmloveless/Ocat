# /ct Command - Direct Task Completion

The `/ct` command allows you to complete tasks directly without engaging the LLM, providing a fast and efficient way to mark tasks as completed.

## Usage

```
/ct <task_id>
```

**Parameters:**
- `task_id`: The ID of the task to complete (e.g., T123, task001, etc.)

## Examples

### Basic Usage

```
/ct T123
```
Complete task T123

```
/ct task001  
```
Complete task001

## Features

- **Direct database update**: Bypasses the LLM for instant task completion
- **Validation**: Ensures the task exists and is not already completed
- **Status feedback**: Shows confirmation message with task details
- **Error handling**: Clear error messages for invalid task IDs or system issues

## Error Handling

The command provides helpful error messages for common issues:

- **Invalid task ID**: "No entity found with ID 'T999'"
- **Non-task entity**: "E123 is not a task. Only tasks can be completed."
- **Already completed**: "Task T123 is already completed"
- **System unavailable**: "Productivity system not available"

## Related Commands

- `/at <category> <priority> "<task text>"` - Add task directly without LLM
- `/st` - Show tasks
- `/help productivity` - Show productivity system help

## Integration

The `/ct` command works seamlessly with the productivity system:
- Updates task status to "completed" in the database
- Maintains task history and timestamps  
- Works with all task types and categories
- Preserves task metadata (category, priority, etc.)

## Help

- `/help ct` - Show help for the /ct command
- `/help productivity` - Complete productivity system guide
