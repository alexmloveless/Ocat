# Ocat Prompts Directory

This directory contains all system prompt markdown files used by Ocat.

## Prompt Files

- **`base_prompt.md`** - The main system prompt that provides context about Ocat's capabilities, available commands, and response guidelines. This is automatically loaded unless `override_base_prompt` is set to `true` in configuration.

- **`casual_mode_prompt.md`** - System prompt addendum for casual chat mode. This is loaded when the `/casual` command is used or when starting with the `--casual` flag.

## Usage

These prompts are automatically loaded by Ocat's configuration system and command handlers. The prompts use standard markdown formatting and can include:

- Headers for organization
- Lists for guidelines  
- Bold/italic text for emphasis
- Code blocks for examples

## Adding New Prompts

When adding new prompt files:

1. Place the `.md` file in this directory
2. Update the relevant command or configuration code to reference the new prompt
3. Use descriptive filenames that clearly indicate the prompt's purpose
4. Follow the existing formatting style for consistency

## Path References

Code references to these prompts use paths relative to the `ocat` package:
- `ocat/prompts/base_prompt.md`
- `ocat/prompts/casual_mode_prompt.md`