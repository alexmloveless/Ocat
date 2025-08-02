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

**Ocat** is an intelligent chat assistant with powerful productivity features and file management capabilities.

## 🎯 **Quick Start**
- **Chat naturally** with AI models (OpenAI, Anthropic, Google)
- **Use slash commands** like `/help`, `/clear`, `/exit` for quick actions
- **Manage productivity** with tasks, events, reminders, and memories
- **Work with files** using built-in file operations and location aliases
- **AI has direct tool access** - ask it to read files, manage tasks, and more!

## 📚 **Help Sections**
Use `/help <section>` to get detailed information:

- **`/help commands`** - All available slash commands
- **`/help productivity`** - Task, event, reminder & memory management
- **`/help files`** - File operations and location aliases  
- **`/help chat`** - Chat features and conversation management
- **`/help config`** - Configuration and setup options
- **`/help tips`** - Usage tips and best practices

## 🚀 **Examples**
```
# Slash commands
/help productivity     # Learn about task management
/file read myfile.txt  # Direct file operations

# Natural AI requests (AI has tool access!)
"read myfile.txt and summarize the key points"
"create a task to review quarterly report due Friday"
"show me what's in the docs directory"
"remember client prefers morning meetings"
```

*Type `/help <section>` for detailed documentation on any area.*
""",
            aliases=["overview", "main"]
        )
        self.register_section("overview", overview)
        
        # Commands section
        commands = HelpSection(
            title="Slash Commands Reference",
            content="""# 🔧 **Slash Commands**

## 📋 **Core Commands**
- **`/help [section]`** - Show help (try `/help productivity`)
- **`/clear`** - Clear screen and show welcome message  
- **`/exit`, `/quit`, `/q`** - Exit the application
- **`/history [limit]`** - Show conversation history
- **`/context`** - Display current conversation context

## 📁 **File Operations**
- **`/file read <path>`** - Read and display file contents
- **`/file write <path> <content>`** - Write content to file
- **`/file append <path> <content>`** - Append content to file
- **`/file list [path]`** - List directory contents
- **`/file search <pattern> [path]`** - Search for files/content
- **`/file tree [path] [depth]`** - Show directory tree structure

## 📍 **Location Aliases**
- **`/locations`** - List all configured location aliases
- **`/location add <alias> <path>`** - Add new location alias
- **`/location remove <alias>`** - Remove location alias
- Use **`alias:filename`** syntax in file commands

## 📋 **Clipboard Operations**
- **`/copy`** - Copy last assistant response to clipboard
- **`/paste`** - Paste clipboard content into chat
- **`/clip <text>`** - Copy specific text to clipboard

## 🗃️ **Vector Store Management**
- **`/vector stats`** - Show vector store statistics  
- **`/vector clear [collection]`** - Clear vector store data
- **`/vector search <query>`** - Search vector store content

## 💭 **Memory & Context**
- **`/remember <information>`** - Store information for later recall
- **`/forget <query>`** - Remove stored information
- **`/recall [query]`** - Search stored memories

## ✅ **Productivity**
- **`/st [category]`** - Show all open tasks, optionally filter by category
- **`/st priority:<priority>`** - Show tasks by priority (urgent/high/medium/low)
- **`/list`** - Show all lists with item counts
- **`/list <listname>`** - Show items in specific list

## ⌨️ **Keyboard Shortcuts**
- **`Ctrl+C`** - Interrupt current operation
- **`Ctrl+D`** - Exit application
- **`↑/↓ arrows`** - Navigate command history
- **`Tab`** - Command auto-completion (where available)
""",
            aliases=["cmd", "command", "slash"]
        )
        self.register_section("commands", commands)
        
        # Productivity section
        productivity = HelpSection(
            title="Productivity System Guide",
            content="""# 📊 **Productivity System**

Manage your tasks, events, reminders, and memories using **natural language**.

## 🎯 **Features**
- **Natural language interface** - Just describe what you want
- **Flexible date parsing** - "next Tuesday", "in 2 weeks", "tomorrow at 3pm"
- **Pseudo IDs** - Easy references like `task001`, `event001`
- **Vector storage** - Integrated with chat history for smart search

