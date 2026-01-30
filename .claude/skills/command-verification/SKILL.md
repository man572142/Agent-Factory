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
    Trigger command-verification skill
         ↓
    Immediately spawn command-verifier subagent
         ↓
    Subagent handles everything:
      ├── Run verify_command.py (as subagent, no verification needed)
      ├── Check registry and parse commands
      ├── Display info to user
      └── Get approvals if needed
         ↓
    Return execution decision to main agent
```

## How to Use This Skill

When you need to execute a Bash command, invoke this skill with the command line as an argument.

The skill will immediately spawn the command-verifier subagent to handle all verification.

### Step 1: Spawn Command Verifier Subagent

Use the Task tool with subagent_type="command-verifier" and provide:
- The command line to be executed
- The registry path: .claude/skills/command-verification/assets/command_registry.json

**Example:**

```json
{
  "description": "Verify command before execution",
  "subagent_type": "command-verifier",
  "prompt": "Verify this command before execution:\n\nCommand: winget install --id Microsoft.Powershell --source winget\n\nRegistry Path: .claude/skills/command-verification/assets/command_registry.json"
}
```

### Step 2: Handle Subagent Response

Based on the subagent's response:

- **ALLOW**: Proceed with command execution
- **DENY**: Do not execute; inform user
- **PARTIAL**: Execute only approved commands

## Subagent Configuration

The `command-verifier` subagent is defined at `.claude/agents/command-verifier.md` with:
- **Tools**: Read, Write, Bash (restricted)
- **Model**: haiku (fast responses for interactive verification)

**Security Model**:
- **Main agent**: Cannot run ANY Bash during verification (breaks circular dependency)
- **Subagent Bash access**: RESTRICTED to only running Python scripts in `.claude/skills/command-verification/scripts/`
- **Never executes**: The subagent never executes the command being verified, only analyzes it
- This creates a secure, one-way verification flow: main agent → subagent → verification scripts → decision

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

When a command is not in the registry, the subagent automatically:
1. Generates command information based on analysis
2. Presents it to the user for approval
3. If approved, updates the registry directly using Read/Write tools (no Bash needed)

The subagent handles all registry updates internally - no manual intervention required.

## Example Interactions

### Example 1: Command Requires Permission

**Command:** `rm -rf temp/`

**Action:** Spawn `command-verifier` subagent to verify and get user permission.

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

### Example 2: Unknown Command

**Command:** `mycustomtool --process data.csv`

**Action:** Spawn `command-verifier` subagent to verify, generate info and add to registry.

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
2. **Always delegate to subagent** - The subagent handles all verification logic
3. **Subagent for interaction** - Use `command-verifier` subagent for all command verification
4. **Registry persistence** - New commands are saved so they don't need re-verification
5. **Compound commands** - Each command in `&&`, `||`, `;`, `|` chains is verified independently
6. **No circular dependency** - Main agent never runs Bash for verification; subagent is a trusted execution environment
