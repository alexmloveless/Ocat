"""
Enhanced help system for Ocat.

Provides organized, markdown-formatted help with section refinement capabilities.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class HelpSection:
    """Represents a help section with markdown content."""

    title: str
    content: str
    aliases: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


class HelpRegistry:
    """Registry for organizing and managing help content."""

    def __init__(self):
        self._sections: Dict[str, HelpSection] = {}
        self._initialize_help_content()

    def register_section(self, key: str, section: HelpSection) -> None:
        """Register a help section."""
        self._sections[key] = section
        # Also register aliases
        for alias in section.aliases:
            self._sections[alias] = section

    def get_section(self, key: str) -> Optional[HelpSection]:
        """Get a help section by key or alias."""
        return self._sections.get(key.lower())

    def get_overview(self) -> str:
        """Get the main help overview."""
        return self._generate_overview()

    def list_sections(self) -> List[str]:
        """List all available section keys (excluding aliases)."""
        seen = set()
        sections = []
        for key, section in self._sections.items():
            if section not in seen:
                sections.append(key)
                seen.add(section)
        return sorted(sections)

    def _initialize_help_content(self):
        """Initialize all help content sections."""

        # Overview section
        overview = HelpSection(
            title="Ocat Help Overview",
            content="""# 🐱 **Ocat** - AI Chat Assistant

**Ocat** is an intelligent chat assistant with productivity features and file management.

## 📚 **Help Sections**
- `/help commands` - All slash commands
- `/help websearch` - Web search functionality
- `/help speak` - Text-to-speech functionality
- `/help productivity` - Tasks, lists, and memory management
- `/help files` - File operations and location aliases
- `/help chat` - Chat features and conversation management
- `/help config` - Configuration and setup
- `/help tips` - Usage tips and best practices

## 🚀 **Quick Examples**
```
/st                    # Show open tasks
/web "latest AI news"  # Search web and analyze results
/speak                 # Speak last response
/file read config.yaml # Read a file
/locations             # Show location aliases
"create a task to review the report due Friday"
"what files are in my current directory?"
```
""",
            aliases=["overview", "main"],
        )
        self.register_section("overview", overview)

        # Commands section
        commands = HelpSection(
            title="Slash Commands Reference",
            content="""# 🔧 **Slash Commands**

## 📋 **Core Commands**
- `/help [section]` - Show help
- `/clear` - Clear conversation history
- `/exit`, `/quit`, `/q` - Exit
- `/history [n]` - Show chat history
- `/showcontext [on|off|summary]` - Control context display

## 📁 **File Operations**
- `/file read <path>` - Read and display file
- `/file write <path> <content>` - Write content to file
- `/file append <path> <content>` - Append to file
- `/file list [path]` - List directory contents
- `/file search <pattern> [path]` - Search files/content
- `/file tree [path] [depth]` - Show directory tree
- `/pwd` - Show current directory
- `/cd <path>` - Change directory
- `/ls [path]` - List directory (alias for `/file list`)
- `/cat <path>` - Display file (alias for `/file read`)
- `/mkdir <path>` - Create directory

## 📎 **File Export/Attach**
- `/attach <file1> [file2...]` - Attach up to 5 files as context
- `/writecode <filepath>` - Extract code from last response
- `/writejson <filepath>` - Export conversation to JSON
- `/writemd <filepath>` - Export conversation to Markdown
- `/writeresp <filepath> [format]` - Export last exchange
- `/append <path> ["text"]` - Append text or last exchange

## 📍 **Location Aliases**
- `/locations` - Show configured location aliases
- Use `alias:filename` syntax in file commands

## 📋 **Clipboard**
- `/copy` - Copy last response to clipboard

## 🗃️ **Vector Store**
- `/vadd <text>` - Add text to vector store
- `/vdelete <id>` - Delete document by ID
- `/vget <id|session|thread>` - Retrieve exchanges
- `/vquery <query> [k]` - Query similar exchanges
- `/vstats` - Show vector store statistics

