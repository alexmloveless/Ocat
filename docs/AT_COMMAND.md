# /at Command - Direct Task Addition

The `/at` command allows you to add tasks directly without engaging the LLM, providing a fast and efficient way to create tasks.

## Usage

```
/at <category> <priority> "<task text>"
```

### Parameters

- `<category>`: Task category (e.g., chores, work, personal)
- `<priority>`: Priority level - must be one of: `low`, `medium`, `high`, `urgent`  
- `<task text>`: Description of the task (use quotes if it contains spaces)

### Examples

```bash
# Simple task
/at chores high "do something boring"

# Work task
/at work urgent "finish the quarterly report"

# Personal task with complex description
/at personal medium "book dentist appointment for next month"

# Shopping item
/at shopping low "buy groceries for the weekend"
```

## Features

- **Fast Creation**: Creates tasks instantly without LLM processing
- **Automatic Display**: Shows the updated task list after creation
- **Validation**: Validates priority levels and provides helpful error messages
- **Case Insensitive**: Priority can be specified in any case (HIGH, high, High, etc.)
- **Rich Formatting**: Tasks are displayed with color-coded categories and priority indicators

## Error Handling

The command provides clear error messages for:
- Insufficient arguments
- Invalid priority levels
- Productivity system unavailable
- Storage errors

## Integration

After successfully creating a task, the command automatically displays the current open task list using the same formatting as the `/st` command, sorted by creation date (newest first).

## Aliases

The command can also be invoked using:
- `/add-task`

## Related Commands

- `/st` - Show tasks with filtering and sorting options
- `/help at` - Show help for the /at command

This command is ideal for quick task entry when you know exactly what you want to add without needing LLM assistance for parsing or interpretation.