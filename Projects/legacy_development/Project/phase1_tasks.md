# Phase 1: Core Infrastructure - Detailed Tasks

## Project 1.1: Configuration System Overhaul

### Task 1.1.1: Replace JSON config with YAML
**Estimated Time**: 2-3 hours

#### Subtasks:
1. **Add dependencies**
   ```bash
   poetry add pyyaml pydantic
   ```

2. **Update config.py imports**
   - Replace `import json` with `import yaml`
   - Add `from pydantic import BaseModel, Field, validator`

3. **Create Pydantic config models**
   - `ModelConfig` class for LLM settings
   - `VectorStoreConfig` class for vector store settings  
   - `DisplayConfig` class for UI settings
   - `OcatConfig` main configuration class

4. **Update file loading methods**
   - Replace `json.load()` with `yaml.safe_load()`
   - Add YAML schema validation
   - Update default config file paths (.yaml extension)

#### Acceptance Criteria:
- [ ] Config loads from YAML files
- [ ] Pydantic validation prevents invalid configurations
- [ ] Backward compatibility maintained during transition
- [x] All tests pass

### Task 1.1.2: Implement comprehensive configuration schema
**Estimated Time**: 3-4 hours

#### Bootstrap specification mapping:
```yaml
# Complete config schema based on bootstrap.md
profile_name: str
model: str = "gpt-4o-mini"
temperature: float = 1.0
max_tokens: int = 4000
system_prompt_files: List[str] = []

# Vector store
vector_store_enabled: bool = true
vector_store_path: str
vector_similarity_threshold: float = 0.65
vector_store_chat_window: int = 3
exchange_context_results: int = 5

# Embedding
embedding_model: str = "text-embedding-3-small"
embedding_dimensions: int = 1536
chunk_size: int = 1000

# Display
user_label: str = "User"
assistant_label: str = "Assistant"
no_rich: bool = false
no_color: bool = false
line_width: int = 80
response_on_new_line: bool = true

# Locations
locations: Dict[str, str] = {}
```

#### Subtasks:
1. **Define complete Pydantic schema**
   - All fields from bootstrap specification
   - Proper types and defaults
   - Field validation rules

2. **Add computed properties**
   - Resolved system prompt content
   - Absolute paths for locations
   - Derived embedding settings

3. **Configuration validation**
   - File path existence checks
   - Model name validation
   - Numeric range validation

#### Acceptance Criteria:
- [ ] All bootstrap config fields implemented
- [ ] Sensible defaults for all optional fields
- [ ] Field validation prevents invalid values
- [ ] Clear error messages for configuration issues

### Task 1.1.3: Add command-line argument overrides
**Estimated Time**: 2 hours

#### Subtasks:
1. **Extend CLI parser**
   ```python
   # Add to cli.py create_parser()
   parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARN", "ERROR"])
   parser.add_argument("--dummy-mode", action="store_true")
   parser.add_argument("--vector-store-path", type=str)
   parser.add_argument("--temperature", type=float)
   parser.add_argument("--max-tokens", type=int)
   ```

2. **Implement override logic**
   - CLI args override environment variables
   - Environment variables override config file
   - Config file overrides defaults

3. **Add headless mode support**
   - Vector store operations without interactive chat
   - Query and add document modes

#### Acceptance Criteria:
- [ ] All major config options available as CLI args
- [ ] Precedence order correctly implemented
- [ ] Headless mode functional for vector operations

## Project 1.2: Logging and Error Handling

### Task 1.2.1: Implement structured logging system
**Estimated Time**: 2-3 hours

#### Subtasks:
1. **Create logging.py module**
   ```python
   # src/ocat/utils/logging.py
   import logging
   from typing import Optional
   from enum import Enum
   
   class LogLevel(Enum):
       DEBUG = "DEBUG"
       INFO = "INFO" 
       WARN = "WARN"
       ERROR = "ERROR"
   
   def setup_logger(name: str, level: LogLevel, config) -> logging.Logger:
       # Implementation with context-aware formatting
   ```

2. **Add logging configuration to config schema**
   ```yaml
   logging:
     level: "WARN"
     format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
     show_context: false
   ```

3. **Integrate throughout codebase**
   - Replace print statements with logging
   - Add debug logs for state changes
   - Info logs for user-visible operations

#### Acceptance Criteria:
- [ ] Structured logging available throughout codebase
- [ ] Configurable log levels
- [ ] Clear, actionable log messages
- [ ] Context information in debug logs

### Task 1.2.2: Enhance error handling
**Estimated Time**: 2 hours

#### Subtasks:
1. **Create custom exception classes**
   ```python
   # src/ocat/exceptions.py
   class OcatError(Exception):
       pass
       
   class ConfigError(OcatError):
       pass
       
   class LLMError(OcatError):
       pass
       
   class VectorStoreError(OcatError):
       pass
   ```