## 🔊 **Text-to-Speech**
- `/speak [voice] [model]` (alias: `/s`) - Speak last response
- `/speaklike "instructions" [voice] [model]` (alias: `/sl`) - Speak with custom instructions

## 🌐 **Web Search**
- `/web "search query" [engine]` - Search the web and add results to context

## 💭 **Memory & Productivity**
- `/remember <type> <text>` - Store information
- `/st [category|priority:<level>]` - Show open tasks
- `/list [listname]` - Show lists/list items
- `/timelog` or `/tl` - Show/export timelog entries

## 🔧 **Model & Settings**
- `/model <model_name>` - Change LLM model
- `/showsys` - Show system prompt
- `/loglevel <level>` - Set logging level
- `/config` - Show configuration
- `/delete [n]` - Remove recent exchanges
""",
            aliases=["cmd", "command", "slash"],
        )
        self.register_section("commands", commands)

        # Productivity section
        productivity = HelpSection(
            title="Productivity System Guide",
            content="""# 📊 **Productivity System**

Manage tasks, lists, memories, and time tracking using natural language.

## ⏰ **Timelog**
Track time spent on projects with flexible entry and powerful reporting.

### Commands:
- `/timelog` or `/tl` - Show all timelog entries
- `/timelog -p <project>` or `/timelog --project=<project>` - Filter by project
- `/timelog -s <date>` or `/timelog --start=<date>` - Filter from date
- `/timelog -e <date>` or `/timelog --end=<date>` - Filter to date
- `/timelog -g <project|week|month>` or `/timelog --group=<project|week|month>` - Group entries
- `/timelog -o <csv|json|yaml> -f <filename>` - Export to file

### Natural Language Examples:
```
"i worked half day today on project nx with a note that I presented to the board"
"log a half day against project alpha for yesterday"
"worked all day on project beta on 6th June 25"
"log 3 hours on database optimization today"
"show time for project alpha last week"
"save the time for the past month for project alpha to alpha.csv"
```

### Features:
- Flexible time entry: "half day" (4h), "full day" (8h), or exact hours
- Smart date parsing: "today", "yesterday", "6th June", etc.
- Project-based tracking
- Optional notes for context
- Export capabilities (CSV, JSON, YAML)
- Grouping by project, week, or month
- Pseudo IDs (timelog001, timelog002, etc.)

### Command Examples:
```
/timelog                           # All entries, most recent first
/timelog -p alpha                  # Only project alpha entries
/timelog -s "last week"            # Entries from last week
/timelog -g project                # Group by project with totals
/timelog -g month                  # Group by month
/timelog -p alpha -o csv -f alpha_time.csv  # Export alpha project to CSV
```

## ✅ **Tasks**
Create and manage to-do items with priorities and categories.

### Commands:
- `/st` - Show all open tasks (active & in-progress)
- `/st -s <field>` or `/st --sort=<field>` - Sort by: created, priority, category, due, id, status
- `/st -o <asc|desc>` or `/st --order=<asc|desc>` - Sort order (default: desc for created, asc for others)
- `/st -p <level>` or `/st --priority=<level>` - Filter by priority (urgent/high/medium/low)
- `/st -c <name>` or `/st --category=<name>` - Filter by category
- `/st -S <status>` or `/st --status=<status>` - Filter by status (active/in_progress/completed)

### Legacy Syntax (still supported):
- `/st <category>` - Show tasks in specific category  
- `/st priority:<level>` - Show tasks by priority

### Natural Language Examples:
```
"create a task to review the quarterly report"
"add high priority task to call client by tomorrow"
"update task001 status to completed"
"show me tasks for project-alpha"
```

### Command Examples:
```
/st                                  # All open tasks, newest first
/st -s priority                      # Sort by priority (urgent first)
/st -s due -o asc                    # Sort by due date, earliest first
/st -p high                          # Only high priority tasks
/st -c work -s due                   # Work tasks sorted by due date
/st -S completed -s created          # Completed tasks, newest first

# Long form also works:
/st --sort=priority --order=desc     # Same as -s priority -o desc
/st --category=work --priority=high  # Same as -c work -p high
```

