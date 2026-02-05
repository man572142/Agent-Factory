#!/usr/bin/env python3
"""
Hook-based Command Verifier - PreToolUse hook for Bash command verification.

This script runs as a Claude Code PreToolUse hook to verify bash commands
before execution. It provides:
- Command verification against the registry
- Educational information about each command
- Risk level indicators and explanations
- Blocking of unknown or high-risk commands pending approval

Hook I/O:
- Input: JSON from stdin with tool_input.command
- Output (stderr): Explanatory information for the user
- Output (stdout): JSON decision using hookSpecificOutput format for PreToolUse

Usage (as a hook, not meant to be run directly):
    echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python hook_verify.py
"""

import sys
import os
import json
from typing import Dict, Any, List

# Add the scripts directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from parse_command import parse_command_line

# Risk indicators with explanations
RISK_INDICATORS = {
    "low": ("🟢", "Safe operation"),
    "medium": ("🟡", "Moderate risk"),
    "high": ("🔴", "High risk"),
    "critical": ("🔴", "Critical risk"),
}

REGISTRY_PATH = os.path.join(script_dir, "..", "assets", "command_registry.json")


def load_registry() -> Dict[str, Any]:
    """Load the command registry from JSON file."""
    try:
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"commands": {}}


def eprint(*args, **kwargs):
    """Print to stderr (shown to user as explanatory output)."""
    print(*args, file=sys.stderr, **kwargs)


def format_command_info(cmd_name: str, full_command: str, info: Dict[str, Any] | None) -> List[str]:
    """Format command information for display."""
    lines = []

    if info:
        risk = info.get("risk", {})
        risk_level = risk.get("level", "unknown")
        indicator, _ = RISK_INDICATORS.get(risk_level, ("⚪", "Unknown"))

        lines.append(f"  Command: {cmd_name}")
        lines.append(f"  Full:    {full_command}")
        lines.append(f"  Description: {info.get('description', 'No description')}")
        lines.append(f"  Risk: {indicator} {risk_level.upper()} - {risk.get('reason', 'No reason provided')}")
        lines.append(f"  Permission: {info.get('permission', 'Unknown')}")
    else:
        lines.append(f"  Command: {cmd_name}")
        lines.append(f"  Full:    {full_command}")
        lines.append(f"  Status:  ⚠️  UNKNOWN - Not in registry")

    return lines


def verify_and_explain(command_line: str) -> Dict[str, Any]:
    """
    Verify a command and output explanatory information.

    Returns the decision dictionary for the hook response.
    """
    registry = load_registry()
    commands_db = registry.get("commands", {})
    parsed = parse_command_line(command_line)

    # Track verification state
    unknown_commands = []
    needs_permission = []
    all_info = []
    highest_risk = "low"
    risk_priority = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    # Analyze each command
    for cmd in parsed["commands"]:
        cmd_name = cmd["command_name"]
        full_cmd = cmd["full_command"]
        info = commands_db.get(cmd_name)

        all_info.append({
            "name": cmd_name,
            "full": full_cmd,
            "info": info
        })

        if info is None:
            unknown_commands.append(cmd_name)
        else:
            if info.get("permission") == "AlwaysAsk":
                needs_permission.append(cmd_name)

            cmd_risk = info.get("risk", {}).get("level", "low")
            if risk_priority.get(cmd_risk, 0) > risk_priority.get(highest_risk, 0):
                highest_risk = cmd_risk

    # Output explanatory header
    eprint("")
    eprint("════════════════════════════════════════════════════════")
    eprint("COMMAND VERIFICATION")
    eprint("════════════════════════════════════════════════════════")
    eprint(f"Command: {command_line}")
    eprint(f"Analyzing {len(all_info)} command(s)...")
    eprint("")

    # Output each command's info
    for cmd_data in all_info:
        eprint("────────────────────────────────────────────────────────")
        for line in format_command_info(cmd_data["name"], cmd_data["full"], cmd_data["info"]):
            eprint(line)
        eprint("")

    # Handle unknown commands - ask and delegate to command-verifier subagent
    if unknown_commands:
        eprint("════════════════════════════════════════════════════════")
        eprint("⚠️  UNKNOWN COMMANDS DETECTED")
        eprint("════════════════════════════════════════════════════════")
        eprint("")
        eprint("The following commands are not in the registry:")
        for cmd in unknown_commands:
            eprint(f"  • {cmd}")
        eprint("")
        eprint("Spawning command-verifier subagent to review and handle...")
        eprint("")

        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Unknown command(s): {', '.join(unknown_commands)}. Spawn the command-verifier subagent with the original command '{command_line}' so it can research each unknown command, present the analysis to the user, and ask whether to add it to the registry and whether to allow or deny execution."
            }
        }

    # Handle AlwaysAsk commands - block for user confirmation
    if needs_permission:
        indicator, _ = RISK_INDICATORS.get(highest_risk, ("⚪", "Unknown"))
        eprint("════════════════════════════════════════════════════════")
        eprint(f"{indicator} PERMISSION REQUIRED")
        eprint("════════════════════════════════════════════════════════")
        eprint("")
        eprint("The following commands require explicit approval:")
        for cmd in needs_permission:
            cmd_info = commands_db.get(cmd, {})
            risk = cmd_info.get("risk", {})
            eprint(f"  • {cmd}: {cmd_info.get('description', 'No description')}")
            eprint(f"    Risk: {risk.get('level', 'unknown').upper()} - {risk.get('reason', 'N/A')}")
        eprint("")

        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"Permission required for: {', '.join(needs_permission)}"
            }
        }

    # All commands are known and AlwaysAllow
    indicator, _ = RISK_INDICATORS.get(highest_risk, ("🟢", "Safe"))
    eprint("════════════════════════════════════════════════════════")
    eprint(f"{indicator} APPROVED - Auto-executing (AlwaysAllow)")
    eprint("════════════════════════════════════════════════════════")
    eprint("")

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "All commands verified and approved for execution"
        }
    }


def main():
    """Main entry point for hook execution."""
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)

        # Extract the command from tool_input
        tool_input = input_data.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            # No command to verify
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": "No command to verify"
                }
            }
        else:
            result = verify_and_explain(command)

        # Output JSON decision to stdout
        print(json.dumps(result))

    except json.JSONDecodeError as e:
        eprint(f"Error: Invalid JSON input - {e}")
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Hook error: Invalid JSON input - {e}"
            }
        }))
        sys.exit(1)
    except Exception as e:
        eprint(f"Error: {e}")
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Hook error: {e}"
            }
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
