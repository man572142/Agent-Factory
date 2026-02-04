---
name: command-verification
description: |
  MANDATORY skill for executing bash/shell commands. Before ANY command execution,
  spawn the command-verifier subagent to verify commands, display risk information,
  and obtain user approval. The subagent handles all verification logic internally.
---

# Command Verification Skill

This skill ensures safe command execution by spawning the `command-verifier` subagent to verify all bash/shell commands before they run.

**CRITICAL: This skill MUST be used before executing ANY bash or shell command.**

## How to Use

When you need to execute a Bash command, spawn the command-verifier subagent using the Task tool:

```json
{
  "description": "Verify command before execution",
  "subagent_type": "command-verifier",
  "prompt": "Verify this command before execution:\n\nCommand: <command_line>\n\nRegistry Path: .claude/skills/command-verification/assets/command_registry.json"
}
```

## Handling the Response

The subagent returns a JSON decision:

- **ALLOW**: Proceed with command execution
- **DENY**: Do not execute; inform user
- **PARTIAL**: Some commands denied - ask user if they want to split and execute approved commands individually, or cancel the entire command-line

## Notes

- The subagent handles all verification, user interaction, and registry updates
- Each command in compound statements (`&&`, `||`, `;`, `|`) is verified independently
- See `.claude/agents/command-verifier.md` for implementation details
