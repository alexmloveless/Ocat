# AGENT.md - Ocat Development Guide

## Build/Lint/Test Commands
- **Development cycle**: `./dev.sh "feat: commit message"` (runs black, mypy, pytest, git add, git commit)
- **Run tests**: `poetry run pytest` (all tests) or `poetry run pytest tests/test_cli.py` (single test file)
- **Format code**: `poetry run black src/ tests/`
- **Type check**: `poetry run mypy src/`
- **Lint**: `poetry run ruff check src/ tests/`
- **Run application**: `poetry run ocat`

## Architecture & Structure
- **Main app**: `src/ocat/` - CLI interface (`cli.py`), chat functionality (`chat.py`), configuration (`config.py`)
- **Commands**: `src/ocat/commands/` - Built-in chat commands and handlers
- **Backends**: `src/ocat/backends/` - LLM provider integrations (OpenAI, Anthropic, Google)
- **Vector store**: `src/ocat/vector_store.py` - Document storage and retrieval with ChromaDB
- **Productivity**: `src/ocat/productivity/` - Task, event, reminder, and memory management system
- **Config**: `ocat.yaml` - Main configuration file, uses Pydantic for validation

## AI Tool Integration
- **File Operations**: AI has direct access to read, write, search, and manage files through pydantic-ai tools
- **Productivity System**: AI can create tasks, events, reminders, and memories using conversational commands
- **Natural language interface**: Users can ask "read myfile.md and summarize" and AI will use file tools directly
- **Examples**: "create a reminder for next tuesday to call Sam", "read config.yaml and explain the settings"
- **Storage**: Uses same ChromaDB vector store as conversation history
- **Features**: CRUD operations, pseudo IDs (task001, event001), status tracking, flexible date parsing

## Code Style Guidelines
- **Types**: Always use type hints for functions and classes
- **Docstrings**: Use numpy format for all functions
- **Comments**: Add inline comments for complex/implicit code sections
- **Imports**: Standard library first, then third-party, then local imports
- **Formatting**: Black formatting (automated via dev.sh)
- **Error handling**: Use custom exceptions from `exceptions.py`
- **Commits**: Use conventional commits format (feat/fix/docs/test/refactor)

## Help System
- **Location**: `src/ocat/commands/help_system.py` - Centralized help content management
- **Structure**: Organized sections (commands, productivity, files, chat, config, tips)
- **Usage**: `/help` for overview, `/help <section>` for specific topics
- **Adding sections**: Use `add_help_section(key, title, content, aliases)` function
- **Content format**: Markdown with clear headers, code blocks, and examples
- **Aliases**: Support multiple keywords per section (e.g., "tasks" and "productivity")

### Adding New Help Content
```python
from src.ocat.commands.help_system import add_help_section

# Add new section
add_help_section(
    key="new_feature",
    title="New Feature Guide", 
    content="""# 🚀 **New Feature**
    
    Detailed markdown content here...
    """,
    aliases=["feature", "new"]
)
```

## Development Workflow
- **MANDATORY**: ALWAYS create a new branch before making changes
- **Branch naming**: Use descriptive names like `feat/new-feature`, `fix/bug-description`, `docs/update-docs`
- **Command**: `git checkout -b feature-branch-name` before starting work
- **Commits**: Use `./dev.sh "commit message"` for quality-checked commits
- **Merge**: Merge to main only after testing and review
- **Bug reports**: Use `./.dev/devreq create bug` for any unrelated issues found
- **Quality**: Code must pass black, mypy, and pytest before committing
