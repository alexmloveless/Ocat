# CLI Input Alternatives for Multiline + History

## Problem
Current `prompt_toolkit` setup cannot simultaneously support:
- Multiline mode with Shift+Enter for newline
- Enter for submit
- Up arrow for history navigation

In multiline mode, prompt_toolkit uses up/down arrows for cursor movement within the text, not history navigation.

## Alternative Solutions

### 1. Custom prompt_toolkit Implementation
**Approach**: Implement custom key binding logic that detects cursor position
- When cursor is at first line + beginning: up arrow = history
- When cursor is at last line + end: down arrow = history  
- Otherwise: up/down = cursor movement
- Use Shift+Enter for newline, Enter for submit

**Pros**: Stays within prompt_toolkit ecosystem
**Cons**: Complex edge case handling, may feel inconsistent

### 2. Rich + keyboard library
**Libraries**: `rich` for display, `keyboard` for input handling
**Approach**: Build custom input handler that:
- Captures raw keyboard input
- Handles multiline buffer manually
- Implements history navigation with custom keys (Ctrl+P/N or Alt+Up/Down)
- Uses rich for syntax highlighting and display

**Pros**: Full control over behavior
**Cons**: More complex, platform-specific keyboard handling

### 3. Textual Framework
**Library**: `textual` (Rich's TUI framework)
**Approach**: Use Textual's input widgets with custom key bindings
- TextArea widget for multiline input
- Custom key bindings for Enter/Shift+Enter
- History implemented as custom behavior

**Pros**: Modern, well-designed TUI framework
**Cons**: Bigger dependency, different paradigm (widget-based)

### 4. cmd2 Framework
**Library**: `cmd2` (enhanced cmd module)
**Approach**: Use cmd2's multiline input with custom history
- Built-in multiline support with continuation prompts
- Extensive history management
- Custom key bindings possible

**Pros**: Designed for interactive CLI apps, robust history
**Cons**: More opinionated framework, may need architectural changes

### 5. GNU Readline Python bindings
**Library**: `gnureadline` or built-in `readline`
**Approach**: Use lower-level readline interface
- Custom key bindings for Shift+Enter vs Enter
- Native history support
- Manual multiline buffer management

**Pros**: Native terminal behavior, robust history
**Cons**: Platform-specific, more low-level coding required

### 6. Terminal.py + custom input handler
**Library**: `blessed` or `rich` for terminal control
**Approach**: Build from scratch:
- Raw terminal input handling
- Custom multiline buffer
- History stored in list/file
- Manual cursor and display management

**Pros**: Complete control, exactly what you want
**Cons**: Most complex, need to handle all edge cases

### 7. Hybrid approach with prompt_toolkit
**Approach**: Use single-line mode with visual multiline simulation
- Single-line prompt_toolkit (gets history navigation)
- Display multiline content above the input line
- Enter = submit, Shift+Enter = add to visual buffer + new prompt
- Custom display logic to show "accumulated" multiline content

**Pros**: Leverages prompt_toolkit's strengths
**Cons**: More complex display logic, not true multiline editing

### 8. Web-based terminal (Browser TUI)
**Libraries**: `flask` + `socket.io` + web terminal emulator
**Approach**: Run web interface instead of terminal
- Full control over key bindings in browser
- Rich editing capabilities
- History navigation works as expected

**Pros**: Full control, modern UX
**Cons**: Requires browser, more complex architecture

## Recommendation Priority

1. **Textual Framework** - Most promising for modern TUI apps
2. **cmd2** - If you want CLI-focused framework with good history
3. **Custom prompt_toolkit** - If you want to stick with current approach
4. **Rich + keyboard** - If you want more control but stay in terminal
5. **Hybrid prompt_toolkit** - Clever workaround using current library

## Implementation Effort

- **Low**: Custom prompt_toolkit, cmd2
- **Medium**: Textual, Rich + keyboard, Hybrid approach  
- **High**: GNU Readline, Terminal.py custom, Web-based

## Next Steps

1. Try Textual framework first - it's designed for exactly this kind of interactive app
2. If Textual doesn't work, try cmd2 for CLI-focused approach
3. Fall back to custom prompt_toolkit implementation with smart cursor detection
