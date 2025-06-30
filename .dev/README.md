# Development Request Management

A minimal process for managing bug fixes and feature requests optimized for LLM development.

## Quick Start

```bash
# Create a new bug report
./.dev/devreq create bug

# Create a feature request  
./.dev/devreq create feature

# List open requests
./.dev/devreq list backlog

# Show request details
./.dev/devreq show BUG-20241230-01

# Update with git commit after fix
./.dev/devreq update BUG-20241230-01

# Mark as completed
./.dev/devreq complete BUG-20241230-01
```

## Process Flow

### 1. Creating Requests
- Use templates to ensure consistency
- Auto-generates unique IDs (BUG-YYYYMMDD-NN, FEAT-YYYYMMDD-NN)
- Opens in neovim/editor for immediate editing
- Stores in `.dev/backlog/`

### 2. Working on Requests
- LLMs can read request files for context
- All necessary information is in the markdown file
- Files likely to need changes are specified

### 3. Completing Requests
- Update with git commit hash
- Mark as completed (moves to `.dev/completed/`)
- Resolution notes track what was done

## Directory Structure
```
.dev/
├── devreq              # Main CLI tool
├── templates/          # Request templates
│   ├── bug_request.md
│   └── feature_request.md
├── backlog/           # Open requests
│   ├── BUG-20241230-01.md
│   └── FEAT-20241230-02.md
└── completed/         # Completed requests
    └── BUG-20241229-01.md
```

## LLM Instructions

### 🚨 IMMEDIATE BUG REPORTING PROTOCOL

**CRITICAL**: When you encounter any bug, failing test, or issue that is NOT related to your current task:

1. **Immediately create a bug report**:
   ```bash
   ./.dev/devreq create bug
   ```

2. **Document the issue completely**:
   - Problem description
   - Error messages/stack traces
   - Steps to reproduce
   - Files involved
   - Set appropriate priority (HIGH for functionality issues)

3. **DO NOT attempt to fix unrelated issues** - continue with your original task

4. **Examples requiring immediate bug reports**:
   - Tests failing unrelated to current work
   - Runtime errors in existing code
   - Configuration problems
   - Missing dependencies
   - Performance issues
   - Documentation errors

### When working on a request:

1. **Read the request**: `.dev/devreq show <ID>`
2. **Implement the fix/feature**
3. **Update with commit**: `.dev/devreq update <ID>`
4. **Mark complete**: `.dev/devreq complete <ID>`

## Git Integration

The process integrates with git through:
- Commit hashes are automatically captured
- Requests track resolution commits
- Status tied to git workflow

## Portability

To use in other repos:
1. Copy `.dev/` directory
2. Run `chmod +x .dev/devreq` 
3. Add to PATH or use relative path

## Aliases (Optional)

Add to shell profile for convenience:
```bash
alias dreq='./.dev/devreq'
alias dlist='./.dev/devreq list'
alias dbug='./.dev/devreq create bug'
alias dfeat='./.dev/devreq create feature'
```