2. **Replace catch-all exceptions**
   - Review existing try/except blocks
   - Make exception handling specific
   - Add unique error codes

3. **Add graceful error recovery**
   - Fallback behaviors for non-critical failures
   - User-friendly error messages
   - Recovery suggestions

#### Acceptance Criteria:
- [ ] No generic `except Exception:` blocks
- [ ] Specific exception types for different error categories
- [ ] Clear error messages with recovery suggestions

## Project 1.3: LLM Backend Integration

### Task 1.3.1: Install and configure dependencies
**Estimated Time**: 1 hour

#### Subtasks:
1. **Add LangChain/LangGraph dependencies**
   ```bash
   poetry add langchain langchain-openai langchain-anthropic langchain-google-genai langgraph
   ```

2. **Add provider-specific packages**
   ```bash
   poetry add openai anthropic google-generativeai
   ```

3. **Update pyproject.toml**
   - Ensure Python 3.12+ compatibility
   - Add optional dependencies for different providers

#### Acceptance Criteria:
- [ ] All required dependencies installed
- [ ] No version conflicts
- [ ] Poetry lock file updated

### Task 1.3.2: Create LLM backend abstraction
**Estimated Time**: 4-5 hours

#### Subtasks:
1. **Create backend interface**
   ```python
   # src/ocat/backends/__init__.py
   from abc import ABC, abstractmethod
   from typing import AsyncIterator, Dict, List
   
   class LLMBackend(ABC):
       @abstractmethod
       async def generate_response(self, messages: List[Dict]) -> str:
           pass
           
       @abstractmethod
       async def generate_streaming_response(self, messages: List[Dict]) -> AsyncIterator[str]:
           pass
   ```

2. **Implement provider backends**
   - `OpenAIBackend` class
   - `AnthropicBackend` class  
   - `GoogleBackend` class

3. **Add backend factory**
   ```python
   def create_backend(config: OcatConfig) -> LLMBackend:
       # Factory method to create appropriate backend
   ```

4. **Model switching capability**
   - Runtime model changes
   - Provider auto-detection from model name
   - Configuration validation

#### Acceptance Criteria:
- [ ] Provider-agnostic interface implemented
- [ ] All three providers (OpenAI, Anthropic, Google) supported
- [ ] Model switching works at runtime
- [ ] Error handling for API failures

### Task 1.3.3: Integrate with existing chat system
**Estimated Time**: 3-4 hours

#### Subtasks:
1. **Update ChatSession class**
   - Replace placeholder `_generate_response()` method
   - Add async support
   - Integrate with LLM backend

2. **Add async UI handling**
   - Non-blocking response generation
   - Progress indicators during LLM calls
   - Cancellation support (Ctrl+C)

3. **Error handling and retries**
   - Exponential backoff for API failures
   - Rate limit handling
   - Network timeout management

#### Acceptance Criteria:
- [ ] Real LLM responses replace placeholder responses
- [ ] Async calls don't block UI
- [ ] Proper error handling for API failures
- [ ] User can cancel long-running operations

### Task 1.3.4: Add dummy mode for testing
**Estimated Time**: 2 hours

#### Subtasks:
1. **Create MockLLMBackend**
   ```python
   class MockLLMBackend(LLMBackend):
       def __init__(self, responses: List[str]):
           self.responses = responses
           self.call_count = 0
   ```

2. **Add --dummy-mode CLI flag**
   - Override backend selection
   - Use mock responses for testing
   - Preserve all other functionality

3. **Create test response sets**
   - Varied response lengths
   - Different content types (text, code, lists)
   - Simulated error conditions

#### Acceptance Criteria:
- [ ] Dummy mode completely bypasses real API calls
- [ ] All UI and command functionality works in dummy mode
- [ ] Suitable for CI/CD testing
- [ ] Configurable mock responses

## Dependencies and Integration Points

### Between Tasks:
- 1.1.1 → 1.1.2: YAML loading must work before full schema
- 1.1.2 → 1.1.3: Schema must be complete before CLI overrides
- 1.2.1 → 1.2.2: Logging system needed before error handling
- 1.3.1 → 1.3.2: Dependencies required before backend implementation
- 1.3.2 → 1.3.3: Backend interface needed before chat integration

### Testing Strategy for Phase 1:
1. **Unit tests for each component**
   - Config loading and validation
   - Backend switching
   - Error handling paths

2. **Integration tests**
   - End-to-end configuration flow
   - Chat session with real/mock backends
   - CLI argument override behavior

3. **Manual testing**
   - Interactive chat sessions
   - Error condition handling
   - Configuration file loading

### Success Metrics:
- [ ] All existing functionality preserved
- [ ] New YAML configuration system working
- [ ] Real LLM integration functional
- [ ] Comprehensive logging available
- [ ] Robust error handling implemented
- [ ] Test coverage >80% for new code
