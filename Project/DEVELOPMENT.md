# Development Process

This project uses a structured development request management system optimized for LLM-assisted development.

## 🚀 Quick Start

```bash
# Create a bug report
./.dev/devreq create bug

# Create a feature request  
./.dev/devreq create feature

# List current requests
./.dev/devreq list

# Get help
./.dev/devreq help
```

## 📋 For LLMs and AI Assistants

### 🚨 CRITICAL: Immediate Bug Reporting

**If you encounter ANY unrelated bug, failing test, or issue while working:**

```bash
# Immediately create a bug report
./.dev/devreq create bug
# Fill out template, mark priority, then continue with original task
```

**Do NOT attempt to fix unrelated issues - just document them!**

### When asked to work on bugs or features:

1. **Check for existing requests**: `./.dev/devreq list backlog`
2. **Read request details**: `./.dev/devreq show <ID>`
3. **Implement the fix/feature** following the specifications
4. **Update with commit**: `./.dev/devreq update <ID>` (after committing)
5. **Mark complete**: `./.dev/devreq complete <ID>`

## 📖 Full Documentation

See [.dev/README.md](./.dev/README.md) for complete process documentation.

## 🔧 Process Commands

All development requests are managed through the `./.dev/devreq` command:
- `create [bug|feature]` - Create new request
- `list [backlog|completed]` - List requests  
- `show <ID>` - Show request details
- `update <ID> [commit]` - Update with git commit
- `complete <ID>` - Mark as completed

## 📁 Request Storage

- **Active requests**: `.dev/backlog/`
- **Completed requests**: `.dev/completed/`
- **Templates**: `.dev/templates/`

Request IDs follow the format: `BUG-YYYYMMDD-NN` or `FEAT-YYYYMMDD-NN`
