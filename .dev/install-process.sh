#!/bin/bash

# install-process.sh - Install development request process in any repo
# Usage: curl -s https://raw.githubusercontent.com/user/repo/main/.dev/install-process.sh | bash

set -e

echo "🔧 Installing Development Request Management Process..."

# Create directory structure
mkdir -p .dev/{templates,backlog,completed,git-hooks}

# Download/copy templates
cat > .dev/templates/bug_request.md << 'EOF'
# Bug Report

**ID**: BUG-{{YYYYMMDD}}-{{NN}}
**Created**: {{DATE}}
**Status**: OPEN
**Priority**: HIGH|MEDIUM|LOW
**Assignee**: LLM|HUMAN

## Problem Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: 
- Language/Runtime: 
- Dependencies: 

## Error Output
```
[paste error logs/stack traces here]
```

## Files Likely Involved
- `path/to/file1.py`
- `path/to/file2.py`

## Additional Context
Any other relevant information

---
**Resolution Notes** (filled after completion):
- Fix commit: 
- Test commit: 
- Resolution summary: 
EOF

cat > .dev/templates/feature_request.md << 'EOF'
# Feature Request

**ID**: FEAT-{{YYYYMMDD}}-{{NN}}
**Created**: {{DATE}}
**Status**: OPEN
**Priority**: HIGH|MEDIUM|LOW
**Assignee**: LLM|HUMAN

## Feature Description
What feature should be added/modified

## Use Case
Why is this feature needed? What problem does it solve?

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3

## Implementation Notes
- Suggested approach or files to modify
- Any constraints or considerations

## Files Likely Involved
- `path/to/file1.py`
- `path/to/file2.py`

## Additional Context
Any mockups, examples, or related information

---
**Resolution Notes** (filled after completion):
- Implementation commit: 
- Test commit: 
- Documentation commit:
- Resolution summary: 
EOF

# Create main CLI tool
cat > .dev/devreq << 'EOF'
#!/bin/bash

# devreq - Development Request Management
# Minimal CLI for managing bug reports and feature requests

set -e

DEV_DIR=".dev"
TEMPLATES_DIR="$DEV_DIR/templates"
BACKLOG_DIR="$DEV_DIR/backlog"
COMPLETED_DIR="$DEV_DIR/completed"

# Ensure directories exist
mkdir -p "$BACKLOG_DIR" "$COMPLETED_DIR"

# Generate ID
generate_id() {
    local type=$1
    local date=$(date +%Y%m%d)
    local counter=1
    
    while [[ -f "$BACKLOG_DIR/${type}-${date}-$(printf '%02d' $counter).md" ]]; do
        ((counter++))
    done
    
    echo "${type}-${date}-$(printf '%02d' $counter)"
}

# Create new request
create_request() {
    local type=$1
    local template=""
    
    case $type in
        "bug")
            template="$TEMPLATES_DIR/bug_request.md"
            ;;
        "feature")
            template="$TEMPLATES_DIR/feature_request.md"
            ;;
        *)
            echo "Usage: devreq create [bug|feature]"
            exit 1
            ;;
    esac
    
    if [[ ! -f "$template" ]]; then
        echo "Template not found: $template"
        exit 1
    fi
    
    local id=$(generate_id $(echo $type | tr '[:lower:]' '[:upper:]'))
    local filename="$BACKLOG_DIR/${id}.md"
    local current_date=$(date +%Y-%m-%d)
    
    # Replace template variables
    sed -e "s/{{YYYYMMDD}}/$(date +%Y%m%d)/g" \
        -e "s/{{NN}}/$(echo $id | grep -o '[0-9]*$')/g" \
        -e "s/{{DATE}}/$current_date/g" \
        "$template" > "$filename"
    
    echo "Created: $filename"
    echo "ID: $id"
    
    # Open in editor if available
    if command -v nvim &> /dev/null; then
        nvim "$filename"
    elif [[ -n "$EDITOR" ]]; then
        $EDITOR "$filename"
    fi
}

