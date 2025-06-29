# Ocat 🐱

An interactive LLM Chat CLI tool that provides a beautiful command-line interface for chatting with Large Language Models.

## Features

- 🎨 **Rich Terminal UI** - Beautiful formatting with colors, panels, and markdown support
- 📝 **Interactive Chat** - Seamless conversation flow with history and auto-suggestions
- ⚙️ **Configurable** - Support for multiple LLM providers and customizable settings
- 🔧 **CLI-First** - Designed for developers who love the terminal
- 🚀 **Easy to Use** - Simple installation and intuitive commands

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ocat

# Install dependencies
poetry install

# Run the application
poetry run ocat
```

### Using pip

```bash
pip install ocat
ocat
```

## Quick Start

1. **Run Ocat**:
   ```bash
   ocat
   ```

2. **Start chatting**:
   ```
   🐱 > Hello! How are you today?
   ```

3. **Use built-in commands**:
   - `help` or `h` - Show available commands
   - `clear` - Clear the screen
   - `exit`, `quit`, or `q` - Exit the application

## Configuration

Ocat can be configured through:

1. **Configuration file** (`~/.ocat/config.json`):
   ```json
   {
     "model": "gpt-3.5-turbo",
     "api_key": "your-api-key",
     "max_tokens": 2048,
     "temperature": 0.7,
     "system_prompt": "You are a helpful AI assistant."
   }
   ```

2. **Environment variables**:
   ```bash
   export OCAT_API_KEY="your-api-key"
   export OCAT_MODEL="gpt-4"
   export OCAT_MAX_TOKENS=2048
   export OCAT_TEMPERATURE=0.7
   ```

3. **Command line arguments**:
   ```bash
   ocat --model gpt-4 --config custom-config.json
   ```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `model` | LLM model to use | `gpt-3.5-turbo` |
| `api_key` | API key for the LLM service | `None` |
| `api_base` | Base URL for the API | `None` |
| `max_tokens` | Maximum tokens in responses | `2048` |
| `temperature` | Response creativity (0.0-1.0) | `0.7` |
| `system_prompt` | Default system message | `"You are a helpful AI assistant."` |

## Command Line Options

```bash
ocat --help
```

Available options:
- `--version` - Show version information
- `--config PATH` - Specify configuration file path
- `--model MODEL` - Override the LLM model
- `--debug` - Enable debug mode

## Development

### Prerequisites

- Python 3.9+
- Poetry

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd ocat

# Install dependencies
poetry install

# Install pre-commit hooks (optional)
pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=ocat

# Run specific test file
poetry run pytest tests/test_cli.py
```

### Code Quality

```bash
# Format code with black
poetry run black src/ tests/

# Type checking with mypy
poetry run mypy src/

# Linting with ruff
poetry run ruff check src/ tests/
```

## Project Structure

```
ocat/
├── src/
│   └── ocat/
│       ├── __init__.py      # Package initialization
│       ├── cli.py           # Main CLI interface
│       ├── config.py        # Configuration management
│       └── chat.py          # Chat session handling
├── tests/
│   ├── __init__.py
│   ├── test_cli.py          # CLI tests
│   └── test_config.py       # Configuration tests
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`poetry run pytest && poetry run black . && poetry run mypy .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Support for multiple LLM providers (OpenAI, Anthropic, local models)
- [ ] Conversation persistence and history
- [ ] Plugin system for custom commands
- [ ] Conversation templates and presets
- [ ] File upload and processing capabilities
- [ ] Integration with popular AI services

## Support

If you encounter any issues or have questions:

1. Check the [documentation](README.md)
2. Search [existing issues](../../issues)
3. Create a [new issue](../../issues/new) if needed

---

Made with ❤️ for terminal enthusiasts and AI developers