### Features:
- Priority levels: urgent, high, medium, low
- Categories for organization
- Status tracking: active, in_progress, completed
- Due dates with flexible parsing
- Pseudo IDs (task001, task002, etc.)

### Direct Task Commands (bypass AI):
- `/at <category> <priority> "<task text>"` - Add task directly without LLM
- `/ct <task_id>` - Complete task directly without LLM

#### Examples:
```
/at work high "finish quarterly report"
/at personal medium "book dentist appointment"
/ct T123                               # Complete task T123
```

## 📝 **Lists**
Organize collections of items in named lists.

### Commands:
- `/list` - Show all lists with item counts
- `/list <listname>` - Show items in specific list

### Examples:
```
"add milk and bread to shopping list"
"create list item 'read 1984' in books list"
"add item 'visit Paris' to travel bucket list"
"show items in shopping list"
```

### Features:
- Named lists group related items
- Categories within lists
- Archive items instead of deleting
- Status tracking per item

## 🧠 **Memory**
Store information for later recall.

### Commands:
- `/remember <type> <text>` - Store information

### Examples:
```
"remember that Sarah prefers tea over coffee"
"save to memory: wifi password is SecureNet123"
"remember client prefers morning meetings"
```

### Features:
- Free-form text storage
- Searchable across all content
- Categorization and tagging
- Timestamped entries

## 🔍 **Natural Language Interface**
All productivity features work through conversation:
```
"create a task to finish the presentation due Friday"
"show me my high priority tasks"
"add eggs to my shopping list"
"what tasks do I have for next week?"
```

## 💡 **Tips**
- Use natural language - the AI understands context
- Pseudo IDs make referencing easy (task001, list001)
- Search works across all productivity content
- AI integration means your assistant knows your schedule
""",
            aliases=[
                "tasks",
                "lists",
                "memories",
                "productivity",
                "prod",
            ],
        )
        self.register_section("productivity", productivity)

        # Files section
        files = HelpSection(
            title="File Operations Guide",
            content="""# 📁 **File Operations**

File management with location aliases for easy access.

## 📖 **Basic File Commands**

### **Read/Write/Edit**
```
/file read myfile.txt              # Read file
/file write notes.txt "Hello"      # Write to file
/file append logs.txt "New entry"  # Append to file
```

### **Directory Operations**
```
/file list                # List current directory
/file list src/           # List specific directory
/file tree               # Show directory tree
/file tree src/ 2        # Tree with max depth 2
/pwd                     # Show current directory
/cd <path>               # Change directory
/mkdir <path>            # Create directory
```

### **Search**
```
/file search "function"     # Search text in files
/file search "*.py"         # Search file patterns
/file search "error" src/   # Search in directory
```

### **Aliases (shortcuts)**
```
/ls [path]    # Same as /file list
/cat <path>   # Same as /file read
```

## 📍 **Location Aliases**

Simplify paths with custom aliases configured in `ocat.yaml`:

```yaml
locations:
  docs: "~/Documents"
  config: "~/.config/app"
  logs: "/var/log"
```

### **Usage**
```
/locations                      # Show all aliases
/file read docs:readme.md       # Use alias
/file list config:              # List alias directory
```

## 📎 **Export/Attach**

### **Export Conversations**
```
/writejson chat.json       # Export to JSON
/writemd chat.md           # Export thread to Markdown (no system prompt)
/w chat.md                 # Alias for /writemd
/writemdall chat.md        # Export full conversation with system prompt
/writeresp last.md         # Export last exchange
/writecode code.py         # Extract code blocks
```

### **File Attachment**
```
/attach file1.txt file2.py    # Attach files to chat
/append notes.md "text"       # Append text to file
/append notes.md              # Append last exchange
```