## ✅ **Tasks**
Manage your to-do items with priorities, categories, and due dates.

### Examples:
```
create a task to review the quarterly report
add task: finish presentation slides due next Friday  
make a high priority task to call client by tomorrow
update task001 status to completed
list all tasks due this week
delete task003
```

### Features:
- **Due dates** with flexible parsing
- **Priority levels**: low, medium, high, urgent
- **Categories** for organization  
- **Status tracking**: active, in_progress, completed
- **Tags** for additional classification

## 📅 **Events**
Schedule meetings, appointments, and time-based activities.

### Examples:
```
add meeting with team on Friday at 2pm
schedule doctor appointment next Tuesday at 10:30am
create event: project deadline on December 15th
update event002 location to conference room A
list events for next week
```

### Features:
- **Start/end times** with flexible scheduling
- **All-day events** supported
- **Participants** and **location** tracking
- **Multi-day events** for longer activities

## ⏰ **Reminders**
Set up notifications and memory aids.

### Examples:
```
create reminder for next Tuesday to call Sam
remind me to water plants every Monday
set reminder: submit expense report by month end
mark reminder001 as completed
list active reminders
```

### Features:
- **Trigger dates/times** with natural language
- **Categories** for organization
- **Status tracking** and completion
- **Recurring reminders** (planned feature)

## 🧠 **Memories**
Store important information and reference material.

### Examples:
```
remember that Sarah prefers tea over coffee
save memory: the wifi password is "SecureNet123"
add to memory: client prefers morning meetings
search memories for "password"
forget memory001
```

### Features:
- **Free-form text** storage
- **Searchable content** across all memories
- **Categorization** and **tagging**
- **Timestamped entries** for tracking

## 📝 **Lists**
Organize collections of items in categorized lists.

### Examples:
```
add "groceries: milk, bread, eggs" to shopping list
create list item "read 1984" in books list
add item "visit Paris" to travel bucket list
archive list001
show all lists
show items in shopping list
```

### Features:
- **Named lists** - group related items together
- **Categories** for organization within lists
- **Archive items** instead of deleting
- **Date tracking** - see when items were added

## 🔍 **Management Commands**
```
# List entities
list tasks, list events, list reminders, list memories, list items

# Search and filter  
show completed tasks
find events next week
search reminders for "call"

# Update and modify
update task001 priority to high
change event002 time to 3pm
mark reminder001 completed

# Delete
delete task003, remove event001, forget memory002
```

## 📋 **Status Management**
- **Tasks**: active → in_progress → completed → deleted
- **Events**: scheduled → completed → cancelled  
- **Reminders**: active → completed → deleted
- **Memories**: active → deleted

## 💡 **Tips**
- Use **natural language** - the system understands context
- **Pseudo IDs** make referencing easy (task001, event002)
- **Search** works across all productivity content
- **Integration** with chat means your AI assistant knows your schedule
""",
            aliases=["tasks", "events", "reminders", "memories", "productivity", "prod"]
        )
        self.register_section("productivity", productivity)
        
        # Files section
        files = HelpSection(
            title="File Operations Guide", 
            content="""# 📁 **File Operations**

Powerful file management capabilities with location aliases for easy access.

## 📖 **File Commands**

### **Reading Files**
```
/file read myfile.txt
/file read docs:readme.md    # Using location alias
/file read /absolute/path/to/file.txt
```

### **Writing Files**
```
/file write newfile.txt "Hello, World!"
/file write config:settings.json "{'debug': true}"
```

### **Appending to Files**
```
/file append logs:app.log "New log entry"
/file append notes.txt "Additional notes"
```

### **Directory Operations**
```
/file list                  # List current directory
/file list src/             # List specific directory  
/file list docs:            # List using location alias
/file tree                  # Show directory tree
/file tree src/ 2           # Tree with max depth 2
```

