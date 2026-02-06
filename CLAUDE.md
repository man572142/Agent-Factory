# CLAUDE.md

## Project Overview

Agent-Factory is a development workspace for building Claude Code extensions — primarily **hooks** and **agents** that enhance the Claude Code CLI experience. The current focus is the **command verification system**, a PreToolUse hook that intercepts Bash commands, verifies them against a registry, and educates users about command risk levels before execution.

## Repository Structure

```
.claude/
  settings.json              # Hook configuration (PreToolUse → hook_verify.py)
  agents/
    command-verifier.md      # Subagent spawned for unknown commands
  hooks/
    command-verification/
      hook_verify.py         # Main hook entry point (reads stdin JSON, writes stdout JSON)
      verify_command.py      # Standalone verification logic
      parse_command.py       # Shell command parser (splits &&, ||, ;, |)
      add_command.py         # CLI tool to add commands to registry
      command_registry.json  # Known commands with risk levels and permissions
  skills/
    skill-creator/           # Anthropic's skill-creator guidance system
```

## Command Verification System

### How It Works

1. **Hook trigger**: `.claude/settings.json` registers a PreToolUse hook on all `Bash` tool calls
2. **Verification**: `hook_verify.py` parses the command line, checks each command against `command_registry.json`
3. **Decision**:
   - **Known + AlwaysAllow** → auto-executes
   - **Known + AlwaysAsk** → prompts user for approval
   - **Unknown** → denies and instructs the main agent to spawn the `command-verifier` subagent
4. **Subagent flow**: The command-verifier agent researches the unknown command, presents risk analysis, and asks the user whether to add it to the registry

### Registry Format

Commands in `command_registry.json` have:
- `description`: What the command does
- `permission`: `AlwaysAllow` or `AlwaysAsk`
- `risk.level`: `low`, `medium`, `high`, or `critical`
- `risk.reason`: Explanation of the risk assessment

### Key Scripts

- `hook_verify.py` — Do not run directly; it reads Claude Code hook JSON from stdin
- `add_command.py <name> <description> <permission> <risk_level> <risk_reason>` — Add a command to the registry
- `parse_command.py` — Importable module for splitting shell command lines
- `verify_command.py` — Importable verification logic (also has a standalone CLI mode)

## Development Guidelines

- **Python 3** is used for all hook scripts — no external dependencies required
- Hook output format: JSON with `hookSpecificOutput.permissionDecision` (`allow`, `deny`, `ask`) on **stdout**; human-readable info on **stderr**
- The command-verifier subagent must **never** execute the commands it analyzes — it only runs `add_command.py`
- When modifying hook scripts, test with: `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | python .claude/hooks/command-verification/hook_verify.py`
- The skill-creator under `.claude/skills/` is a bundled tool from Anthropic for creating new skills — see `skill-creator/SKILL.md` for its documentation
