# Productivity System Development Tasks

## Overview
Development guide for implementing the productivity system with pydantic-ai function calling. This system allows LLM models to create, read, update, and delete productivity entities (tasks, events, reminders, memories) through natural language commands prefixed with `!`.

## Core Architecture

### Technology Stack
- **pydantic-ai**: Function calling framework with automatic validation
- **ChromaDB**: Vector storage (existing Ocat vector store)
- **Pydantic**: Entity models and parameter validation
- **Rich**: Console output formatting (existing Ocat dependency)

### Key Components
1. **Productivity Agent**: pydantic-ai Agent with registered tools
2. **Entity Models**: Pydantic BaseModel classes for each entity type
3. **Vector Store Abstraction**: Wrapper around existing Ocat vector store
4. **Tool Functions**: CRUD operations for each entity type
5. **Output Formatters**: Consistent display formatting

## Entity Definitions

### Base Entity Model
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class BaseEntity(BaseModel):
    pseudo_id: str = Field(description="Human-readable ID like task001")
    entity_type: Literal["task", "event", "reminder", "memory"]
    content: str = Field(description="Main text content")
    status: Literal["active", "completed", "deleted"] = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### Entity Types
1. **Task**: due_date (optional), category, tags, status
2. **Event**: date_time (required), end_time (optional), participants, all_day flag
3. **Reminder**: trigger_datetime, category, status
4. **Memory**: Simple storage with just base fields

## Implementation Tasks

### Phase 1: Core Infrastructure

#### 1. Entity Models (`src/ocat/productivity/models.py`)
- [ ] Create BaseEntity pydantic model
- [ ] Create Task model with due dates and categories
- [ ] Create Event model with datetime handling
- [ ] Create Reminder model with trigger times
- [ ] Create Memory model (minimal)
- [ ] Add validation methods for date parsing
- [ ] Add status normalization (e.g., "done" → "completed")

#### 2. Vector Store Abstraction (`src/ocat/productivity/storage.py`)
- [ ] Create ProductivityStorage class wrapping existing vector store
- [ ] Implement pseudo ID generation system (type-specific counters)
- [ ] Add CRUD operations with proper metadata handling
- [ ] Implement entity search and filtering
- [ ] Add soft deletion support via status field
- [ ] Ensure thread safety for concurrent operations

#### 3. Tool Functions (`src/ocat/productivity/tools.py`)
- [ ] Create productivity agent with pydantic-ai
- [ ] Implement create_task tool with RunContext
- [ ] Implement create_event tool with datetime parsing
- [ ] Implement create_reminder tool
- [ ] Implement create_memory tool
- [ ] Implement read/search tools with filtering
- [ ] Implement update tools by pseudo ID
- [ ] Implement delete tools (soft delete)
- [ ] Add error handling with ModelRetry exceptions

#### 4. Output Formatting (`src/ocat/productivity/formatters.py`)
- [ ] Create entity display formatters (plain text, markdown, CSV)
- [ ] Implement consistent output styling with Rich
- [ ] Add table/list views for multiple entities
- [ ] Support dictionary output for model consumption

#### 5. Integration (`src/ocat/productivity/agent.py`)
- [ ] Create productivity agent configuration
- [ ] Register all tools with proper dependencies
- [ ] Add system prompt with tool documentation
- [ ] Configure RunContext with storage abstraction
- [ ] Set up proper error handling and retries

### Phase 2: Chat Integration

#### 6. Main Agent Integration (`src/ocat/chat.py`)
- [ ] Register productivity tools with main chat agent
- [ ] Update system prompt with productivity capabilities
- [ ] Ensure natural language intent recognition
- [ ] Maintain conversation context with tool usage
- [ ] Handle productivity tool errors gracefully

#### 7. Configuration (`src/ocat/config.py`)
- [ ] Add productivity system configuration options
- [ ] Configure entity types and their properties
- [ ] Set up default categories and statuses
- [ ] Add output format preferences

### Phase 3: Testing & Documentation

#### 8. Testing (`tests/test_productivity.py`)
- [ ] Unit tests for entity models
- [ ] Integration tests for storage layer
- [ ] Tool function tests with mock dependencies
- [ ] Agent integration tests
- [ ] Error handling and validation tests
- [ ] Performance tests for large entity sets

#### 9. Documentation
- [ ] Update README with productivity features
- [ ] Create user guide for productivity commands
- [ ] Document entity schemas and validation rules
- [ ] Add examples for common use cases
- [ ] Document configuration options

## Architecture Decisions Made

### Agent Integration
- Register productivity tools directly with main chat agent
- Natural language intent recognition - no special prefix needed
- Tools seamlessly integrated into conversation flow

### RunContext Dependencies
- Use ProductivityStorage abstraction as dependency
- Provides clean interface without exposing internal vector store details
- Allows for future storage backend changes

### Entity Storage
- Use same ChromaDB collection with entity_type metadata
- Separate collections could be added later if needed
- Pseudo IDs stored in metadata with type-specific counters

### Command Processing
- Model receives natural language requests and recognizes productivity intent
- pydantic-ai handles function calling and parameter validation
- Automatic retry on validation errors

## Development Commands

### Setup
```bash
poetry install
poetry run pip install pydantic-ai
```

### Testing
```bash
poetry run pytest tests/test_productivity.py -v
```

### Type Checking
```bash
poetry run mypy src/ocat/productivity/
```

### Development Cycle
```bash
./dev.sh "feat: add productivity system foundation"
```

## Next Steps After Implementation

1. **User Testing**: Get feedback on natural language command interface
2. **Performance Optimization**: Optimize vector store queries for large datasets
3. **Advanced Features**: Add recurring events, task dependencies, smart scheduling
4. **External Integrations**: Calendar sync, task manager APIs
5. **Mobile/Web Interface**: Build GUI for productivity features

## Files Structure
```
src/ocat/productivity/
├── __init__.py
├── models.py          # Pydantic entity models
├── storage.py         # Vector store abstraction
├── tools.py           # pydantic-ai tool functions
├── formatters.py      # Output formatting
└── agent.py           # Productivity agent setup

tests/
├── test_productivity.py
└── test_productivity_integration.py
```

## Key Considerations

- **Backward Compatibility**: Don't break existing vector store functionality
- **Performance**: Consider indexing strategies for large entity sets
- **User Experience**: Make natural language commands intuitive
- **Error Messages**: Provide clear feedback for invalid commands
- **Security**: Validate all inputs and prevent injection attacks
- **Extensibility**: Design for easy addition of new entity types

---
*This document will be updated as implementation progresses and requirements evolve.*