## 💡 **Tips**
- Use location aliases for frequently accessed paths
- Working directory persists during session
- File operations work with both absolute and relative paths
- AI can directly read/search files through natural language
""",
            aliases=["file", "files", "location", "locations", "paths"],
        )
        self.register_section("files", files)

        # Chat section
        chat = HelpSection(
            title="Chat Features Guide",
            content="""# 💬 **Chat Features**

Conversation management and AI interaction.

## 🤖 **AI Models**
Supports multiple AI providers:
- **OpenAI**: GPT-4, GPT-3.5-turbo models
- **Anthropic**: Claude-3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro models

Configure in `ocat.yaml` or use environment variables.

## 🔧 **AI Tool Access**
The AI can directly access tools through natural language:

### **File Operations**
```
"read config.yaml and explain the settings"
"what files are in my current directory?"
"search for Python files containing 'error'"
"create a summary of the docs directory"
```

### **Productivity Management**
```
"create a task to review the report due Friday"
"show me my high priority tasks"
"add milk to my shopping list"
"what do I have scheduled for next week?"
```

## 🗣️ **Conversation Management**

### **History & Context**
```
/history [n]                    # Show chat history
/showcontext [on|off|summary]   # Control context display
/clear                          # Clear conversation history
```

### **Model Control**
```
/model <model_name>   # Change AI model
/showsys              # Show system prompt
/config               # Show configuration
```

## 📋 **Clipboard & Export**
```
/copy                 # Copy last response
/writejson chat.json  # Export conversation to JSON
/writemd chat.md      # Export thread to Markdown (alias: /w)
/writemdall chat.md   # Export full conversation with system prompt
```

## ⌨️ **Input & Navigation**
- Type naturally and press Enter
- **↑/↓ arrows** navigate command history
- **Ctrl+C** interrupts current response
- **Ctrl+D** exits application

## 💡 **Tips**
- Mix natural chat with slash commands
- AI remembers conversation context
- Ask about your productivity data naturally
- Use Ctrl+C to stop long responses
""",
            aliases=["conversation", "ai", "models", "chat"],
        )
        self.register_section("chat", chat)

        # Config section
        config = HelpSection(
            title="Configuration Guide",
            content="""# ⚙️ **Configuration**

Customize Ocat through configuration files and environment variables.

## 📄 **Configuration File**
Main config: `ocat.yaml`

### **Basic Structure**
```yaml
# LLM Configuration
llm:
  provider: "openai"        # openai, anthropic, google
  model: "gpt-4"           # Model name
  api_key: "${OCAT_API_KEY}" # Environment variable

# Location Aliases
locations:
  docs: "~/Documents"
  config: "~/.config/ocat"
  logs: "/var/log/ocat"

# Vector Store Settings
vector_store:
  collection_name: "ocat_main"
  persist_directory: "./vector_stores"
```

## 🔑 **Environment Variables**

### **API Keys**
```bash
export OCAT_API_KEY="your-api-key"          # Primary key
export OPENAI_API_KEY="your-openai-key"     # OpenAI
export ANTHROPIC_API_KEY="your-claude-key"  # Anthropic
export GOOGLE_API_KEY="your-google-key"     # Google
```

### **Configuration**
```bash
export OCAT_CONFIG_PATH="/custom/ocat.yaml"
export OCAT_LOG_LEVEL="DEBUG"
export OCAT_VECTOR_PATH="/custom/vectors"
```

## 🚀 **Quick Setup**

1. **Install**: `poetry install` or `pip install -r requirements.txt`
2. **Set API Key**: `export OCAT_API_KEY="your-key"`
3. **Run**: `poetry run ocat` or `ocat`

## 🛠️ **Troubleshooting**

### **Common Issues**
- **API key errors**: Check environment variables
- **Config not found**: Verify file path and permissions
- **Vector store issues**: Check disk space
- **Model errors**: Verify model name and provider

### **Debug Mode**
```bash
export OCAT_LOG_LEVEL="DEBUG"
ocat
```

