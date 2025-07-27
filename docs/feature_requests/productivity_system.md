# Productivity System Feature Request

## Overview
Implement a function calling system that allows LLM models to interact with local productivity entities (tasks, events, reminders, memories) through the vector store using natural language commands.

## Architecture Decisions

### Function Calling Framework
- **Technology**: pydantic-ai function calling system
- **Documentation**: `/Users/alex/Documents/repos/pydantic-ai/docs`
- **Integration**: Model receives function call capabilities via system prompt

### Command Interface
- **Prefix**: `!` (exclamation point) to distinguish from human-only `/` commands
- **Example**: `! create a reminder for next tuesday to call Sam`
- **Processing**: Send `!` commands directly to model, system prompt explains handling
- **Keywords**: Operations must start with create/update/read/delete as first word
- **Aliases**: Support aliases like "add meeting" → "create event"

### Storage Architecture
- **Backend**: Same ChromaDB vector store as conversation history
- **Abstraction**: Create separate abstraction layer hiding core vector store operations from model
- **Access Control**: Read-only access to saved chats, full CRUD for productivity entities

### Entity System

#### Entity Types
1. **Tasks**
   - Due date (optional)
   - Category
   - Tags field
   - Status (open/in-progress/complete/deleted)

2. **Events/Meetings**
   - Date and time (required)
   - All-day flag for date-only events
   - Start/end times for timed events
   - Multi-day support
   - Participants (free text)
   - Minimum viable meeting system requirements

3. **Reminders**
   - Trigger date/time
   - Categories
   - Status (open/in-progress/complete/deleted)
   - No alerting system (storage/CRUD only)

4. **Memories**
   - Basic storage entity
   - Minimal required fields

#### Entity Properties
- **Pseudo IDs**: Type-specific sequential numbering (task001, task002, event001, event002)
- **Metadata**: All entities have created date, type, status
- **Text Storage**: Plain text values stored as vectors
- **Status**: Soft deletion using status field as metadata
- **Validation**: Pydantic models enforce constraints and standardization

### Data Management

#### CRUD Operations
- **Create**: Natural language entity creation
- **Read**: Query and retrieve entities
- **Update**: Modify existing entities by pseudo ID
- **Delete**: Soft delete using status field

#### Conflict Resolution
- **Ambiguity**: When updates are ambiguous, find similar items and ask user to specify
- **Never guess**: Always request clarification for unclear requests
- **Missing data**: Ask for required information when defaults unavailable

#### Output Formats
- **Display**: Handled by package functions, not model
- **Formats**: Plain text, Markdown, CSV options
- **Dictionary**: Model can request dictionary format
- **Consistency**: Standardized output across all entity types

### Error Handling
- **pydantic-ai**: Framework handles validation and error responses
- **Model Decision**: Model receives errors and decides response approach
- **User Feedback**: Clear error messages for invalid operations

### Integration Points

#### System Prompt
- Document available functions and usage patterns
- Explain `!` prefix behavior
- Provide function metadata and constraints
- Include keyword requirements and aliases

#### Response Flow
1. User sends `! command`
2. Model processes and calls appropriate function
3. Function executes and returns result/error
4. Model incorporates response into user reply
5. Consistent output formatting applied

## Implementation Scope

### Phase 1 (Current)
- Core function calling infrastructure
- Basic CRUD operations for all entity types
- Pydantic model definitions
- Vector store abstraction layer
- Pseudo ID system

### Excluded from Phase 1
- Alerting system for reminders
- Advanced querying capabilities
- UI enhancements beyond console output
- Integration with external calendar systems

## Technical Notes
- Maintain backward compatibility with existing vector store
- Ensure thread safety for concurrent operations
- Follow existing Ocat code style and patterns
- Use type hints and proper documentation
- Comprehensive test coverage required

## Future Considerations
- Plugin architecture for additional entity types
- External integrations (calendar, task managers)
- Advanced search and filtering capabilities
- Notification and alerting systems
- Web/mobile interfaces

---
*This document will be updated as implementation progresses and requirements evolve.*
