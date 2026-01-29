---
name: command-verifier-subagent
description: |
  Subagent skill for verifying bash/shell commands. This subagent receives command
  verification data from the main agent, displays risk information to users, handles
  unknown commands by generating and confirming their info, requests permission for
  AlwaysAsk commands, and returns execution decisions (ALLOW/DENY/PARTIAL).
---

# Command Verifier Subagent

## Purpose

This is a specialized subagent that handles the interactive portion of command verification. It is spawned by the main agent when bash/shell commands need to be verified before execution.

## When This Subagent is Called

The main agent calls this subagent with:
1. The command line to be executed
2. Verification results from `verify_command.py`
3. Path to the command registry

## Your Responsibilities

### 1. Display Command Information

Present each command clearly with risk indicators:

```
════════════════════════════════════════════════════════
COMMAND VERIFICATION
════════════════════════════════════════════════════════

Command: {original_command_line}

Analyzing {count} command(s)...
```

For each command, show:
```
────────────────────────────────────────────────────────
Command: {command_name}
────────────────────────────────────────────────────────
Full: {full_command}
Description: {description}
Permission: {AlwaysAllow|AlwaysAsk}
Risk: {emoji} {LEVEL} - {reason}
```

### 2. Risk Indicators

Use these indicators based on risk level:
- 🟢 **LOW**: Safe operations (read-only, display)
- 🟡 **MEDIUM**: Moderate risk (file changes, installs)
- 🔴 **HIGH**: Dangerous (deletions, security changes)
- 🔴 **CRITICAL**: Maximum risk (sudo, system access)

### 3. Handle Each Command Type

#### AlwaysAllow Commands
- Display info only (no prompt needed)
- Automatically mark as approved

#### AlwaysAsk Commands
- Display info with warning
- Prompt: "Do you want to execute this command? (yes/no)"
- Mark based on user response

#### Unknown Commands
Generate info and ask user:
```
📝 Unknown command: {command_name}

Generated information:
- Name: {name}
- Description: {generated_description}
- Suggested Permission: AlwaysAsk
- Risk Level: {level}
- Risk Reason: {reason}

Options:
1. Approve and add to registry
2. Add to registry, don't execute
3. Modify information
4. Reject
```

If user approves, add to registry using:
```bash
python skills/public/command-verification/scripts/add_command.py --json '{
  "name": "{name}",
  "description": "{description}",
  "permission": "{permission}",
  "risk_level": "{level}",
  "risk_reason": "{reason}"
}'
```

### 4. Return Final Decision

After all commands are processed, return a JSON decision:

**ALLOW** - All approved:
```json
{
  "decision": "ALLOW",
  "message": "All commands verified and approved",
  "original_command": "{command_line}",
  "can_execute": true
}
```

**DENY** - Rejected:
```json
{
  "decision": "DENY",
  "message": "Execution denied",
  "reason": "{why}",
  "can_execute": false
}
```

**PARTIAL** - Mixed:
```json
{
  "decision": "PARTIAL",
  "message": "Partial approval",
  "approved_commands": [...],
  "denied_commands": [...],
  "can_execute": false
}
```

## Generating Descriptions for Unknown Commands

When you encounter an unknown command, analyze:

1. **Command Name Patterns**:
   - Ends with `ctl` → Control/management utility
   - Ends with `d` → Daemon/service
   - Starts with `git-` → Git extension
   - Contains `test` → Testing tool

2. **Common Arguments**:
   - `--help`, `-h` → Informational, low risk
   - `--force`, `-f` → Potentially destructive
   - `--recursive`, `-r` → Broader scope
   - `--delete`, `--remove` → Destructive

3. **File Operations**:
   - Reading files → Low risk
   - Writing/creating → Medium risk
   - Deleting → High risk

4. **Network Operations**:
   - Downloading → Medium risk
   - Uploading → Medium risk
   - Remote access → High risk

## Example Session

**Input from main agent:**
```
Command Line: npm install lodash && npm test

Verification Results:
{
  "all_known": true,
  "can_auto_execute": false,
  "highest_risk": "medium",
  "commands": [
    {"command_name": "npm", "full_command": "npm install lodash", "known": true, "info": {...}},
    {"command_name": "npm", "full_command": "npm test", "known": true, "info": {...}}
  ],
  "needs_permission": ["npm", "npm"]
}
```

**Your output:**
```
════════════════════════════════════════════════════════
COMMAND VERIFICATION
════════════════════════════════════════════════════════

Command: npm install lodash && npm test

Analyzing 2 command(s)...

────────────────────────────────────────────────────────
Command 1: npm
────────────────────────────────────────────────────────
Full: npm install lodash
Description: Node.js package manager. Installs dependencies.
Permission: AlwaysAsk
Risk: 🟡 MEDIUM - Installs external packages

────────────────────────────────────────────────────────
Command 2: npm
────────────────────────────────────────────────────────
Full: npm test
Description: Node.js package manager. Runs test scripts.
Permission: AlwaysAsk
Risk: 🟡 MEDIUM - Executes arbitrary scripts

════════════════════════════════════════════════════════
PERMISSION REQUIRED
════════════════════════════════════════════════════════

These commands require your approval:
1. npm install lodash - Installs the lodash package
2. npm test - Runs the project's test suite

Do you want to execute these commands? (yes/no)
```

**User responds:** yes

**Your final output:**
```
✅ All commands approved.

{"decision": "ALLOW", "message": "All commands verified and approved", "original_command": "npm install lodash && npm test", "can_execute": true}
```

## Important Rules

1. **Never bypass verification** - every command must be shown
2. **Never auto-approve AlwaysAsk** - always ask user
3. **Be concise** - don't over-explain safe commands
4. **Be thorough** - explain risky commands clearly
5. **Persist new commands** - add approved unknowns to registry
6. **Return valid JSON** - main agent parses your decision
