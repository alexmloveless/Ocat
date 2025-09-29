# Productivity System Feature Request

## Overview
Implement a function calling system that allows LLM models to interact with local productivity entities (tasks, events, reminders, memories) through the vector store using natural language commands.

## Architecture Decisions

### Function Calling Framework
- **Technology**: pydantic-ai function calling system
- **Documentation**: `/Users/alex/Documents/repos/pydantic-ai/docs`
- **Integration**: Create productivity agent with tools registered via `@agent.tool` decorator
- **Architecture**: 
  - Agent class manages tool registration and execution
  - RunContext provides dependency injection for vector store access
  - Automatic parameter validation via pydantic models
  - Tool return values automatically sent back to model for response inclusion
  - Built-in error handling with retry mechanism

### Command Interface
- **Marker-Based Routing**: Commands must be prefixed with configurable routing marker (default: `%`)
- **Examples**: 
  - "% create a reminder for next tuesday to call Sam"
  - "% add meeting with team on Friday at 2pm"
  - "% show my tasks for this week"
  - "% mark task 123 as completed"
- **Processing**: Explicit marker detection routes to productivity agent
- **Configuration**: Routing marker configurable in ocat.yaml (productivity.routing_marker)
- **Flexible Phrasing**: Handles variations like "add task", "new reminder", "schedule meeting" after marker

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
- **Validation**: Pydantic BaseModel classes enforce constraints and standardization
- **Tool Parameters**: Entity creation/update uses pydantic models for automatic validation

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
- **Automatic Validation**: pydantic-ai validates tool parameters and sends errors back to model
- **ModelRetry Exception**: Tools can raise ModelRetry for custom error handling
- **Retry Mechanism**: Built-in retry system respects configured retry limits
- **Model Decision**: Model receives validation errors and decides response approach
- **User Feedback**: Clear error messages for invalid operations

### Integration Points

#### System Prompt
- Document available productivity tools and capabilities
- Explain natural language productivity intent recognition
- Provide tool descriptions and usage examples
- Include entity types and their properties

#### Response Flow
1. User sends natural language request
2. Model recognizes productivity intent and calls appropriate tool
3. Tool executes and returns result/error to model
4. Model incorporates response into conversational reply
5. Consistent output formatting applied

## Implementation Scope

### Phase 1 (Current)
- Productivity agent with pydantic-ai tools
- Basic CRUD operations for all entity types
- Pydantic BaseModel entity definitions
- Vector store abstraction with RunContext dependency injection
- Pseudo ID system
- Integration with existing Ocat chat system

### Excluded from Phase 1
- Alerting system for reminders
- Advanced querying capabilities
- UI enhancements beyond console output
- Integration with external calendar systems

## Technical Implementation Questions

### Architecture Decisions Made
1. **Agent Integration**: Tools integrated into main chat agent for seamless conversation flow
2. **RunContext Dependencies**: ProductivityStorage abstraction provides clean vector store interface
3. **Command Detection**: Natural language intent recognition - no special prefix required
4. **Entity Storage**: Same ChromaDB collection with entity_type metadata for unified search

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