## 💡 **Tips**
- Start with defaults, customize gradually
- Use environment variables for secrets
- Test with `/config` and `/vstats` commands
""",
            aliases=["configuration", "setup", "config", "settings"],
        )
        self.register_section("config", config)

        # Tips section
        tips = HelpSection(
            title="Usage Tips & Best Practices",
            content="""# 💡 **Tips & Best Practices**

## 🚀 **Getting Started**

### **First Steps**
1. Set API key: `export OCAT_API_KEY="your-key"`
2. Start chatting naturally
3. Try: `"create a task to learn Ocat"`
4. Explore: `/help commands`

### **Essential Commands**
```
/st                  # Show open tasks
/locations           # Set up location aliases
/history             # Review conversation
/copy                # Copy AI responses
```

## 📊 **Productivity Workflow**

### **Daily Planning**
```
"show me my tasks for today"
"create a task to review the quarterly report"
"add milk to my shopping list"
/st priority:urgent
```

### **Project Management**
```
"create high priority task: define requirements"
"remember: project deadline is December 15th"
"show me all tasks for project-alpha"
/list project-tasks
```

## 📁 **File Management**

### **Efficient File Access**
Set up location aliases in `ocat.yaml`:
```yaml
locations:
  proj: "~/work/current-project"
  docs: "~/Documents"
```

Then use shortcuts:
```
/file read proj:readme.md
/file list docs:
"read config.yaml and explain the settings"
```

## 💬 **Chat Optimization**

### **Effective Communication**
- Be specific: "Debug the auth error in login.py"
- Provide context: Share relevant file contents  
- Ask follow-ups: Build on previous responses
- Use productivity data: "Based on my tasks, what's priority?"

### **Managing Conversations**
```
/clear               # Start fresh when needed
/history 10          # Review recent discussion
/showcontext off     # Reduce context display
```

## ⚡ **Efficiency Tips**

### **Keyboard Shortcuts**
- **↑/↓**: Navigate command history
- **Ctrl+C**: Interrupt long responses
- **Ctrl+D**: Quick exit

### **Natural Language Power**
```
"create a task to finish the presentation due Friday"
"what files are in my current directory?"
"show me my high priority tasks"
"add eggs and milk to my shopping list"
"remember that the client prefers morning meetings"
```

## 🛠️ **Troubleshooting**

### **Common Issues**
- **Slow responses**: Check internet and API limits
- **Missing data**: Use `/vstats` to check storage
- **Command errors**: Verify syntax with `/help commands`
- **File access**: Check paths and permissions

### **Performance Tips**
- Use `/clear` to start fresh conversations
- Set up location aliases for frequent paths
- Use specific queries rather than broad searches
- Check `/config` for current settings

## 🌟 **Pro Tips**
- Combine natural language with slash commands seamlessly
- Use AI to interpret your productivity data
- Set up location aliases for frequent file access
- Build consistent productivity workflows
- Experiment with organization patterns
""",
            aliases=["tip", "tips", "best", "practices", "workflow"],
        )
        self.register_section("tips", tips)

        # TTS (Text-to-Speech) section
        tts = HelpSection(
            title="Text-to-Speech Commands",
            content="""# 🔊 **Text-to-Speech Commands**

Convert assistant responses to speech using OpenAI's TTS API and play them directly through your terminal.

## 🎵 **Commands**

### `/speak [voice] [model]` (alias: `/s`)
Convert the last assistant response to speech and play it.

**Examples:**
```
/speak                    # Use default voice and model
/s                        # Same as /speak (alias)
/speak nova               # Use nova voice with default model  
/speak fable tts-1-hd     # Use fable voice with tts-1-hd model
```

### `/speaklike "instructions" [voice] [model]` (alias: `/sl`)
Convert the last assistant response to speech with custom instructions for how it should be spoken.

**Examples:**
```
/speaklike "speak slowly and clearly"
/sl "speak in an excited tone"
/speaklike "speak in an excited tone" nova
/speaklike "read this like a news anchor" fable tts-1-hd
```

