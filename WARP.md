# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common commands

- Install deps (Poetry):
  - poetry install
- Run app (Poetry):
  - poetry run ocat
- Dev cycle (format + type-check + tests + commit):
  - ./dev.sh "feat: message"
- Run all tests:
  - poetry run pytest
- Run a single test file/test:
  - poetry run pytest tests/test_cli.py::test_cli_help
- Format:
  - poetry run black src tests
- Type check:
  - poetry run mypy src
- Lint (ruff):
  - poetry run ruff check src tests

Docker:
- Build images:
  - docker compose --profile production build
- Run CLI (prod image):
  - docker compose run --rm ocat
- Run dev image with live reload mounts:
  - docker compose --profile development up ocat-dev
- Headless vector operations:
  - docker compose run --rm --profile headless ocat-headless --vector-store-stats
  - docker compose run --rm --profile headless ocat-headless --add-to-vector-store path/to.txt
  - docker compose run --rm --profile headless ocat-headless --query-vector-store "query"

Configuration:
- Primary sources in priority order: CLI > env vars > YAML config > defaults
- Default config search paths: ~/.ocat/config.yaml, ./ocat.yaml, ./.ocat.yaml
- Useful env vars: OCAT_MODEL, OCAT_MAX_TOKENS, OCAT_TEMPERATURE, OCAT_VECTOR_STORE_PATH, OCAT_LOG_LEVEL, OCAT_PROFILE_NAME, OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY

## Project architecture (big picture)

Top-level runtime flow:
- Entry points: src/ocat/__main__.py and src/ocat/cli.py
  - cli.py parses args, loads Config, handles headless vector ops, starts interactive loop
- Chat core: src/ocat/chat.py
  - ChatSession orchestrates: slash commands, LLM backend, vector memory, productivity and file tool integrations
- Commands system: src/ocat/commands/
  - __init__.py exposes a registry, BaseCommand, @command decorator
  - parser.py parses and executes /commands
  - core/help/file/history/context/vector/clipboard/productivity commands are auto-registered by import side-effects
- Backends: src/ocat/backends/
  - factory.py detects provider from model (OpenAI/Anthropic/Google) and constructs backend; Mock backend supports dummy mode
- Config: src/ocat/config.py
  - Pydantic models; loads from YAML, env, CLI overrides; includes display/logging/vector/embedding settings
- Vector memory: src/ocat/vector_store.py
  - ConversationVectorStore using Chroma (DuckDB persistence) with an Exchange dataclass; integrates LangGraph MemorySaver checkpoints; provides add/query/get/delete/stats APIs
- Integrations:
  - Productivity: src/ocat/productivity/ (integration/models/storage/tools)
  - File tools: src/ocat/file_tools/ (integration/models/storage/tools)
- Utilities: src/ocat/utils/ (logging, path utils)
- Tests: tests/ cover CLI, commands, config, vector store and utilities

Key runtime behaviors to know:
- System prompts: base_prompt.md (packaged) + optional user prompt files, with current timestamp injection; can be overridden via config
- Vector context: recent exchanges summarized and optionally injected into the LLM request; context display mode controlled inside ChatSession
- Dummy mode: --dummy-mode switches to MockLLMBackend with progress indicator
- Clipboard ops: /copy strips markdown and uses platform-specific clipboard tools

## Development workflow (repo-specific)

- Always create a new branch before changes:
  - git checkout -b feat/short-name
- Use ./dev.sh to run black + mypy + pytest and commit with a Conventional Commit message
- Conventional commits are used (feat/fix/docs/test/refactor ...)
- Tests focus on core functionality; keep changes minimal MVP-style

## Docker notes

- docker-compose.yml defines three profiles: production (ocat), development (ocat-dev with src/tests bind-mounted read-only), headless (ocat-headless)
- Volumes persist vector stores and user config (ocat_vectors*, ocat_config*)
- Environment is passed via .env; containers set OCAT_VECTOR_STORE_PATH and disable telemetry/tokenizer parallelism

## Important docs to read first

- README.md (usage, Docker quick start, config examples)
- DEVELOPMENT.md (LLM-oriented dev workflow, mandatory ./dev.sh usage, bug report protocol)
- .dev/README.md (dev request manager: ./.dev/devreq create/list/show/update/complete)
- Project/RELEASE.md (release steps)

## Running a targeted test quickly

- Single test function:
  - poetry run pytest tests/test_commands.py::TestCommandParser::test_parse_command
- Match by keyword (-k):
  - poetry run pytest -k "vector and vstats"

## Environment assumptions

- Python managed via Poetry (pyproject.toml); tests run with pytest; formatting via black; type-checking via mypy; optional ruff lint
- Conda environment file exists (environment.yml) if you prefer conda; Dockerfile provides dev and prod targets