### **Search Operations**
```
/file search "function"     # Search for text in files
/file search "class" src/   # Search in specific directory
/file search "*.py"         # Search for file patterns
```

## 📍 **Location Aliases**

Simplify file paths with custom aliases.

### **Managing Aliases**
```
/locations                          # List all aliases
/location add docs ~/Documents      # Add alias
/location add config ~/.config/app  # Add alias  
/location remove old_alias          # Remove alias
```

### **Using Aliases**
```
# Instead of: /file read ~/Documents/readme.md
/file read docs:readme.md

# Instead of: /file list ~/.config/app/
/file list config:

# Works with all file commands
/file write logs:debug.log "Debug info"
/file search "error" logs:
```

## 🔗 **Filesystem Aliases**

Convenient shortcuts for common filesystem commands:

```
/ls [path]              # → /file list [path]
/pwd                    # Show current working directory  
/cd <path>              # Change working directory
/cat <path>             # → /file read <path>
/mkdir <path>           # Create directory
```

## 💡 **Tips**
- **Tab completion** available for file paths (where supported)
- **Relative paths** work from current directory
- **Absolute paths** start with `/` (Unix) or `C:` (Windows)
- **Aliases** make frequent paths much easier to use
- **Wildcards** supported in search patterns
- **Working directory** persists during your session
""",
            aliases=["file", "files", "location", "locations", "paths"]
        )
        self.register_section("files", files)
        
        # Chat section
        chat = HelpSection(
            title="Chat Features Guide",
            content="""# 💬 **Chat Features**

Advanced conversation management and AI interaction capabilities.

## 🤖 **AI Models**
Ocat supports multiple AI providers:

- **OpenAI**: GPT-4, GPT-3.5-turbo models
- **Anthropic**: Claude-3 (Opus, Sonnet, Haiku)  
- **Google**: Gemini Pro models

Configure in `ocat.yaml` or use environment variables.

## 🔧 **AI Tool Access**
The AI has direct access to powerful tools and can:

### **File Operations**
Ask the AI to work with files naturally:
```
"read myfile.md and summarize the key points"
"show me what's in the config directory"  
"search for Python files containing 'error'"
"create a new file called notes.txt with today's agenda"
```

### **Productivity Management**
Manage tasks, events, and reminders through conversation:
```
"create a task to review the quarterly report due Friday"
"schedule a meeting with the team next Tuesday at 2pm"
"remind me to call the client tomorrow"
"show me my tasks for this week"
```

The AI understands context and can chain operations together naturally.

## 🗣️ **Conversation Management**

### **History**
```
/history           # Show recent conversation
/history 20        # Show last 20 messages
/context           # Display current context
```

### **Screen Control**
```
/clear             # Clear screen, show welcome
/exit, /quit, /q   # Exit application
```

## 📋 **Clipboard Integration**
```
/copy              # Copy last AI response
/paste             # Paste clipboard content
/clip "text"       # Copy specific text
```

## 🧠 **Memory Integration**
The chat system integrates with your productivity data:

- **Context awareness** of your tasks and events
- **Smart suggestions** based on your stored memories
- **Seamless productivity** commands within conversation

## ⌨️ **Input Methods**

### **Text Input**
- Type naturally and press Enter
- Multi-line input supported
- Rich text formatting in responses

### **Command History**
- **↑/↓ arrows** to navigate previous commands
- **History persists** across sessions
- **Smart filtering** of commands vs chat

### **Interruption**
- **Ctrl+C** to stop current AI response
- **Ctrl+D** to exit application gracefully

## 🎨 **Response Formatting**
- **Markdown rendering** for rich content
- **Syntax highlighting** for code blocks
- **Tables and lists** properly formatted
- **Color coding** for different content types

## 💡 **Tips**
- **Mix natural chat** with slash commands seamlessly
- **Ask about your productivity** data in conversation
- **Use context** - the AI remembers your preferences
- **Interrupt long responses** with Ctrl+C when needed
""",
            aliases=["conversation", "ai", "models", "chat"]
        )
        self.register_section("chat", chat)
        
        # Config section
        config = HelpSection(
            title="Configuration Guide",
            content="""# ⚙️ **Configuration**

