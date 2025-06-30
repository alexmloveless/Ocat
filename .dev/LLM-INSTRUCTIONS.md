# Instructions for LLMs and AI Assistants

This document provides specific guidance for LLMs working on this codebase.

## 🚨 Immediate Bug Reporting

**CRITICAL**: If you encounter ANY bug, failing test, or issue that is NOT related to your current development task, you MUST immediately:

1. **Create a bug report**:
   ```bash
   ./.dev/devreq create bug
   ```

2. **Fill out the template** with:
   - Clear problem description
   - Steps to reproduce (if applicable)
   - Error messages/stack traces
   - Files involved
   - Mark priority as HIGH if it affects functionality

3. **Do NOT attempt to fix it** - just document it and continue with your original task

4. **Examples of when to create immediate bug reports**:
   - Tests failing that are unrelated to your current work
   - Runtime errors in existing functionality
   - Configuration issues
   - Missing dependencies
   - Performance problems
   - Documentation errors

**This ensures all issues are tracked and can be addressed systematically.**

---

## 🎯 Development Request Process

### Before Starting Any Development Task

1. **Check for existing requests**:
   ```bash
   ./.dev/devreq list backlog
   ```

2. **If working on a specific request, read it first**:
   ```bash
   ./.dev/devreq show <REQUEST-ID>
   ```

3. **If no request exists for the task, create one**:
   ```bash
   # For bugs
   ./.dev/devreq create bug
   
   # For features  
   ./.dev/devreq create feature
   ```

### During Development

- Follow the specifications in the request file
- Focus on the "Files Likely Involved" section
- Meet all "Acceptance Criteria" for features
- Address the "Expected Behavior" for bugs

### After Completing Work

1. **Update the request with your commit**:
   ```bash
   ./.dev/devreq update <REQUEST-ID>
   ```

2. **Mark the request as completed**:
   ```bash
   ./.dev/devreq complete <REQUEST-ID>
   ```

## 🔍 Discovery Commands

When asked to work on something:

```bash
# See what's currently in the backlog
./.dev/devreq list backlog

# Check recently completed work
./.dev/devreq list completed

# Get help with the process
./.dev/devreq help
```

## 📝 Request Information

Each request contains:
- **Problem/Feature Description**: What needs to be done
- **Steps to Reproduce** (bugs): How to trigger the issue
- **Acceptance Criteria** (features): What success looks like
- **Files Likely Involved**: Where to start looking
- **Environment Info**: Context about the system
- **Priority Level**: HIGH/MEDIUM/LOW

## 🚨 Important Notes

- Always read the full request before starting
- Update requests with commit hashes when work is done
- Ask for clarification if request details are unclear
- Create new requests for work not covered by existing ones

## 📋 Common Workflows

### Bug Fix Workflow
```bash
./.dev/devreq show BUG-YYYYMMDD-NN
# Read the bug details, reproduce the issue
# Fix the code, test the fix
# Commit with: "fix: resolve BUG-YYYYMMDD-NN - brief description"
./.dev/devreq update BUG-YYYYMMDD-NN
./.dev/devreq complete BUG-YYYYMMDD-NN
```

### Feature Development Workflow
```bash
./.dev/devreq show FEAT-YYYYMMDD-NN
# Read feature requirements and acceptance criteria
# Implement the feature, write tests
# Commit with: "feat: implement FEAT-YYYYMMDD-NN - brief description"
./.dev/devreq update FEAT-YYYYMMDD-NN
./.dev/devreq complete FEAT-YYYYMMDD-NN
```

### Ad-hoc Development
```bash
# If asked to do something without an existing request
./.dev/devreq create [bug|feature]
# Fill out the template with the details
# Follow normal workflow from there
```

### Failing Test Workflow
```bash
# When you encounter failing tests unrelated to current work:
./.dev/devreq create bug
# Document:
# - Which tests are failing
# - Error messages from test output
# - When the failure likely started
# - Mark as HIGH priority if blocking development
# Then continue with original task
```

### Configuration/Environment Issue Workflow
```bash
# For missing dependencies, config errors, etc:
./.dev/devreq create bug
# Document:
# - What's missing or misconfigured
# - Error messages
# - Environment details
# - Impact on development
# Continue with original task (if possible)
```