## 🎤 **Available Voices**

- **alloy** - Balanced, neutral voice suitable for most content
- **echo** - Clear, professional voice great for documentation
- **fable** - Warm, expressive voice perfect for storytelling
- **nova** - Bright, energetic voice (default) - friendly and conversational
- **onyx** - Deep, authoritative voice ideal for serious content
- **shimmer** - Soft, gentle voice with a calming tone

## 🎛️ **Available Models**

- **tts-1** - Standard quality, faster generation (default)
- **tts-1-hd** - Higher quality audio, slower generation

## ⚙️ **Configuration**

Configure TTS settings in your `ocat.yaml` file:

```yaml
tts:
  enabled: true              # Enable/disable TTS functionality
  voice: "nova"              # Default voice (see available voices above)
  model: "tts-1"             # Default model (tts-1 or tts-1-hd)
  audio_dir: "/tmp"          # Directory to store MP3 files
```

## 🔑 **Prerequisites**

### **1. OpenAI API Key**
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### **2. Audio Player**
Install a compatible audio player for your system:

**Linux:**
```bash
# Install one of these players:
sudo apt install mpg123        # Recommended
sudo apt install ffmpeg        # Includes ffplay
sudo apt install alsa-utils    # Includes aplay
sudo apt install pulseaudio-utils  # Includes paplay
```

**macOS:**
- `afplay` is built-in (no installation needed)

**Windows:**
- Uses built-in `start` command (no installation needed)

## 📁 **Audio File Management**

- MP3 files are saved to the directory specified in `tts.audio_dir`
- Files are named with timestamps: `ocat_tts_<timestamp>.mp3`
- Files are played immediately after generation
- Audio files remain on disk for later playback if needed

## 🧹 **Text Processing**

The TTS system automatically cleans responses for optimal speech:

- **Code blocks** → Replaced with "[code block]"
- **Markdown formatting** → Stripped (bold, italic, headers, links)
- **List markers** → Removed
- **Extra whitespace** → Normalized

This ensures clean, natural-sounding speech without markdown artifacts.

## 📋 **Usage Examples**

### **Basic Usage**
```
User: What is Python?
Assistant: Python is a high-level programming language known for its simplicity...
User: /speak
🔊 Generating speech using nova voice...
🎵 Audio saved to: /tmp/ocat_tts_1234567890.mp3
🎧 Playing audio...
✅ Audio playback completed
```

### **Custom Voice**
```
User: /speak fable
🔊 Generating speech using fable voice...
```

### **Custom Instructions**
```
User: /speaklike "speak like a helpful teacher explaining to a student"
🔊 Generating speech using nova voice...
```

### **Full Customization**
```
User: /sl "read this dramatically like a movie narrator" onyx tts-1-hd
🔊 Generating speech using onyx voice...
```

## ❌ **Error Handling**

Common errors and solutions:

**"TTS is disabled in configuration"**
- Set `tts.enabled: true` in your `ocat.yaml` file

**"OPENAI_API_KEY environment variable not set"**
- Set your API key: `export OPENAI_API_KEY="your-key-here"`

**"No suitable audio player found"**
- Install an audio player: `sudo apt install mpg123` (Linux)

**"No assistant response found to speak"**
- Make sure there's a recent assistant response in the conversation

**"Invalid voice 'xyz'"**
- Use one of: alloy, echo, fable, nova, onyx, shimmer

**"Invalid model 'xyz'"**
- Use either: tts-1, tts-1-hd

## 🚀 **Performance Tips**

- **tts-1** is faster for quick responses
- **tts-1-hd** provides better audio quality for important content
- Large responses may take longer to generate
- Audio playback happens asynchronously
- Check your system volume if audio doesn't play

## 🎯 **Best Practices**

1. **Start with defaults** - Try `/speak` first to test your setup
2. **Choose appropriate voices** - nova for casual, onyx for serious content
3. **Use custom instructions** - Add personality with `/speaklike`
4. **Test your audio setup** - Verify volume and speakers work
5. **Check storage space** - Audio files accumulate in the configured directory

