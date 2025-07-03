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
- **Config**: `ocat.yaml` - Main configuration file, uses Pydantic for validation

## Code Style Guidelines
- **Types**: Always use type hints for functions and classes
- **Docstrings**: Use numpy format for all functions
- **Comments**: Add inline comments for complex/implicit code sections
- **Imports**: Standard library first, then third-party, then local imports
- **Formatting**: Black formatting (automated via dev.sh)
- **Error handling**: Use custom exceptions from `exceptions.py`
- **Commits**: Use conventional commits format (feat/fix/docs/test/refactor)

## Development Process
- **ALWAYS** use `./dev.sh` for commits (enforces quality checks)
- **Bug reports**: Use `./.dev/devreq create bug` for any unrelated issues found
- **Quality**: Code must pass black, mypy, and pytest before committing
