# Ocat 🐱

A vibes-only LLM chat CLI that I built for my own weird workflow. You might like it too.

## What it does

- **Chat with LLMs**: OpenAI, Anthropic, Google, Ollama - whatever floats your boat
- **Productivity stuff**: Tasks, events, reminders, memory - all in natural language  
- **File operations**: Read, write, search files directly from chat
- **Vector memory**: Remembers your conversations and context via ChromaDB
- **Terminal vibes**: Rich UI with colors and markdown because life's too short for ugly CLIs

## Installation

```bash
pip install ocat
ocat
```

That's it. No Docker needed, no fancy setup. Just install and go.

## Basic Commands

- `/help` - Get help (or just ask "how do I...")
- `/clear` - Clear the screen
- `/exit` or `/quit` - Leave the chat
- `/config` - Show current settings
- `/context` - Toggle showing conversation context

## Productivity Features

```bash
🐱 > create a task to review the quarterly report by friday
🐱 > add meeting with sarah on tuesday at 2pm  
🐱 > set reminder to call mom tomorrow at 5pm
🐱 > save that the wifi password is "coffee123"
🐱 > show my tasks for this week
🐱 > mark task001 as done
```

## File Operations

```bash
🐱 > read my config.yaml and explain what it does
🐱 > write a hello world script to hello.py
🐱 > search for "TODO" in all my python files
🐱 > list files in the docs folder
```

## Getting Help

Type `/help` for the main help menu, or `/help <topic>` for specific areas:
- `/help commands` - All available commands
- `/help productivity` - Tasks, events, reminders
- `/help files` - File operations and shortcuts  
- `/help config` - Configuration options

Or just ask naturally: "how do I create a task?" or "what can you do?"

## Configuration

Ocat creates a config file at `~/.ocat/ocat.yaml` on first run. Edit it or set environment variables like `OCAT_OPENAI_API_KEY`. Use `/help config` for details.

## Development & Contributing

This was vibe-coded expressly for my personal use, so it's not open for PRs and future development is entirely at my whim. That said, anyone's free to fork the repo and extend/improve as they wish. Attribution preferred but not mandatory.

If you find bugs or have ideas, feel free to open issues - I might get around to them if they align with my needs.

## License

MIT - do whatever you want with it.

---

*Made with caffeine and stubbornness*
