---
name: command-verification
description: |
  MANDATORY skill for executing bash/shell commands. Before ANY command execution,
  this skill verifies commands, displays risk information, and obtains user approval.
  Use this skill EVERY TIME the agent wants to run a bash command. It splits command
  lines, looks up command info from registry, shows risk levels (color-coded), and
  determines if auto-execution is allowed or user permission is needed.
---

# Command Verification Skill

## Overview

This skill ensures safe command execution by verifying all bash/shell commands before they run. It provides transparency about what each command does, its risk level, and whether user permission is required.

**CRITICAL: This skill MUST be used before executing ANY bash or shell command.**

## Workflow

```
Main Agent wants to execute command
         ↓
    Trigger this skill
         ↓
    Run verify_command.py to check registry
         ↓
    If can_auto_execute=true → Execute immediately
         ↓
    Otherwise, delegate to command-verifier subagent
         ↓
    Subagent checks each command:
      ├── Known + AlwaysAllow → Show info, mark for auto-execute
      ├── Known + AlwaysAsk  → Show info, request permission
      └── Unknown → Generate info, ask to add to registry
         ↓
    Return execution decision to main agent
```

## How to Use This Skill

### Step 1: Verify Commands Against Registry

When you need to execute a command, run the verification script:

```bash
python .claude/skills/command-verification/scripts/verify_command.py --json "your command here"
```

The output includes:
- `all_known`: Whether all commands are in the registry
- `can_auto_execute`: Whether execution can proceed without asking
- `highest_risk`: The highest risk level among all commands
- `commands`: Detailed info for each command
- `unknown_commands`: Commands not in the registry
- `needs_permission`: Commands requiring user approval

### Step 2: Check if Auto-Execute is Allowed

If `can_auto_execute` is `true`, all commands are known and have `AlwaysAllow` permission. You can proceed directly to execution.

### Step 3: Delegate to command-verifier Subagent

If `can_auto_execute` is `false`, use the Task tool to spawn the `command-verifier` subagent:

```
Use the Task tool with subagent_type="command-verifier" and provide:
- The command line to be executed
- The JSON verification results
- The registry path: .claude/skills/command-verification/assets/command_registry.json
```

**Example Task invocation:**

```json
{
  "description": "Verify command before execution",
  "subagent_type": "command-verifier",
  "prompt": "Verify this command before execution:\n\nCommand Line: git push origin main\n\nVerification Results:\n{...json results...}\n\nRegistry Path: .claude/skills/command-verification/assets/command_registry.json"
}
```

The `command-verifier` subagent is defined in `.claude/agents/command-verifier.md` and will:
1. Display command information to the user
2. For unknown commands: Generate info and ask if it should be added to registry
3. For AlwaysAsk commands: Request explicit permission
4. Return whether execution can proceed

### Step 4: Handle Subagent Response

Based on the subagent's response:

- **ALLOW**: Proceed with command execution
- **DENY**: Do not execute; inform user
- **PARTIAL**: Execute only approved commands

## Subagent Configuration

The `command-verifier` subagent is defined at `.claude/agents/command-verifier.md` with:
- **Tools**: Read, Bash, Write (for reading registry and adding commands)
- **Model**: haiku (fast responses for interactive verification)

## Command Information Structure

Each command in the registry has:

```json
{
  "name": "command-name",
  "description": "What this command does",
  "permission": "AlwaysAllow | AlwaysAsk",
  "risk": {
    "level": "low | medium | high | critical",
    "color": "green | yellow | red",
    "reason": "Why this risk level"
  }
}
```

### Permission Types

| Permission | Behavior |
|------------|----------|
| `AlwaysAllow` | Can execute without asking user |
| `AlwaysAsk` | Must get user permission before executing |

### Risk Levels

| Level | Color | Description |
|-------|-------|-------------|
| `low` | 🟢 Green | Read-only, safe operations |
| `medium` | 🟡 Yellow | Modifies files, installs packages |
| `high` | 🔴 Red | Security implications, data deletion |
| `critical` | 🔴 Red | System-level access, root privileges |

## Adding New Commands

When a command is not in the registry, the subagent generates its information and asks the user to confirm. If approved, use:

```bash
python .claude/skills/command-verification/scripts/add_command.py --json '{
  "name": "command-name",
  "description": "What it does",
  "permission": "AlwaysAsk",
  "risk_level": "medium",
  "risk_reason": "Reason for risk level"
}'
```

## Example Interactions

### Example 1: All Commands Known and AlwaysAllow

**Command:** `ls -la && pwd`

**Verification result:** `can_auto_execute: true`

**Action:** Execute immediately without spawning subagent.

```
🟢 All commands verified (AlwaysAllow). Executing: ls -la && pwd
```

### Example 2: Command Requires Permission

**Command:** `rm -rf temp/`

**Verification result:** `can_auto_execute: false`, `needs_permission: ["rm"]`

**Action:** Spawn `command-verifier` subagent to get user permission.

```
════════════════════════════════════════════════════════
COMMAND VERIFICATION
════════════════════════════════════════════════════════

Command: rm -rf temp/

────────────────────────────────────────────────────────
Command: rm
────────────────────────────────────────────────────────
Full: rm -rf temp/
Description: Remove files or directories. Permanently deletes files.
Permission: AlwaysAsk
Risk: 🔴 HIGH - Permanently deletes files; cannot be undone easily

⚠️  This command requires your permission to execute.
Do you want to proceed? (yes/no)
```

### Example 3: Unknown Command

**Command:** `mycustomtool --process data.csv`

**Verification result:** `all_known: false`, `unknown_commands: ["mycustomtool"]`

**Action:** Spawn `command-verifier` subagent to generate info and add to registry.

```
════════════════════════════════════════════════════════
COMMAND VERIFICATION
════════════════════════════════════════════════════════

Command: mycustomtool --process data.csv

────────────────────────────────────────────────────────
Command: mycustomtool [UNKNOWN]
────────────────────────────────────────────────────────
Full: mycustomtool --process data.csv
Status: Not in registry

📝 Unknown command detected. Generated information:

- Name: mycustomtool
- Description: Custom data processing tool
- Suggested Permission: AlwaysAsk
- Risk Level: medium
- Risk Reason: Unknown command; executes external processing

Options:
1. Approve and add to registry
2. Add to registry, don't execute
3. Modify information
4. Reject
```

## Resources

### scripts/
- `parse_command.py` - Splits command lines into individual commands
- `verify_command.py` - Verifies commands against the registry
- `add_command.py` - Adds new commands to the registry

### assets/
- `command_registry.json` - Database of known commands with their info

### Subagent
- `.claude/agents/command-verifier.md` - Subagent for user interaction

## Integration Notes

1. **Always use this skill before bash execution** - No exceptions
2. **Fast path for safe commands** - If `can_auto_execute=true`, skip subagent
3. **Subagent for interaction** - Use `command-verifier` subagent for permission requests
4. **Registry persistence** - New commands are saved so they don't need re-verification
5. **Compound commands** - Each command in `&&`, `||`, `;`, `|` chains is verified independently