Customize Ocat's behavior through configuration files and environment variables.

## 📄 **Configuration File**
Main config: **`ocat.yaml`**

### **Basic Structure**
```yaml
# LLM Configuration
llm:
  provider: "openai"        # openai, anthropic, google
  model: "gpt-4"           # Model name
  api_key: "${OCAT_API_KEY}" # Environment variable

# Chat Settings  
chat:
  max_history: 100         # Conversation history limit
  auto_save: true          # Auto-save conversations
  
# Vector Store Settings
vector_store:
  collection_name: "ocat_main"
  persist_directory: "./vector_stores"
  
# Location Aliases
locations:
  docs: "~/Documents"
  config: "~/.config/ocat"
  logs: "/var/log/ocat"
```

## 🔑 **Environment Variables**

### **API Keys**
```bash
export OCAT_API_KEY="your-api-key"          # Primary API key
export OPENAI_API_KEY="your-openai-key"     # OpenAI specific
export ANTHROPIC_API_KEY="your-claude-key"  # Anthropic specific  
export GOOGLE_API_KEY="your-google-key"     # Google specific
```

### **Configuration Override**
```bash
export OCAT_CONFIG_PATH="/custom/path/ocat.yaml"
export OCAT_LOG_LEVEL="DEBUG"               # Logging level
export OCAT_VECTOR_PATH="/custom/vectors"   # Vector storage path
```

## 📂 **File Locations**

### **Default Paths**
```
Config:        ~/.config/ocat/ocat.yaml
Logs:          ~/.local/share/ocat/logs/
Vector Store:  ~/.local/share/ocat/vectors/
Cache:         ~/.cache/ocat/
```

### **Custom Locations**
Override with environment variables or config file settings.

## 🔧 **Advanced Settings**

### **LLM Provider Configuration**
```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.7        # Response creativity (0-1)
  max_tokens: 2048        # Response length limit
  timeout: 30             # Request timeout seconds
```

### **Vector Store Tuning**
```yaml
vector_store:
  chunk_size: 1000        # Document chunk size
  chunk_overlap: 200      # Overlap between chunks  
  embedding_model: "text-embedding-ada-002"
```

## 🚀 **Quick Setup**

### **1. Install Dependencies**
```bash
poetry install  # If using Poetry
pip install -r requirements.txt  # Alternative
```

### **2. Set API Key**
```bash
export OCAT_API_KEY="your-key-here"
```

### **3. Run Ocat**
```bash
poetry run ocat  # With Poetry
ocat            # If installed globally
```

## 🛠️ **Troubleshooting**

### **Common Issues**
- **API key errors**: Check environment variables
- **Config not found**: Verify file path and permissions
- **Vector store issues**: Check disk space and permissions
- **Model errors**: Verify model name and provider settings

### **Debug Mode**
```bash
export OCAT_LOG_LEVEL="DEBUG"
ocat  # Run with verbose logging
```

## 💡 **Tips**
- **Start with defaults** and customize gradually
- **Use environment variables** for sensitive data
- **Version control** your config (without secrets)
- **Test configuration** with `/vector stats` command
""",
            aliases=["configuration", "setup", "config", "settings"]
        )
        self.register_section("config", config)
        
        # Tips section
        tips = HelpSection(
            title="Usage Tips & Best Practices",
            content="""# 💡 **Tips & Best Practices**

## 🚀 **Getting Started**

### **First Steps**
1. **Set up API key**: `export OCAT_API_KEY="your-key"`
2. **Start chatting**: Ask questions naturally
3. **Try productivity**: `create a task to learn Ocat`
4. **Explore commands**: `/help commands`

### **Essential Commands**
```
/help productivity    # Learn task management
/locations           # Set up file shortcuts  
/history            # Review conversation
/copy               # Copy AI responses
```

## 📊 **Productivity Workflow**

