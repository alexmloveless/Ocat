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

## Productivity System
- **Natural language interface**: Create tasks, events, reminders, and memories using conversational commands
- **Examples**: "create a reminder for next tuesday to call Sam", "add meeting with team on Friday at 2pm"
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

## Development Workflow
- **MANDATORY**: ALWAYS create a new branch before making changes
- **Branch naming**: Use descriptive names like `feat/new-feature`, `fix/bug-description`, `docs/update-docs`
- **Command**: `git checkout -b feature-branch-name` before starting work
- **Commits**: Use `./dev.sh "commit message"` for quality-checked commits
- **Merge**: Merge to main only after testing and review
- **Bug reports**: Use `./.dev/devreq create bug` for any unrelated issues found
- **Quality**: Code must pass black, mypy, and pytest before committing