# List requests
list_requests() {
    local status=${1:-"backlog"}
    local dir=""
    
    case $status in
        "backlog"|"open")
            dir="$BACKLOG_DIR"
            ;;
        "completed"|"done")
            dir="$COMPLETED_DIR"
            ;;
        *)
            echo "Usage: devreq list [backlog|completed]"
            exit 1
            ;;
    esac
    
    echo "=== $(echo $status | tr '[:lower:]' '[:upper:]') ==="
    
    if [[ ! -d "$dir" ]] || [[ -z "$(ls -A "$dir" 2>/dev/null)" ]]; then
        echo "No requests found"
        return
    fi
    
    for file in "$dir"/*.md; do
        if [[ -f "$file" ]]; then
            local id=$(basename "$file" .md)
            local priority=$(grep "Priority:" "$file" | cut -d' ' -f2- | tr -d '*')
            local desc=$(grep -A1 "Problem Description\|Feature Description" "$file" | tail -1)
            printf "%-20s %-8s %s\n" "$id" "$priority" "$desc"
        fi
    done
}

# Complete a request
complete_request() {
    local id=$1
    
    if [[ -z "$id" ]]; then
        echo "Usage: devreq complete <ID>"
        exit 1
    fi
    
    local backlog_file="$BACKLOG_DIR/${id}.md"
    local completed_file="$COMPLETED_DIR/${id}.md"
    
    if [[ ! -f "$backlog_file" ]]; then
        echo "Request not found: $id"
        exit 1
    fi
    
    # Update status to COMPLETED
    sed -i.bak 's/Status**: OPEN/Status**: COMPLETED/' "$backlog_file"
    
    # Move to completed
    mv "$backlog_file" "$completed_file"
    rm -f "$backlog_file.bak"
    
    echo "Completed: $id"
    echo "Moved to: $completed_file"
}

# Show request details
show_request() {
    local id=$1
    
    if [[ -z "$id" ]]; then
        echo "Usage: devreq show <ID>"
        exit 1
    fi
    
    local file=""
    if [[ -f "$BACKLOG_DIR/${id}.md" ]]; then
        file="$BACKLOG_DIR/${id}.md"
    elif [[ -f "$COMPLETED_DIR/${id}.md" ]]; then
        file="$COMPLETED_DIR/${id}.md"
    else
        echo "Request not found: $id"
        exit 1
    fi
    
    cat "$file"
}

# Update request with git commit info
update_request() {
    local id=$1
    local commit_hash=${2:-$(git rev-parse HEAD)}
    
    if [[ -z "$id" ]]; then
        echo "Usage: devreq update <ID> [commit-hash]"
        exit 1
    fi
    
    local file=""
    if [[ -f "$BACKLOG_DIR/${id}.md" ]]; then
        file="$BACKLOG_DIR/${id}.md"
    elif [[ -f "$COMPLETED_DIR/${id}.md" ]]; then
        file="$COMPLETED_DIR/${id}.md"
    else
        echo "Request not found: $id"
        exit 1
    fi
    
    # Add commit info to resolution notes
    if grep -q "Fix commit: $" "$file"; then
        sed -i.bak "s/Fix commit: $/Fix commit: $commit_hash/" "$file"
    elif grep -q "Implementation commit: $" "$file"; then
        sed -i.bak "s/Implementation commit: $/Implementation commit: $commit_hash/" "$file"
    fi
    
    rm -f "$file.bak"
    echo "Updated $id with commit $commit_hash"
}

# Main command dispatcher
case ${1:-help} in
    "create")
        create_request $2
        ;;
    "list")
        list_requests $2
        ;;
    "show")
        show_request $2
        ;;
    "complete")
        complete_request $2
        ;;
    "update")
        update_request $2 $3
        ;;
    "help"|*)
        echo "🔧 devreq - Development Request Management"
        echo ""
        echo "📋 USAGE:"
        echo "  devreq create [bug|feature]     - Create a new request"
        echo "  devreq list [backlog|completed] - List requests"
        echo "  devreq show <ID>                - Show request details"
        echo "  devreq complete <ID>            - Mark request as completed"
        echo "  devreq update <ID> [commit]     - Update with git commit"
        echo ""
        echo "💡 EXAMPLES:"
        echo "  devreq create bug               # Create new bug report"
        echo "  devreq list backlog             # See open requests"
        echo "  devreq show BUG-20241230-01     # View request details"
        echo "  devreq update BUG-20241230-01   # Add commit info"
        echo "  devreq complete BUG-20241230-01 # Mark as done"
        echo ""
        echo "🚨 IMMEDIATE BUG REPORTING:"
        echo "  - Create bug report for ANY unrelated issue: devreq create bug"
        echo "  - Do NOT fix unrelated issues - just document them!"
        echo ""
        echo "📖 DOCUMENTATION:"
        echo "  - Full process: .dev/README.md"
        echo "  - LLM instructions: .dev/LLM-INSTRUCTIONS.md"
        echo "  - Project development: DEVELOPMENT.md"
        echo ""
        echo "📁 REQUEST STORAGE:"
        echo "  - Active: .dev/backlog/"
        echo "  - Completed: .dev/completed/"
        echo "  - Templates: .dev/templates/"
        ;;
esac
EOF

chmod +x .dev/devreq

echo "✅ Development Request Management Process installed!"
echo ""
echo "📋 Quick start:"
echo "  ./.dev/devreq help"
echo "  ./.dev/devreq create bug"
echo "  ./.dev/devreq list backlog"
echo ""
echo "📖 Consider adding to your project:"
echo "  - DEVELOPMENT.md file with process overview"
echo "  - Link from main README.md"
echo "  - Add .dev/ to .gitignore if you want to exclude backlog"
