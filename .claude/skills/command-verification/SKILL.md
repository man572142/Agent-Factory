---
name: command-verification
description: |
  Automatic command verification hook that ensures safe bash/shell command execution.
  Displays educational information about each command including descriptions, risk levels,
  and reasons before execution. Unknown commands are blocked until added to the registry.

hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python3 .claude/skills/command-verification/scripts/hook_verify.py"
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
   - **Unknown**: Blocks until added to registry

## Adding Unknown Commands

When an unknown command is blocked, you have two options:

### Option 1: Use the add_command.py script directly
```bash
python .claude/skills/command-verification/scripts/add_command.py \
  "command_name" \
  "Description of what it does" \
  "AlwaysAllow|AlwaysAsk" \
  "low|medium|high|critical" \
  "Reason for the risk level"
```

### Option 2: Use the command-verifier subagent for interactive addition
Spawn the subagent with:
```json
{
  "subagent_type": "command-verifier",
  "prompt": "Add this command to the registry: <command_name>"
}
```

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
- The subagent is only needed when you want to interactively add new commands to the registry
