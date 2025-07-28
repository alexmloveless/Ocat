# DEVELOPMENT.md - LLM Quick Start Guide

🚨 **CRITICAL**: Read this entire document before starting any development work.
🚨 **CRITICAL**: Read the documents in Projects  before starting any development work 

## 🎯 IMMEDIATE ACTION REQUIRED

### 1. MANDATORY Bug Reporting Protocol
**IF YOU ENCOUNTER ANY BUG, FAILING TEST, OR ISSUE UNRELATED TO YOUR CURRENT TASK:**

```bash
# IMMEDIATELY create a bug report - DO NOT attempt to fix it
./.dev/devreq create bug
```

Fill out the template completely and continue with your original task. This ensures all issues are tracked systematically.

### 2. Development Request Process 
**ALWAYS work through the request system:**

```bash
# Check existing work
./.dev/devreq list backlog

# Read specific request
./.dev/devreq show <REQUEST-ID>

# After completing work
./.dev/devreq update <REQUEST-ID>
./.dev/devreq complete <REQUEST-ID>
```

## 🛠️ Core Development Process

### Development Workflow (ALWAYS follow this order)
```bash
# 1. MANDATORY: Create a new branch before making changes
git checkout -b feat/your-feature-name

# 2. ALWAYS use dev.sh for complete cycle
./dev.sh "feat: your commit message"

# This runs: black → mypy → pytest → git add → git commit
# Following conventional commits: feat/fix/docs/test/refactor

# 3. After testing, merge to main
git checkout main
git merge feat/your-feature-name
git push origin main
```

### Testing & Quality (Run before every commit)
```bash
# These are automatically run by dev.sh
poetry run black src tests    # Code formatting
poetry run mypy src          # Type checking  
poetry run pytest           # Test suite
```

### Project Setup
```bash
# Environment setup
poetry install

# Run application
poetry run ocat
```

## 📁 Key Project Structure
```
ocat/
├── src/ocat/           # Main application code
│   ├── cli.py         # CLI interface
│   ├── config.py      # Configuration management
│   ├── chat.py        # Chat functionality
│   ├── commands/      # Built-in chat commands
│   ├── backends/      # LLM provider integrations
│   ├── productivity/  # Task, event, reminder, memory management
│   └── vector_store.py # ChromaDB integration
├── tests/             # Test suite
├── .dev/              # Development process management
└── dev.sh             # MAIN DEVELOPMENT SCRIPT
```

## 🔧 Essential Commands

### Development Request Management
```bash
./.dev/devreq create bug      # Create bug report
./.dev/devreq create feature  # Create feature request
./.dev/devreq list backlog    # List open work
./.dev/devreq show BUG-YYYYMMDD-NN  # Read request details
./.dev/devreq help           # Full command reference
```

### Git Process
```bash
# MANDATORY: Always create branch first
git checkout -b feat/feature-name

# ALWAYS use conventional commits
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug issue"
git commit -m "docs: update documentation"
git commit -m "test: add missing tests"
git commit -m "refactor: improve code structure"

# Merge to main after testing
git checkout main
git merge feat/feature-name
```

## 🐛 Bug Discovery Protocol

When you find ANY unrelated issue:

1. **Immediately create bug report**: `./.dev/devreq create bug`
2. **Document completely**: Error messages, reproduction steps, files involved
3. **Set priority**: HIGH for functionality issues, MEDIUM/LOW for others
4. **DO NOT FIX**: Continue with original task
5. **Examples requiring immediate reports**:
   - Tests failing unrelated to current work
   - Runtime errors in existing functionality  
   - Configuration issues
   - Missing dependencies
   - Performance problems

## 🚀 Release Process

### Quick Release
```bash
./release.sh  # If available
```

### Manual Release Steps
```bash
poetry run pytest           # Test
poetry run black src tests  # Format
poetry run mypy src         # Type check
# Edit pyproject.toml version
poetry build               # Build package
git tag v{version} && git push --tags
```

## 📖 Core Development Rules

### Code Quality Requirements
- **Always create docstrings** for Python functions (numpy format)
- **Always use type hints** for functions and classes
- **Use in-line comments** for complex/implicit code sections
- **Keep code simple, clear and explicit**
- **Follow all Python best practices**

### Working Process
1. **Read request specifications completely**
2. **Focus on "Files Likely Involved" section**
3. **Meet all "Acceptance Criteria" for features**
4. **Address "Expected Behavior" for bugs**
5. **Use ./dev.sh for all commits**
6. **Update requests with commit hashes**

### Environment Notes
- Python at: `/Users/alex/opt/miniconda3/bin/python3`
- Use `ocat` conda env when working on this project
- Testing: pytest
- Formatting: black  
- Type checking: mypy

## 🎯 Development Priorities

1. **Minimum viable product approach** while achieving all objectives
2. **Input/output token minimization**
3. **Short, concise updates and summaries**
4. **Focus on core functionality in tests**
5. **Expose configurable parameters to user API**

## ⚠️ Critical Notes

- **NEVER bypass the ./dev.sh script** - it ensures complete quality checks
- **ALWAYS document unrelated bugs immediately** - don't attempt fixes
- **Read request files completely** before starting work
- **Follow conventional commit format strictly**
- **Update and complete requests after finishing work**

## 📋 Quick Reference Commands

```bash
# Start development work
./.dev/devreq list backlog              # See what needs doing
./.dev/devreq show <REQUEST-ID>         # Read specific request

# During development  
./dev.sh "feat: implement feature X"    # Complete dev cycle

# After completion
./.dev/devreq update <REQUEST-ID>       # Record commit
./.dev/devreq complete <REQUEST-ID>     # Mark as done

# Emergency bug reporting
./.dev/devreq create bug               # For ANY unrelated issue
```

## 📞 Need Help?
- Process documentation: `.dev/README.md`
- LLM instructions: `.dev/LLM-INSTRUCTIONS.md`  
- Request templates: `.dev/templates/`
- Command help: `./.dev/devreq help`

---

**Remember: Follow this process at all times. It ensures quality code, proper tracking, and systematic development.**
