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
    Load command registry
         ↓
    Parse command line into individual commands
         ↓
    Delegate to verification subagent
         ↓
    Subagent checks each command:
      ├── Known + AlwaysAllow → Show info, mark for auto-execute
      ├── Known + AlwaysAsk  → Show info, request permission
      └── Unknown → Generate info, ask to add to registry
         ↓
    Return execution decision to main agent
```

## How to Use This Skill

### Step 1: Parse the Command Line

When you need to execute a command, first parse it using the command parser:

```bash
python skills/public/command-verification/scripts/parse_command.py --json "your command here"
```

This splits compound commands (using `&&`, `||`, `;`, `|`) into individual commands.

### Step 2: Verify Commands Against Registry

Run the verification script to check all commands:

```bash
python skills/public/command-verification/scripts/verify_command.py --json "your command here"
```

The output includes:
- `all_known`: Whether all commands are in the registry
- `can_auto_execute`: Whether execution can proceed without asking
- `highest_risk`: The highest risk level among all commands
- `commands`: Detailed info for each command
- `unknown_commands`: Commands not in the registry
- `needs_permission`: Commands requiring user approval

### Step 3: Delegate to Verification Subagent

Spawn a `command-verifier` subagent with the verification results and command line. The subagent will:

1. Display command information to the user
2. For unknown commands: Generate info and ask if it should be added
3. For AlwaysAsk commands: Request explicit permission
4. Return whether execution can proceed

**Subagent Prompt Template:**

```
You are the Command Verification Subagent. Your task is to verify the following
command before execution and interact with the user as needed.

Command Line: {command_line}

Verification Results:
{json_verification_results}

Command Registry Path: skills/public/command-verification/assets/command_registry.json

Instructions:
1. Display each command's information to the user with risk indicators
2. For UNKNOWN commands: Generate appropriate command info and ask user to confirm adding to registry
3. For AlwaysAsk commands: Ask for explicit permission to execute
4. For AlwaysAllow commands: Just display info (no permission needed)
5. Return final decision: ALLOW, DENY, or PARTIAL (some commands approved)

Use colored risk indicators:
- 🟢 LOW (green): Safe operations
- 🟡 MEDIUM (yellow): Moderate risk
- 🔴 HIGH/CRITICAL (red): Significant risk
```

### Step 4: Handle Subagent Response

Based on the subagent's response:

- **ALLOW**: Proceed with command execution
- **DENY**: Do not execute; inform user
- **PARTIAL**: Execute only approved commands

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

When a command is not in the registry, generate its information:

```bash
python skills/public/command-verification/scripts/add_command.py \
  "command-name" \
  "Description of what it does" \
  "AlwaysAllow|AlwaysAsk" \
  "low|medium|high|critical" \
  "Reason for this risk level"
```

Or use JSON format:

```bash
python skills/public/command-verification/scripts/add_command.py --json '{
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

**Output:**
```
Command Verification Report
==================================================
Command: ls -la && pwd

🟢 [ALLOW] All commands can be executed automatically

Highest Risk Level: LOW

Commands:
--------------------------------------------------
  ls
    Full: ls -la
    Description: List directory contents
    Permission: AlwaysAllow
    Risk: 🟢 LOW - Read-only operation

  pwd
    Full: pwd
    Description: Print working directory
    Permission: AlwaysAllow
    Risk: 🟢 LOW - Read-only operation

→ Proceeding with execution...
```

### Example 2: Command Requires Permission

**Command:** `rm -rf temp/`

**Output:**
```
Command Verification Report
==================================================
Command: rm -rf temp/

🟡 [ASK] User permission required

Highest Risk Level: HIGH

Commands:
--------------------------------------------------
  rm
    Full: rm -rf temp/
    Description: Remove files or directories. Permanently deletes files.
    Permission: AlwaysAsk
    Risk: 🔴 HIGH - Permanently deletes files; cannot be undone easily

⚠️  This command requires your permission to execute.
    Do you want to proceed? (yes/no)
```

### Example 3: Unknown Command

**Command:** `mycustomtool --process data.csv`

**Output:**
```
Command Verification Report
==================================================
Command: mycustomtool --process data.csv

🟡 [UNKNOWN] Command not in registry

Commands:
--------------------------------------------------
  mycustomtool [UNKNOWN]
    Full: mycustomtool --process data.csv
    Status: Not in registry

📝 I need to add this command to the registry.
   Please confirm the following information:

   Name: mycustomtool
   Description: [Generated description based on context]
   Permission: AlwaysAsk (recommended for unknown commands)
   Risk Level: medium
   Risk Reason: Unknown command; requires verification

   Does this look correct? Should I add it to the registry? (yes/no/modify)
```

## Resources

### scripts/
- `parse_command.py` - Splits command lines into individual commands
- `verify_command.py` - Verifies commands against the registry
- `add_command.py` - Adds new commands to the registry

### assets/
- `command_registry.json` - Database of known commands with their info

## Integration Notes

1. **Always use this skill before bash execution** - No exceptions
2. **Subagent delegation** - Use a subagent for user interaction to keep main agent context clean
3. **Registry updates** - Persist new commands so they don't need re-verification
4. **Compound commands** - Always parse first; each command is verified independently
5. **Piped commands** - Each command in a pipe is treated as a separate command
