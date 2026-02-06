# Agent-Factory

A development workspace for building Claude Code extensions — hooks, agents, and skills that enhance the CLI experience. The primary project is a **command verification system** that intercepts Bash commands, educates users about risk levels, and manages approval workflows.

## Command Verification System

The command verification system is a [Claude Code hook](https://docs.anthropic.com/en/docs/claude-code) that runs before every Bash command execution. It provides:

- **Command registry** — a database of known commands with descriptions, risk levels, and permission policies
- **Automatic verification** — each command is checked against the registry before execution
- **Risk-based decisions** — commands are auto-allowed, require approval, or blocked based on their registry entry
- **Unknown command handling** — a dedicated subagent researches unfamiliar commands and presents analysis to the user

### How It Works

```
Bash command invoked
  → PreToolUse hook triggers hook_verify.py
    → Command parsed and checked against registry
      → Known + AlwaysAllow  → auto-executes
      → Known + AlwaysAsk   → prompts user
      → Unknown             → spawns command-verifier subagent
                               → researches command, shows risk analysis
                               → asks user to approve & add to registry
```

### Project Structure

```
.claude/
  settings.json                      # Hook configuration
  agents/
    command-verifier.md              # Subagent for unknown command analysis
  hooks/
    command-verification/
      hook_verify.py                 # PreToolUse hook entry point
      verify_command.py              # Verification logic
      parse_command.py               # Shell command line parser
      add_command.py                 # Registry management CLI
      command_registry.json          # Command database
```

### Registry

Commands are stored in `command_registry.json` with:

| Field | Values | Description |
|-------|--------|-------------|
| `permission` | `AlwaysAllow`, `AlwaysAsk` | Whether to auto-execute or prompt |
| `risk.level` | `low`, `medium`, `high`, `critical` | Risk classification |
| `risk.reason` | free text | Explanation of the risk assessment |

### Adding Commands

Commands can be added via the subagent workflow (automatic when an unknown command is encountered) or manually:

```bash
python .claude/hooks/command-verification/add_command.py "name" "description" "AlwaysAllow|AlwaysAsk" "low|medium|high|critical" "risk reason"
```

## Skill Creator

This repository also includes the [Anthropic skill-creator](https://github.com/anthropics/skills) for building reusable Claude Code skills. See `.claude/skills/skill-creator/SKILL.md` for documentation.

## License

The skill-creator is licensed under the Apache License 2.0. See `.claude/skills/skill-creator/LICENSE.txt` for details.