## 💡 **Pro Tips**

- Use `/s` as a quick alias for `/speak`
- Combine with other commands: first get info, then speak it
- Perfect for accessibility and hands-free operation
- Great for reviewing long responses while doing other tasks
- Try different voices to find your preference
""",
            aliases=["speak", "tts", "speech", "audio", "voice"],
        )
        self.register_section("tts", tts)

        # Web Search section
        web_search = HelpSection(
            title="Web Search Guide",
            content="""# 🌐 **Web Search**

Search the web and integrate results directly into your conversation context.

## 📝 **Basic Usage**
```bash
/web "search query"                 # Search using default engine
/web "search query" duckduckgo      # Specify search engine
/web "latest AI news" google        # Use Google search
/web "python asyncio" bing          # Use Bing search
```

## 🔧 **Available Search Engines**
- **duckduckgo** (default) - Privacy-focused search
- **google** - Google search (may be rate-limited)
- **bing** - Microsoft Bing search

## 📊 **How It Works**
1. **Search**: Performs web search with your query
2. **Filter**: Only retrieves HTML content (skips PDFs, images, videos)
3. **Extract**: Uses intelligent content extraction focusing on main content
4. **Process**: Cleans and truncates content to configurable word limit (default: 500 words)
5. **Integrate**: Automatically adds search results to conversation context

## ⚙️ **Configuration**
Configure web search in `ocat.yaml`:
```yaml
web_search:
  enabled: true                    # Enable/disable web search
  default_engine: "duckduckgo"     # Default search engine
  content_threshold: 500           # Max words per page
  max_results: 3                   # Max search results to process
  timeout: 10                      # Request timeout in seconds
```

## 💡 **Examples**
```bash
# Research and ask questions
/web "what is quantum computing"
# AI will search and then respond with information from web results

# Get latest news
/web "technology news 2025" 
# AI will provide summary based on current web results

# Technical help
/web "python best practices 2025"
# AI will incorporate latest web information into advice
```

## 🚀 **Tips**
- Web search results are automatically integrated - just ask your follow-up questions
- Results are processed and summarized by the AI
- Content is filtered and cleaned for better readability
- Use specific queries for better results
- The AI will tell you if no relevant content was found
""",
            aliases=["search", "web", "internet"],
        )
        self.register_section("websearch", web_search)

    def _generate_overview(self) -> str:
        """Generate the main help overview."""
        return self.get_section("overview").content


# Global help registry instance
_help_registry = HelpRegistry()


def get_help_registry() -> HelpRegistry:
    """Get the global help registry instance."""
    return _help_registry


def get_help_content(section: Optional[str] = None) -> str:
    """
    Get help content for a specific section or overview.

    Parameters
    ----------
    section : Optional[str]
        Help section to retrieve, or None for overview

    Returns
    -------
    str
        Formatted help content
    """
    registry = get_help_registry()

    if section is None:
        return registry.get_overview()

    help_section = registry.get_section(section)
    if help_section is None:
        available_sections = ", ".join(registry.list_sections())
        return f"""# ❌ **Help Section Not Found**

The section **`{section}`** was not found.

## 📚 **Available Sections:**
{available_sections}

Use `/help` for the main overview or `/help <section>` for specific topics.

**Example**: `/help productivity` or `/help commands`
"""

    return help_section.content


def add_help_section(
    key: str, title: str, content: str, aliases: List[str] = None
) -> None:
    """
    Add a new help section to the registry.

    This function allows developers to easily add new help sections.

    Parameters
    ----------
    key : str
        Primary key for the section
    title : str
        Section title
    content : str
        Markdown-formatted help content
    aliases : List[str], optional
        Alternative keys for the section
    """
    registry = get_help_registry()
    section = HelpSection(title=title, content=content, aliases=aliases or [])
    registry.register_section(key, section)
