# Ocat Development - LLM Quick Reference

## 🚀 Getting Started (Read This First!)

### Essential Context Files
1. **`Project/bootstrap.md`** - Complete project requirements and specifications
2. **`Project/implementation_strategy.md`** - Overall development roadmap and phases  
3. **`Project/phase1_tasks.md`** - Detailed breakdown of immediate tasks
4. **`LLM/project_state.md`** - Current development status and history

### Project Core Principles
- **Explicit over implicit** - No catch-all exceptions, clear error handling
- **MVP approach** - Core functionality first, enhancements later
- **Token efficiency** - Minimal updates, focused changes
- **Type hints + docstrings** - All functions must have both (numpy style)

## 📁 Project Structure

```
Ocat/
├── Project/                    # 📋 Planning docs (this folder)
├── LLM/                       # 📝 Development state tracking  
├── src/ocat/                  # 🐍 Main Python package
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # CLI interface & argument parsing
│   ├── config.py             # Configuration management
│   ├── chat.py               # Chat session handling
│   └── repl.py               # REPL interface (stub)
├── tests/                     # 🧪 Test suite
└── pyproject.toml            # 📦 Poetry configuration
```

## 🎯 Current Status Summary

### ✅ Working
- Basic CLI with Rich output
- Configuration system (JSON-based)
- Chat session framework
- Poetry packaging setup

### ❌ Needs Implementation  
- YAML configuration system
- Real LLM integration (LangChain/LangGraph)
- Vector store for memory
- Slash commands system
- Async handling

## 🔧 Key Technologies & Dependencies

### Current Stack
```bash
# Core dependencies
rich = "^14.0.0"              # CLI output and formatting
prompt-toolkit = "^3.0.51"   # Interactive prompts

# Development
pytest = "^8.4.1"            # Testing
black = "^21.5b1"            # Code formatting  
mypy = "^0.910"              # Type checking
ruff = "*"                   # Linting
```

### Target Stack (To Be Added)
```bash
# LLM Integration
langchain                    # LLM framework
langgraph                    # Graph-based LLM workflows
langchain-openai             # OpenAI provider
langchain-anthropic          # Anthropic provider  
langchain-google-genai       # Google provider

# Configuration & Data
pyyaml                       # YAML config files
pydantic                     # Config validation
annoy                        # Vector store (or alternative)
pystache                     # Mustache templating

# Async
aiohttp                      # Async HTTP requests
asyncio                      # Core async framework
```

## 📋 Bootstrap Requirements Checklist

### Configuration (YAML-based)
- [ ] Model selection (gpt-4o-mini default)
- [ ] System prompt files support
- [ ] Vector store settings
- [ ] Display preferences
- [ ] Location aliases

### LLM Integration
- [ ] Provider-agnostic backend (OpenAI, Anthropic, Google)
- [ ] Model switching at runtime
- [ ] Dummy mode for testing

### Vector Store & Memory
- [ ] Real-time conversation storage
- [ ] Similarity search for context
- [ ] Episode/session/thread IDs
- [ ] LangGraph memory integration

### Slash Commands (27 total)
```bash
/attach    /clear     /config    /delete    /exit
/help      /history   /showsys   /vadd      /vdelete  
/vget      /vquery    /vstats    /writecode /writejson
/writemd   /writeresp /model     /showcontext /loglevel
```

### UI/UX Requirements
- Welcome screen with model/profile info
- Configurable line width (80 chars default)
- High contrast for accessibility
- Progress indicators for long operations
- Ctrl+C cancellation support

## 🏗️ Development Workflow

### Before Starting Any Task
1. Read `Project/bootstrap.md` to understand requirements
2. Check current status in `LLM/project_state.md`
3. Review implementation strategy for context
4. Update project status when starting work

### Code Quality Standards
```python
# Required for all functions
def example_function(param: str, config: Config) -> Optional[str]:
    """
    Brief description of what this function does.
    
    Parameters
    ----------
    param : str
        Description of parameter
    config : Config
        Configuration object
        
    Returns
    -------
    Optional[str]
        Description of return value
        
    Raises
    ------
    ConfigError
        When configuration is invalid
    """
    try:
        # Specific error handling - NO catch-all exceptions!
        result = some_operation(param)
        return result
    except SpecificError as e:
        logger.error(f"Operation failed: {e}")
        raise ConfigError(f"Invalid configuration: {param}") from e
```

### Testing Requirements
- Focus on core functionality over exhaustive coverage
- Mock LLM calls for CI/CD
- Integration tests for main workflows
- Manual testing checklist completion

## 🚨 Critical Rules

### NEVER DO
- ❌ Use `except Exception:` or catch-all exceptions
- ❌ Hardcode values that users might want to configure
- ❌ Break existing functionality without user permission
- ❌ Skip type hints or docstrings
- ❌ Commit non-working code

### ALWAYS DO  
- ✅ Use specific exception types
- ✅ Add logging for debugging
- ✅ Validate configurations
- ✅ Update project state documentation
- ✅ Test changes before committing

## 🎯 Next Priority Tasks (Phase 1)

1. **Configuration Overhaul**
   - Replace JSON with YAML + Pydantic
   - Add all bootstrap config fields
   - CLI argument overrides

2. **LLM Backend Integration**
   - Add LangChain/LangGraph dependencies
   - Create provider-agnostic interface
   - Replace placeholder responses

3. **Logging & Error Handling**
   - Structured logging system
   - Specific exception classes
   - Context-aware error messages

## 🔍 Common Development Patterns

### Configuration Access
```python
# Always use config object, never hardcode
response_limit = config.max_tokens
model_name = config.model
```

### Error Handling Pattern
```python
try:
    result = risky_operation()
except SpecificKnownError as e:
    logger.error(f"Known error in operation: {e}")
    raise OcatError("User-friendly message") from e
except AnotherSpecificError as e:
    logger.warning(f"Recoverable error: {e}")
    # Implement fallback behavior
    result = fallback_operation()
```

### Async Pattern (Future)
```python
async def llm_operation():
    try:
        async with progress_indicator():
            result = await llm_backend.generate_response(messages)
        return result
    except asyncio.CancelledError:
        logger.info("Operation cancelled by user")
        raise
```

## 📞 When to Ask for Help

- Unclear requirements from bootstrap specification
- Architecture decisions affecting multiple components  
- Breaking changes that might affect existing functionality
- Performance issues or optimization questions
- Integration challenges between components

## 🧭 Quick Navigation

- **Full requirements**: `Project/bootstrap.md`
- **Implementation plan**: `Project/implementation_strategy.md`  
- **Current tasks**: `Project/phase1_tasks.md`
- **Project status**: `LLM/project_state.md`
- **Code**: `src/ocat/`
- **Tests**: `tests/`

Remember: Ocat is a chat client with memory capabilities, built for modularity and extensibility. Keep the end user experience simple while maintaining sophisticated backend capabilities.
