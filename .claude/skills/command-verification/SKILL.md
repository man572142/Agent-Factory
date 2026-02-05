---
name: command-verification
description: |
  Automatic command verification hook that ensures safe bash/shell command execution.
  Displays educational information about each command including descriptions, risk levels,
  and reasons before execution. Unknown commands trigger the command-verifier subagent
  to research, present analysis, and ask the user whether to add and/or allow.

---

# Command Verification Skill

This skill automatically verifies all bash/shell commands before execution using a PreToolUse hook.

## Features

- **Automatic Verification**: Every Bash command is verified before execution - no manual invocation needed
- **Educational Output**: Each command displays its description, risk level, and risk reason so you can learn what commands do
- **Risk Indicators**:
  - 🟢 **LOW**: Safe operations (read-only, display)
  - 🟡 **MEDIUM**: Moderate risk (file changes, installs)
  - 🔴 **HIGH**: Dangerous (deletions, security changes)
  - 🔴 **CRITICAL**: Maximum risk (sudo, system access)
- **Permission Levels**:
  - **AlwaysAllow**: Executes automatically after displaying info
  - **AlwaysAsk**: Blocks and requires your approval

## How It Works

1. When Claude attempts to run a Bash command, the hook intercepts it
2. The command is parsed and each sub-command (separated by `&&`, `||`, `;`, `|`) is verified
3. Educational information is displayed about each command
4. Based on registry status:
   - **Known + AlwaysAllow**: Executes automatically
   - **Known + AlwaysAsk**: Blocks for your approval
   - **Unknown**: The command-verifier subagent is spawned automatically. It researches the command, presents an analysis (description, risk level, suggested permission), and asks you whether to add it to the registry and whether to allow or deny execution.

## Registry Location

Commands are stored in: `.claude/skills/command-verification/assets/command_registry.json`

## Example Output

When you run a command like `npm install`:

```
════════════════════════════════════════════════════════
COMMAND VERIFICATION
════════════════════════════════════════════════════════
Command: npm install
Analyzing 1 command(s)...

────────────────────────────────────────────────────────
  Command: npm
  Full:    npm install
  Description: Node.js package manager for installing dependencies
  Risk: 🟡 MEDIUM - Modifies node_modules and may run install scripts
  Permission: AlwaysAllow

════════════════════════════════════════════════════════
🟡 APPROVED - Auto-executing (AlwaysAllow)
════════════════════════════════════════════════════════
```

## Notes

- The hook runs automatically for ALL Bash commands - you don't need to invoke anything manually
- Commands are verified even in compound statements (e.g., `mkdir foo && cd foo`)
- The command-verifier subagent is spawned automatically whenever an unknown command is encountered
