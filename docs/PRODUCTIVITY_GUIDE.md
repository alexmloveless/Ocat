# Productivity System User Guide

## Overview

Ocat includes a powerful productivity system that allows you to manage tasks, events, reminders, and memories using natural language commands prefixed with a routing marker. The system integrates seamlessly with your chat conversations and stores everything in the same vector database as your chat history.

## Getting Started

To use productivity features, prefix your commands with the routing marker (default: `%`):

```
🐱 > % add task "finish quarterly report" due next Friday
🐱 > % create meeting with team tomorrow at 2pm
🐱 > % show my tasks for this week
```

The routing marker is configurable in your `ocat.yaml` file:
```yaml
productivity:
  routing_marker: "%"    # Change to any symbol you prefer
```

## Features

- **Marker-Based Interface**: Create and manage productivity entities using commands prefixed with a configurable marker (default: `%`)
- **Multiple Entity Types**: Tasks, events, reminders, and memories
- **Flexible Date Parsing**: Supports natural date expressions like "next Tuesday" or "in 2 weeks"
- **Pseudo IDs**: Easy-to-remember identifiers like `task001`, `event001`
- **Status Tracking**: Track completion and progress of tasks and reminders
- **Vector Storage**: Leverages the same ChromaDB storage as chat history for seamless integration

## Entity Types

### Tasks
Manage your to-do items with optional due dates, categories, and priority levels.

**Examples:**
```
🐱 > % create a task to review the quarterly report
🐱 > % add task: finish the presentation slides due next Friday
🐱 > % make a high priority task to call the client by tomorrow
```

**Features:**
- Optional due dates with flexible parsing
- Categories for organization
- Priority levels (low, medium, high, urgent)
- Tags for additional classification
- Status tracking (active, in_progress, completed, deleted)

### Events
Schedule meetings, appointments, and other time-based activities.

**Examples:**
```
🐱 > % add meeting with team on Friday at 2pm
🐱 > % schedule doctor appointment next Tuesday at 10:30am
🐱 > % create event: project deadline on December 15th
```

**Features:**
- Start and end times
- All-day event support
- Participant tracking
- Location information
- Multi-day event support

### Reminders
Set up notifications and memory aids for important items.

**Examples:**
```
🐱 > create a reminder for next Tuesday to call Sam
🐱 > remind me to water the plants every Monday
🐱 > set reminder: submit expense report by month end
```

**Features:**
- Trigger date/time
- Categories for organization
- Status tracking
- Recurring reminder support

### Memories
Store important information, notes, and reference material.

**Examples:**
```
🐱 > remember that Sarah prefers tea over coffee
🐱 > save memory: the wifi password is "SecureNet123"
🐱 > add to memory: client prefers morning meetings
```

**Features:**
- Free-form text storage
- Searchable content
- Categorization
- Timestamped entries

## Natural Language Commands

### Creating Entities

The system recognizes various natural language patterns for creating productivity entities:

**Task Creation:**
- "create a task to..."
- "add task..."
- "new task..."
- "make a task..."
- "todo..."

**Event Creation:**
- "schedule..."
- "add meeting..."
- "create event..."
- "book..."

**Reminder Creation:**
- "remind me to..."
- "create reminder..."
- "set reminder..."

**Memory Creation:**
- "remember..."
- "save memory..."
- "add to memory..."
- "note that..."

### Viewing Entities

**List Commands:**
```
🐱 > show my tasks
🐱 > list events for this week
🐱 > display reminders
🐱 > what are my memories?
```

**Filtered Views:**
```
🐱 > show tasks due today
🐱 > list high priority tasks
🐱 > show events for next week
🐱 > display active reminders
```

### Updating Entities

**Status Updates:**
```
🐱 > mark task001 as completed
🐱 > set task002 to in progress
🐱 > complete reminder003
```

**Content Updates:**
```
🐱 > update task001 content to "finish quarterly report by Friday"
🐱 > change event002 time to 3pm
🐱 > modify reminder001 to trigger next week
```

### Deleting Entities

```
🐱 > delete task001
🐱 > remove event002
🐱 > cancel reminder003
```

## Date and Time Parsing

The system supports flexible date and time expressions:

**Relative Dates:**
- "tomorrow"
- "next Tuesday"
- "in 2 weeks"
- "next month"

**Specific Dates:**
- "December 15th"
- "2024-12-25"
- "Jan 1, 2024"

**Times:**
- "2pm"
- "14:30"
- "10:30am"
- "at noon"

**Combined:**
- "next Friday at 2pm"
- "tomorrow morning at 9am"
- "December 15th at 3:30pm"

## Pseudo IDs

Each entity gets a human-readable pseudo ID for easy reference:

- Tasks: `task001`, `task002`, `task003`...
- Events: `event001`, `event002`, `event003`...
- Reminders: `reminder001`, `reminder002`, `reminder003`...
- Memories: `memory001`, `memory002`, `memory003`...

These IDs are displayed when you list entities and can be used in update/delete commands.

## Status Management

### Task Status
- **active**: New or open tasks
- **in_progress**: Tasks currently being worked on
- **completed**: Finished tasks
- **deleted**: Soft-deleted tasks (hidden from normal views)

### Event Status
- **active**: Upcoming events
- **completed**: Past events
- **deleted**: Cancelled events

### Reminder Status
- **active**: Active reminders
- **completed**: Triggered or acknowledged reminders
- **deleted**: Cancelled reminders

## Output Formats

The system can display information in various formats:

**Plain Text:**
```
🐱 > show my tasks in plain text
```

**Markdown:**
```
🐱 > list events in markdown format
```

**CSV:**
```
🐱 > export tasks as CSV
```

## Tips and Best Practices

1. **Be Specific**: Include as much detail as possible when creating entities
2. **Use Categories**: Organize related items with categories like "work", "personal", "project-alpha"
3. **Set Priorities**: Use priority levels to focus on important tasks
4. **Regular Reviews**: Periodically review and update your productivity entities
5. **Natural Language**: Don't worry about exact syntax - the system understands various phrasings

## Integration with Chat

The productivity system is fully integrated with your chat experience:

- All entities are stored in the same vector database as your conversations
- You can reference productivity items in regular chat
- The system remembers context from previous conversations
- Search functionality works across both chat history and productivity entities

## Troubleshooting

**Common Issues:**

1. **Date Parsing Errors**: If a date isn't recognized, try being more specific or use ISO format (YYYY-MM-DD)
2. **Ambiguous Updates**: When updating entities, always include the pseudo ID for clarity
3. **Missing Entities**: Check if you're looking in the right status (active vs completed)

**Getting Help:**
```
🐱 > help productivity
🐱 > show productivity commands
🐱 > what can I do with tasks?
```

The system will provide context-specific help and examples for any productivity features.
