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
- `/help productivity` - Tasks, lists, and memory management
- `/help files` - File operations and location aliases
- `/help chat` - Chat features and conversation management
- `/help config` - Configuration and setup
- `/help tips` - Usage tips and best practices

## 🚀 **Quick Examples**
```
/st                    # Show open tasks
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

## 💭 **Memory & Productivity**
- `/remember <type> <text>` - Store information
- `/st [category|priority:<level>]` - Show open tasks
- `/list [listname]` - Show lists/list items

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

Manage tasks, lists, and memories using natural language.

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
/writemd chat.md           # Export to Markdown
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
/writejson chat.json  # Export conversation
/writemd chat.md      # Export to Markdown
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