### **Daily Planning**
```
# Morning routine
list tasks due today
add event: standup meeting at 9am
create reminder to review weekly goals

# End of day
mark task001 completed
list tasks for tomorrow
save memory: great progress on project X
```

### **Project Management**
```
# Project setup
create task: define project requirements
add event: project kickoff next Monday 2pm
remember: project deadline is December 15th

# Progress tracking  
update task001 status to in_progress
create task: review milestone deliverables
list all tasks in category "project-alpha"
```

## 📁 **File Management**

### **Efficient File Access**
```bash
# Set up aliases first
/location add proj ~/work/current-project
/location add docs ~/Documents
/location add config ~/.config

# Then use shortcuts
/file read proj:readme.md
/file list docs:
/file search "TODO" proj:
```

### **Documentation Workflow**
```
# Reading and note-taking
/file read docs:meeting-notes.md
remember: key decision was to use microservices
create task: update architecture documentation

# Writing and organization
/file write docs:summary.md "Project Summary..."
/file append proj:changelog.md "v1.2 - Added new features"
```

## 💬 **Chat Optimization**

### **Effective Communication**
- **Be specific**: "Help me debug the auth error in login.py"
- **Provide context**: Share relevant file contents
- **Ask follow-ups**: Build on previous responses
- **Use productivity data**: "Based on my tasks, what should I prioritize?"

### **Managing Long Conversations**
```
/clear               # Start fresh when context gets heavy
/history 10          # Review recent discussion
/context             # Check current conversation scope
```

## 🔄 **Integration Patterns**

### **Cross-Feature Usage**
```
# Chat + Productivity
"Based on my tasks, what should I work on next?"
"Add the suggestions from this conversation to my tasks"

# Files + Memory  
/file read config.yaml
remember: the database URL is set in config.yaml line 15

# Productivity + Files
create task: update documentation in docs:api.md
/file read proj:todo.txt  # Import existing todos
```

## ⚡ **Efficiency Tips**

### **Keyboard Shortcuts**
- **↑/↓**: Command history navigation
- **Ctrl+C**: Interrupt long responses
- **Ctrl+D**: Quick exit
- **Tab**: Auto-completion (where available)

### **Command Optimization**
```
# Use aliases for common commands
/h instead of /help
/q instead of /quit  
/c instead of /clear

# Batch operations
list all tasks; list events this week; show reminders
```

### **Productivity Shortcuts**
```
# Quick task creation
todo: finish the report by Friday

# Rapid event scheduling  
meeting with client tomorrow 2pm

# Fast memory storage
remember: Sarah's extension is 2745
```

## 🛠️ **Troubleshooting**

### **Common Issues**
- **Slow responses**: Check internet connection and API limits
- **Missing data**: Use `/vector stats` to check storage
- **Command errors**: Verify syntax with `/help commands`
- **File access**: Check paths and permissions

### **Performance Tips**
- **Clear vector store** periodically with `/vector clear`
- **Limit history** in config for faster loading
- **Use specific queries** rather than broad searches
- **Restart session** if memory usage grows large

## 🎯 **Advanced Usage**

### **Power User Workflows**
```
# Daily dashboard
list tasks due today; list events today; show active reminders

# Weekly review
search tasks completed last week
list events next week  
show memories from category "project-notes"

# Project context switching
forget old_project memories
/vector clear old_project_collection
create task: set up new project environment
```

### **Automation Ideas**
- **Morning routine**: Standard set of list commands
- **Project templates**: Reusable task and event patterns  
- **Review cycles**: Regular memory and task cleanup
- **Documentation sync**: File operations + memory storage

## 🌟 **Pro Tips**
- **Combine natural language** with slash commands seamlessly
- **Use the AI assistant** to help interpret your productivity data
- **Leverage vector search** across all your data (chat + productivity)
- **Build habits** around consistent productivity workflows
- **Experiment** with different organization patterns to find what works
""",
            aliases=["tip", "tips", "best", "practices", "workflow"]
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


def add_help_section(key: str, title: str, content: str, aliases: List[str] = None) -> None:
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
